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
from src.models.llm_analysis import GeminiMeetingAnalyzer

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
    import os
    initialization_error = None
    
    try:
        # 환경 변수 체크
        logger.info(f"📋 환경 변수 체크:")
        logger.info(f"  - GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
        logger.info(f"  - GOOGLE_CLOUD_LOCATION: {os.getenv('GOOGLE_CLOUD_LOCATION', 'NOT SET')}")
        logger.info(f"  - ASSEMBLYAI_API_KEY: {'SET' if os.getenv('ASSEMBLYAI_API_KEY') else 'NOT SET'}")
        logger.info(f"  - GOOGLE_APPLICATION_CREDENTIALS_JSON: {'SET' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON') else 'NOT SET'}")
        
        # Google 자격증명 JSON이 제공되면 파일로 저장해 ADC 구성
        try:
            creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            creds_path_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_json and not creds_path_env:
                creds_path = "/tmp/gcp_creds.json"
                with open(creds_path, "w", encoding="utf-8") as f:
                    f.write(creds_json)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                logger.info("✅ GOOGLE_APPLICATION_CREDENTIALS가 JSON에서 설정되었습니다")
        except Exception as e:
            logger.warning(f"⚠️ Google 자격증명 설정 실패: {e}")
        
        logger.info("🎵 오디오 프로세서 초기화 중...")
        assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
        audio_processor = AudioProcessor(assemblyai_api_key=assemblyai_api_key)
        logger.info("✅ 오디오 프로세서 초기화 완료")
        
        logger.info("🤖 Gemini LLM 분석기 초기화 중...")
        google_project = os.getenv('GOOGLE_CLOUD_PROJECT')
        google_location = os.getenv('GOOGLE_CLOUD_LOCATION')
        meeting_analyzer = GeminiMeetingAnalyzer(google_project=google_project, google_location=google_location)
        logger.info("✅ Gemini LLM 분석기 초기화 완료")
            
        logger.info("✅ 모든 모듈 초기화 완료")
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"❌ 초기화 오류: {str(e)}")
        logger.error(f"❌ 초기화 오류 상세:\n{error_detail}")
        initialization_error = str(e)
        # 초기화 실패해도 앱은 시작하도록 함
    
    yield  # 앱이 실행되는 동안
    
    # 앱 종료 시
    if initialization_error:
        app.state.initialization_error = initialization_error
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
    init_error = getattr(app.state, 'initialization_error', None)
    return {
        "status": "healthy" if not init_error else "error",
        "timestamp": datetime.now().isoformat(),
        "audio_processor": audio_processor is not None,
        "meeting_analyzer": meeting_analyzer is not None,
        "initialization_error": init_error
    }

@app.get("/api/debug")
async def debug_env():
    """환경 변수 디버깅"""
    import os
    import sys
    return {
        "google_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "google_location": os.getenv("GOOGLE_CLOUD_LOCATION"),
        "assemblyai_key_exists": bool(os.getenv("ASSEMBLYAI_API_KEY")),
        "google_creds_exists": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")),
        "python_version": sys.version,
        "current_working_directory": os.getcwd()
    }

@app.get("/api/test-init")
async def test_initialization():
    """초기화 테스트"""
    try:
        # AudioProcessor 테스트
        from src.models.audio_processing import AudioProcessor
        audio_test = AudioProcessor()
        audio_status = "OK"
    except Exception as e:
        audio_status = f"ERROR: {str(e)}"
    
    try:
        # GeminiMeetingAnalyzer 테스트
        from src.models.llm_analysis import GeminiMeetingAnalyzer
        gemini_test = GeminiMeetingAnalyzer()
        gemini_status = "OK"
    except Exception as e:
        gemini_status = f"ERROR: {str(e)}"
    
    return {
        "audio_processor": audio_status,
        "gemini_analyzer": gemini_status,
        "global_audio_processor": audio_processor is not None,
        "global_meeting_analyzer": meeting_analyzer is not None
    }

@app.post("/api/analyze")
async def analyze_meeting(
    audio_file: UploadFile = File(...),
    meeting_type: str = Form(default="1on1"),
    qa_data: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None)
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
        
        # 0. 참가자 수 계산 (STT 처리 최적화용)
        expected_speakers = 2  # 기본값 (1on1)
        if participants_info:
            try:
                participants = json.loads(participants_info)
                if meeting_type == "1on1":
                    expected_speakers = 2  # 1on1은 항상 2명
                else:
                    # 다른 회의 타입들은 participants 리스트 길이 사용
                    participant_list = participants.get('participants', [])
                    if participant_list:
                        expected_speakers = len(participant_list)
                        logger.info(f"👥 참가자 수: {expected_speakers}명")
            except json.JSONDecodeError as e:
                logger.error(f"❌ 참가자 정보 JSON 파싱 오류: {e}")
        
        # 1. STT 처리 (참가자 수 포함)
        logger.info(f"🎙️ STT 처리 시작... (예상 화자 수: {expected_speakers})")
        transcript_result = audio_processor.transcribe_existing_file(temp_audio_path, expected_speakers=expected_speakers)
        
        if not transcript_result or 'transcript' not in transcript_result:
            raise HTTPException(status_code=500, detail="STT 처리에 실패했습니다")
        
        transcript = transcript_result['transcript']
        speaker_stats = transcript_result.get('speaker_stats', {})
        
        logger.info(f"✅ STT 완료 (길이: {len(transcript)}자)")
        
        # 2. 질문 사용 안 함(qa_pairs JSON만 사용)
        
        # 3. Q&A 데이터 처리 (JSON 그대로 사용)
        qa_list = None
        if qa_data:
            try:
                qa_list = json.loads(qa_data)
                logger.info(f"🔍 받은 Q&A 데이터: {len(qa_list)}개 항목")
                for i, qa in enumerate(qa_list):
                    logger.info(f"  Q{i+1}: {qa.get('question', '질문없음')[:50]}...")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Q&A 데이터 JSON 파싱 오류: {e}")
                qa_list = None
        
        # 4. 참석자 정보 처리
        participants = None
        if participants_info:
            try:
                participants = json.loads(participants_info)
                # 1on1과 다른 회의 타입별로 다르게 로깅
                if meeting_type == "1on1":
                    logger.info(f"👥 받은 참석자 정보: 리더={participants.get('leader', '미지정')}, 멤버={participants.get('member', '미지정')}")
                else:
                    participant_list = participants.get('participants', [])
                    logger.info(f"👥 받은 참석자 정보: {', '.join(participant_list) if participant_list else '미지정'}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ 참석자 정보 JSON 파싱 오류: {e}")
                participants = None
        
        # 3. LLM 분석 (미팅 타입별)
        if meeting_type == "1on1":
            logger.info("🤖 1on1 미팅 LLM 분석 시작...")
            analysis_result = meeting_analyzer.analyze_1on1_meeting(
                transcript=transcript,
                speaker_stats=speaker_stats,
                qa_pairs=qa_list,
                participants=participants
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
                speaker_stats=speaker_stats,
                participants=participants
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
        
        elif meeting_type == "general":
            logger.info("🤖 일반회의 LLM 분석 시작...")
            analysis_result = meeting_analyzer.analyze_general_meeting(
                transcript=transcript,
                speaker_stats=speaker_stats,
                participants=participants
            )
            
            # JSON 파싱
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError as e:
                logger.error(f"❌ 일반회의 LLM 결과 JSON 파싱 오류: {e}")
                analysis_data = {"error": "일반회의 분석 결과 파싱 실패", "raw_result": analysis_result}
            
            logger.info("✅ 일반회의 LLM 분석 완료")
            
            # 프론트엔드 형식으로 변환
            formatted_result = format_general_analysis(analysis_data, transcript, speaker_stats)
            
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
        
        elif meeting_type == "weekly":
            logger.info("🤖 주간회의 LLM 분석 시작...")
            analysis_result = meeting_analyzer.analyze_weekly_meeting(
                transcript=transcript,
                speaker_stats=speaker_stats,
                participants=participants
            )
            
            # JSON 파싱
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError as e:
                logger.error(f"❌ 주간회의 LLM 결과 JSON 파싱 오류: {e}")
                analysis_data = {"error": "주간회의 분석 결과 파싱 실패", "raw_result": analysis_result}
            
            logger.info("✅ 주간회의 LLM 분석 완료")
            
            # 프론트엔드 형식으로 변환
            formatted_result = format_weekly_analysis(analysis_data, transcript, speaker_stats)
            
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
            # 다른 미팅 타입들은 간단한 전사 결과만 제공
            logger.info(f"📋 {meeting_type} 미팅 간단 처리...")
            
            # 참가자 정보 처리 (간단한 텍스트 추가)
            participants_text = ""
            if participants_info:
                try:
                    participants = json.loads(participants_info)
                    if 'participants' in participants and participants['participants']:
                        participants_text = f"\n\n회의 참가자: {', '.join(participants['participants'])}"
                        logger.info(f"👥 {meeting_type} 참가자: {participants['participants']}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 참가자 정보 JSON 파싱 오류: {e}")
            
            # 간단한 요약만 제공
            participant_count = len(participants['participants']) if participants_info and 'participants' in json.loads(participants_info or '{}') else 0
            participant_info = f" (참가자 {participant_count}명)" if participant_count > 0 else ""
            simple_summary = f"{meeting_type} 미팅 내용이 성공적으로 전사되었습니다{participant_info}. 총 {len(transcript)}자의 대화 내용입니다."
            
            # 전사 텍스트에 참가자 정보 추가
            full_transcript = transcript + participants_text
            
            final_response = {
                "status": "success",
                "meeting_type": meeting_type,
                "timestamp": datetime.now().isoformat(),
                "title": f"{meeting_type} 미팅 전사 결과",
                "summary": simple_summary,
                "transcript": full_transcript,
                "speaker_stats": speaker_stats,
                "file_info": {
                    "filename": audio_file.filename,
                    "size": len(content),
                    "format": file_ext
                }
            }
            
            logger.info(f"✅ {meeting_type} 미팅 처리 완료")
            return JSONResponse(content=final_response)
    
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
        result = {
            "title": analysis_data.get("title", "기획회의 분석 결과"),
            "detailed_discussion": analysis_data.get("detailed_discussion", ""),
            "strategic_insights": analysis_data.get("strategic_insights", []),
            "innovation_ideas": analysis_data.get("innovation_ideas", []),
            "risks_challenges": analysis_data.get("risks_challenges", []),
            "next_steps": analysis_data.get("next_steps", []),
            "transcript": transcript
        }
        return result
        
    except Exception as e:
        logger.error(f"❌ 기획회의 결과 포맷팅 오류: {e}")
        return {
            "summary": "기획회의 결과 처리 중 오류가 발생했습니다.",
            "transcript": transcript
        }

def format_general_analysis(analysis_data, transcript, speaker_stats):
    """일반회의 분석 결과를 프론트엔드 형식으로 변환"""
    try:
        # 에러가 있는 경우
        if "error" in analysis_data:
            return {
                "summary": "일반회의 분석 중 오류가 발생했습니다.",
                "transcript": transcript
            }
        
        # 일반회의 분석 결과가 있는 경우 그대로 반환
        result = {
            "title": analysis_data.get("title", "일반회의 분석 결과"),
            "detailed_discussion": analysis_data.get("detailed_discussion", ""),
            "discussion_topics": analysis_data.get("discussion_topics", []),
            "team_contributions": analysis_data.get("team_contributions", []),
            "action_items": analysis_data.get("action_items", []),
            "follow_up_items": analysis_data.get("follow_up_items", []),
            "transcript": transcript
        }
        return result
        
    except Exception as e:
        logger.error(f"❌ 일반회의 결과 포맷팅 오류: {e}")
        return {
            "summary": "일반회의 결과 처리 중 오류가 발생했습니다.",
            "transcript": transcript
        }

def format_weekly_analysis(analysis_data, transcript, speaker_stats):
    """주간회의 분석 결과를 프론트엔드 형식으로 변환"""
    try:
        # 에러가 있는 경우
        if "error" in analysis_data:
            return {
                "summary": "주간회의 분석 중 오류가 발생했습니다.",
                "transcript": transcript
            }
        
        # 주간회의 분석 결과가 있는 경우 그대로 반환
        result = {
            "title": analysis_data.get("title", "주간회의 분석 결과"),
            "detailed_discussion": analysis_data.get("detailed_discussion", ""),
            "progress_updates": analysis_data.get("progress_updates", []),
            "blockers_challenges": analysis_data.get("blockers_challenges", []),
            "next_week_priorities": analysis_data.get("next_week_priorities", []),
            "team_coordination": analysis_data.get("team_coordination", []),
            "transcript": transcript
        }
        return result
        
    except Exception as e:
        logger.error(f"❌ 주간회의 결과 포맷팅 오류: {e}")
        return {
            "summary": "주간회의 결과 처리 중 오류가 발생했습니다.",
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

@app.get("/api/test-qa-data")
async def get_test_qa_data():
    """김준희 테스트용 Q&A 데이터 반환"""
    try:
        # 테스트 Q&A 파일 경로
        qa_file = Path(__file__).parent.parent.parent / "data" / "qa_questions_20250812_180133.txt"
        
        if not qa_file.exists():
            return JSONResponse(content={
                "status": "error",
                "message": "테스트 Q&A 파일을 찾을 수 없습니다"
            })
        
        # 파일 읽기 및 파싱
        with open(qa_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Q&A 데이터 파싱
        qa_pairs = []
        sections = content.split('=== Question')
        
        for section in sections[1:]:  # 첫 번째는 빈 문자열이므로 제외
            lines = section.strip().split('\n')
            if len(lines) >= 3:
                # 질문 추출 (Q: 뒤의 내용)
                question_line = lines[1] if lines[1].startswith('Q: ') else ""
                question = question_line[3:] if question_line.startswith('Q: ') else ""
                
                # 답변 추출 (A: 뒤의 내용)
                answer_line = lines[2] if len(lines) > 2 and lines[2].startswith('A: ') else ""
                answer = answer_line[3:] if answer_line.startswith('A: ') else ""
                
                # 답변이 없거나 "(답변 없음)"인 경우 제외
                if question and answer and answer != "(답변 없음)":
                    qa_pairs.append({
                        "question": question.strip(),
                        "answer": answer.strip()
                    })
        
        logger.info(f"✅ 테스트 Q&A 데이터 로드 완료: {len(qa_pairs)}개 항목")
        
        return JSONResponse(content={
            "status": "success",
            "qa_data": qa_pairs,
            "count": len(qa_pairs)
        })
        
    except Exception as e:
        logger.error(f"❌ 테스트 Q&A 데이터 로드 오류: {str(e)}")
        return JSONResponse(content={
            "status": "error",
            "message": f"테스트 Q&A 데이터 로드 실패: {str(e)}"
        })

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