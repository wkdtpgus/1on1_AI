from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import logging

# 프로젝트 모듈 임포트
from src.models.audio_processing import AudioProcessor
from src.models.llm_analysis import GeminiMeetingAnalyzer, OpenAIMeetingAnalyzer
from src.config.config import LLM_PROVIDER

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수로 모델 인스턴스 관리
audio_processor = None
meeting_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    global audio_processor, meeting_analyzer
    
    # 시작시 초기화
    try:
        logger.info("🎵 오디오 프로세서 초기화 중...")
        audio_processor = AudioProcessor()
        
        logger.info(f"🤖 LLM 분석기 초기화 중... (Provider: {LLM_PROVIDER})")
        if LLM_PROVIDER.lower() == 'openai':
            meeting_analyzer = OpenAIMeetingAnalyzer()
        else:
            meeting_analyzer = GeminiMeetingAnalyzer()
            
        logger.info("✅ 모든 모듈 초기화 완료")
        
        yield  # 앱이 실행되는 동안
        
    except Exception as e:
        logger.error(f"❌ 초기화 오류: {str(e)}")
        raise e
    finally:
        logger.info("🔄 앱 종료 중...")

# FastAPI 앱 생성
app = FastAPI(
    title="1on1 Meeting AI Analysis API",
    description="AI 기반 1on1 미팅 분석 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드 연동을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 운영시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (프론트엔드)
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    # JavaScript 및 CSS 파일들도 직접 서빙
    from fastapi import Request
    


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "audio_processor": audio_processor is not None,
        "meeting_analyzer": meeting_analyzer is not None
    }

@app.post("/api/analyze")
async def analyze_meeting(
    audio_file: UploadFile = File(...),
    meeting_type: str = Form(default="1on1"),
    questions: Optional[str] = Form(default=None)
):
    """오디오 파일을 업로드하고 1on1 미팅 분석을 수행"""
    if not audio_processor or not meeting_analyzer:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")
    
    temp_audio_path = None
    try:
        # 파일 확장자 검증
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        file_ext = Path(audio_file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}"
            )
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_audio_path = temp_file.name
            content = await audio_file.read()
            temp_file.write(content)
        
        logger.info(f"📁 임시 파일 저장: {temp_audio_path} ({len(content)} bytes)")
        
        # 1. STT 처리
        logger.info("🎙️ STT 처리 시작...")
        transcript_result = audio_processor.transcribe_existing_file(temp_audio_path)
        
        if not transcript_result or 'transcript' not in transcript_result:
            raise HTTPException(status_code=500, detail="STT 처리에 실패했습니다")
        
        transcript = transcript_result['transcript']
        speaker_stats = transcript_result.get('speaker_stats', {})
        
        logger.info(f"✅ STT 완료 (길이: {len(transcript)}자)")
        
        # 2. 질문 처리
        questions_list = None
        if questions:
            try:
                questions_list = json.loads(questions)
            except json.JSONDecodeError:
                questions_list = [q.strip() for q in questions.split('\n') if q.strip()]
        
        # 3. LLM 분석 (미팅 타입별)
        if meeting_type == "1on1":
            logger.info("🤖 1on1 미팅 LLM 분석 시작...")
            analysis_result = meeting_analyzer.analyze_comprehensive(
                transcript=transcript,
                questions=questions_list,
                speaker_stats=speaker_stats
            )
            
            # JSON 파싱
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError as e:
                logger.error(f"❌ LLM 결과 JSON 파싱 오류: {e}")
                analysis_data = {"error": "분석 결과 파싱 실패", "raw_result": analysis_result}
            
            logger.info("✅ LLM 분석 완료")
            
            # 디버깅: LLM 분석 결과 로그
            logger.info(f"🔍 LLM 분석 결과 구조: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else type(analysis_data)}")
            
            # 프론트엔드 형식으로 변환
            formatted_result = format_1on1_analysis(analysis_data, transcript, speaker_stats)
            
            # 디버깅: 포맷된 결과 로그
            logger.info(f"🔍 포맷된 결과 구조: {list(formatted_result.keys()) if isinstance(formatted_result, dict) else type(formatted_result)}")
            
            final_response = {
                "status": "success",
                "meeting_type": meeting_type,
                "timestamp": datetime.now().isoformat(),
                **formatted_result,
                "file_info": {
                    "filename": audio_file.filename,
                    "size": len(content),
                    "format": file_ext
                }
            }
            
            # 디버깅: 최종 응답 구조 로그
            logger.info(f"🔍 최종 응답 구조: {list(final_response.keys())}")
            
            return JSONResponse(content=final_response)
        
        elif meeting_type == "planning":
            logger.info("🤖 기획회의 LLM 분석 시작...")
            analysis_result = meeting_analyzer.analyze_planning_meeting(
                transcript=transcript,
                questions=questions_list,
                speaker_stats=speaker_stats
            )
            
            # JSON 파싱
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError as e:
                logger.error(f"❌ 기획회의 LLM 결과 JSON 파싱 오류: {e}")
                analysis_data = {"error": "기획회의 분석 결과 파싱 실패", "raw_result": analysis_result}
            
            logger.info("✅ 기획회의 LLM 분석 완료")
            
            # 프론트엔드 형식으로 변환
            formatted_result = format_planning_analysis(analysis_data, transcript, speaker_stats)
            
            final_response = {
                "status": "success",
                "meeting_type": meeting_type,
                "timestamp": datetime.now().isoformat(),
                **formatted_result,
                "file_info": {
                    "filename": audio_file.filename,
                    "size": len(content),
                    "format": file_ext
                }
            }
            
            return JSONResponse(content=final_response)
        
        else:
            # 다른 미팅 타입은 기본 응답
            return JSONResponse(content={
                "status": "success",
                "meeting_type": meeting_type,
                "message": f"{meeting_type} 미팅 분석은 준비 중입니다",
                "transcript": transcript,
                "speaker_stats": speaker_stats
            })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 분석 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 처리 중 오류가 발생했습니다: {str(e)}")
    
    finally:
        # 임시 파일 정리
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
                logger.info(f"🗑️ 임시 파일 삭제: {temp_audio_path}")
            except Exception as e:
                logger.warning(f"⚠️ 임시 파일 삭제 실패: {e}")

def format_1on1_analysis(analysis_data, transcript, speaker_stats):
    """LLM 분석 결과를 프론트엔드 형식으로 변환"""
    try:
        # 에러가 있는 경우
        if "error" in analysis_data:
            return {
                "summary": "분석 중 오류가 발생했습니다.",
                "transcript": transcript
            }
        
        # 실제 분석 결과가 있는 경우 그대로 반환 (JSON 파일과 동일한 구조)
        if "quick_review" in analysis_data:
            # JSON 파일과 동일한 구조로 반환
            result = {
                "title": analysis_data.get("title", "1on1 미팅 분석 결과"),
                "quick_review": analysis_data.get("quick_review", {}),
                "detailed_discussion": analysis_data.get("detailed_discussion", ""),
                "feedback": analysis_data.get("feedback", []),
                "positive_aspects": analysis_data.get("positive_aspects", []),
                "qa_summary": analysis_data.get("qa_summary", []),
                "transcript": transcript
            }
            return result
        
        # 기존 구조의 분석 결과인 경우 변환
        return {
            "summary": analysis_data.get("summary", "요약 정보가 없습니다."),
            "decisions": analysis_data.get("key_decisions", []),
            "actionItems": analysis_data.get("action_items", []),
            "feedback": {
                "positive": analysis_data.get("leader_feedback", {}).get("positive_points", []),
                "improvement": analysis_data.get("leader_feedback", {}).get("improvement_points", [])
            },
            "qa": format_qa_results(analysis_data.get("qa_analysis", {})),
            "transcript": transcript
        }
    except Exception as e:
        logger.error(f"❌ 결과 포맷팅 오류: {e}")
        return {
            "summary": "결과 처리 중 오류가 발생했습니다.",
            "transcript": transcript
        }

def format_qa_results(qa_data):
    """Q&A 결과 포맷팅"""
    try:
        if not qa_data or not isinstance(qa_data, dict):
            return []
        
        questions = qa_data.get("questions", [])
        answers = qa_data.get("answers", [])
        
        if not questions or not answers:
            return []
        
        return [
            {"question": q, "answer": answers[i] if i < len(answers) else "답변이 없습니다."}
            for i, q in enumerate(questions)
        ]
    except Exception as e:
        logger.error(f"❌ Q&A 포맷팅 오류: {e}")
        return []

def format_planning_analysis(analysis_data, transcript, speaker_stats):
    """기획회의 분석 결과를 프론트엔드 형식으로 변환"""
    try:
        # 에러가 있는 경우
        if "error" in analysis_data:
            return {
                "summary": "기획회의 분석 중 오류가 발생했습니다.",
                "transcript": transcript
            }
        
        # 기획회의 분석 결과가 있는 경우 그대로 반환
        if "quick_review" in analysis_data:
            result = {
                "title": analysis_data.get("title", "기획회의 분석 결과"),
                "quick_review": analysis_data.get("quick_review", {}),
                "detailed_discussion": analysis_data.get("detailed_discussion", ""),
                "strategic_insights": analysis_data.get("strategic_insights", []),
                "innovation_ideas": analysis_data.get("innovation_ideas", []),
                "risks_challenges": analysis_data.get("risks_challenges", []),
                "next_steps": analysis_data.get("next_steps", []),
                "transcript": transcript
            }
            return result
        
        # 기본 구조 반환
        return {
            "summary": "기획회의 분석 결과를 처리할 수 없습니다.",
            "transcript": transcript
        }
    except Exception as e:
        logger.error(f"❌ 기획회의 결과 포맷팅 오류: {e}")
        return {
            "summary": "기획회의 결과 처리 중 오류가 발생했습니다.",
            "transcript": transcript
        }

@app.get("/api/analysis-history")
async def get_analysis_history():
    """분석 히스토리 조회 (추후 구현)"""
    return {
        "status": "success", 
        "history": [],
        "message": "히스토리 기능은 준비 중입니다"
    }

@app.get("/api/test-result")
async def get_test_result():
    """테스트용 분석 결과 반환"""
    try:
        # 기존 분석 결과 파일 읽기
        result_file = Path(__file__).parent.parent.parent / "data" / "qa_analysis_result_20250811_203558.json"
        if result_file.exists():
            import json
            with open(result_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # 가짜 스크립트 추가
            test_data["transcript"] = """[00:00] 리더: 안녕하세요 준희님, 오늘도 1on1 미팅 시간이 되었네요. 어떻게 지내세요?

[00:15] 준희: 네, 안녕하세요. 요즘 잠을 너무 못 잤는데 그래도 괜찮습니다.

[00:25] 리더: 그럼 오늘은 수습 기간이 거의 끝나가는 시점에서 여러 가지 이야기를 나눠보려고 해요. 먼저 회사 적응은 어떤가요?

[00:40] 준희: 네, 벌써 두 달 반이 다 되어가는데요. 처음 왔을 때보다는 훨씬 편해지고 적응하고 있다는 게 느껴집니다...

[이하 생략...]"""
            
            return JSONResponse(content={
                "status": "success",
                "meeting_type": "1on1",
                "timestamp": datetime.now().isoformat(),
                **test_data
            })
        
        return JSONResponse(content={
            "status": "error",
            "message": "테스트 결과 파일을 찾을 수 없습니다"
        })
        
    except Exception as e:
        logger.error(f"❌ 테스트 결과 로드 오류: {str(e)}")
        return JSONResponse(content={
            "status": "error",
            "message": f"테스트 결과 로드 실패: {str(e)}"
        })

@app.post("/api/export/{analysis_id}")
async def export_analysis(analysis_id: str, format: str = "pdf"):
    """분석 결과 내보내기 (추후 구현)"""
    return {
        "status": "success",
        "message": f"내보내기 기능은 준비 중입니다 (ID: {analysis_id}, Format: {format})"
    }

# 정적 파일 서빙 (모든 API 라우트 뒤에 배치)
if frontend_path.exists():
    @app.get("/{file_path:path}")
    async def serve_static_files(file_path: str):
        """정적 파일 서빙 (JS, CSS 등)"""
        # API 경로는 제외
        if file_path.startswith('api/'):
            raise HTTPException(status_code=404, detail="Not found")
        
        # 루트 경로는 index.html 반환
        if file_path == "" or file_path == "/":
            return FileResponse(frontend_path / "index.html")
            
        # 파일 존재 확인
        file_full_path = frontend_path / file_path
        if file_full_path.exists() and file_full_path.is_file():
            return FileResponse(file_full_path)
        
        # 파일이 없으면 index.html 반환 (SPA 지원)
        return FileResponse(frontend_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)