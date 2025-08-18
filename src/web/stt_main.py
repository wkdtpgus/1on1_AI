from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

# 프로젝트 모듈 임포트
from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_CLOUD_PROJECT, 
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_APPLICATION_CREDENTIALS_JSON,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_BUCKET_NAME
)
import os
import json
from datetime import datetime
from fastapi.responses import JSONResponse
import assemblyai as aai
from supabase import create_client, Client

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_main")

# 서비스 인스턴스
audio_processor = None
meeting_analyzer = None
supabase: Client = None

# 더 이상 Pydantic 모델이 필요하지 않음 (Form 데이터 직접 처리)

# 헬퍼 함수들
async def find_file_in_storage(bucket_name: str, file_id: str):
    """재귀적으로 스토리지에서 파일을 찾는 함수"""
    def search_files(path: str = ""):
        try:
            files = supabase.storage.from_(bucket_name).list(path)
            found = []
            
            for file in files:
                file_path = f"{path}/{file['name']}" if path else file['name']
                
                if file.get('id') is not None or '.' in file['name']:
                    if (file['name'] == file_id or 
                        file_path == file_id or 
                        file_id in file['name']):
                        found.append({**file, "full_path": file_path})
                else:
                    try:
                        sub_found = search_files(file_path)
                        found.extend(sub_found)
                    except:
                        pass
            return found
        except:
            return []
    
    return search_files()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global audio_processor, meeting_analyzer, supabase
    
    # Google 자격증명 설정
    if GOOGLE_APPLICATION_CREDENTIALS_JSON:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(GOOGLE_APPLICATION_CREDENTIALS_JSON)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    
    # Supabase 초기화
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # AssemblyAI 초기화
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    
    # 서비스 초기화 (각 클래스가 자체 검증 수행)
    from src.utils.formatter import STTProcessor
    from src.utils.model import GeminiMeetingAnalyzer
    
    audio_processor = STTProcessor(api_key=ASSEMBLYAI_API_KEY)
    meeting_analyzer = GeminiMeetingAnalyzer(
        google_project=GOOGLE_CLOUD_PROJECT, 
        google_location=GOOGLE_CLOUD_LOCATION
    )
    logger.info("모든 서비스 초기화 완료")
    logger.info(f"Supabase 연결: {SUPABASE_URL}")
    logger.info(f"기본 버킷: {SUPABASE_BUCKET_NAME}")
    
    yield
    # 종료시 정리 (필요시)
    pass

# FastAPI 앱 생성
app = FastAPI(
    title="1on1 Meeting AI Analysis", 
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """메인 페이지"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

@app.get("/api.js")
async def api_js():
    """API JavaScript 파일"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/api.js", media_type="application/javascript")

@app.get("/app.js")
async def app_js():
    """앱 JavaScript 파일"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/app.js", media_type="application/javascript")

@app.get("/favicon.ico")
async def favicon():
    """파비콘"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/favicon.ico", media_type="image/x-icon")

@app.get("/api/config")
async def get_config():
    """프론트엔드용 설정 정보 제공"""
    return {
        "supabase_url": SUPABASE_URL,
        "supabase_key": SUPABASE_KEY,
        "bucket_name": SUPABASE_BUCKET_NAME
    }



@app.post("/api/analyze")
async def analyze_meeting_with_storage(
    file_id: str = Form(...),
    qa_data: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None),
    bucket_name: Optional[str] = Form(default=SUPABASE_BUCKET_NAME)
):
    """
    Supabase 스토리지 파일을 사용한 1on1 미팅 분석 API
    
    Args:
        file_id: Supabase 스토리지 파일 ID
        qa_data: Q&A 데이터 (JSON 문자열)
        participants_info: 참가자 정보 (JSON 문자열)
        bucket_name: 버킷 이름
    """
    if not audio_processor or not meeting_analyzer:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")
    
    try:
        # 1. 파일 찾기 및 STT 처리
        logger.info(f"🔍 파일 검색: {file_id}")
        
        found_files = await find_file_in_storage(bucket_name, file_id)
        if not found_files:
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_id}")
        
        # 2. URL 생성 및 STT 처리
        file_info = found_files[0]
        file_path = file_info.get('full_path', file_info['name'])
        file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        logger.info(f"🌐 공개 URL 생성: {file_url}")
        
        # AssemblyAI 설정
        from src.config.config import (
            ASSEMBLYAI_LANGUAGE,
            ASSEMBLYAI_PUNCTUATE,
            ASSEMBLYAI_FORMAT_TEXT,
            ASSEMBLYAI_DISFLUENCIES,
            ASSEMBLYAI_SPEAKER_LABELS,
            ASSEMBLYAI_SPEAKERS_EXPECTED
        )
        
        config = aai.TranscriptionConfig(
            language_code=ASSEMBLYAI_LANGUAGE,
            speaker_labels=ASSEMBLYAI_SPEAKER_LABELS,
            speakers_expected=ASSEMBLYAI_SPEAKERS_EXPECTED,
            punctuate=ASSEMBLYAI_PUNCTUATE,
            format_text=ASSEMBLYAI_FORMAT_TEXT,
            filter_profanity=ASSEMBLYAI_DISFLUENCIES
        )
        
        # STT 처리 (URL 직접 사용)
        logger.info(f"🎙️ AssemblyAI STT 처리 시작...")
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(file_url)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"STT 처리 실패: {transcript.error}")
        
        # AssemblyAI transcript를 dict로 변환
        transcript_dict = {
            "id": transcript.id,
            "status": transcript.status.value,
            "text": transcript.text,
            "confidence": transcript.confidence,
            "audio_duration": transcript.audio_duration,
            "words": [
                {
                    "text": word.text,
                    "start": word.start,
                    "end": word.end,
                    "confidence": word.confidence,
                    "speaker": getattr(word, 'speaker', None)
                }
                for word in transcript.words
            ] if transcript.words else [],
            "utterances": [
                {
                    "text": utterance.text,
                    "start": utterance.start,
                    "end": utterance.end,
                    "confidence": utterance.confidence,
                    "speaker": utterance.speaker
                }
                for utterance in transcript.utterances
            ] if transcript.utterances else [],
            "supabase_metadata": {
                "file_id": file_id,
                "file_path": file_path,
                "file_url": file_url,
                "bucket_name": bucket_name,
                "processed_at": datetime.now().isoformat()
            }
        }
        
        # 3. 화자 통계 계산
        speaker_stats = {}
        if transcript_dict.get('utterances'):
            for utterance in transcript_dict['utterances']:
                speaker = utterance.get('speaker', 'Unknown')
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {'word_count': 0, 'duration': 0}
                speaker_stats[speaker]['word_count'] += len(utterance.get('text', '').split())
                speaker_stats[speaker]['duration'] += utterance.get('end', 0) - utterance.get('start', 0)
        
        # 4. JSON 입력 파싱
        qa_list = json.loads(qa_data) if qa_data else None
        participants = json.loads(participants_info) if participants_info else None
        
        # 5. LLM 분석 수행
        analysis_result = meeting_analyzer.analyze_1on1_meeting(
            transcript=transcript_dict,
            speaker_stats=speaker_stats,
            qa_pairs=qa_list,
            participants=participants
        )
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {"error": "분석 결과 파싱 실패", "raw_result": analysis_result}
        
        # transcript 추가
        if isinstance(analysis_data, dict):
            analysis_data["transcript"] = transcript_dict
        
        # 6. 성공 응답 생성
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **analysis_data,
            "file_info": {
                "file_id": file_id,
                "bucket_name": bucket_name,
                "file_path": file_path
            }
        }
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 처리 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)