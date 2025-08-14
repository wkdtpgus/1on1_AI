import tempfile
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger("api_utils")

# 서비스 인스턴스
audio_processor = None
meeting_analyzer = None

def validate_services(audio_processor, meeting_analyzer) -> None:
    """서비스 초기화 상태 검증"""
    if not audio_processor or not meeting_analyzer:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")

def validate_audio_file(filename: str) -> str:
    """오디오 파일 형식 검증"""
    allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다")
    return file_ext

def create_temp_file(content: bytes, file_ext: str) -> str:
    """임시 파일 생성"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        temp_file.write(content)
        return temp_file.name

def process_audio_transcription(audio_processor, temp_audio_path: str) -> dict:
    """오디오 전사 처리"""
    transcript_result = audio_processor.transcribe_audio(temp_audio_path, expected_speakers=2)
    if not transcript_result or 'transcript' not in transcript_result:
        raise HTTPException(status_code=500, detail="STT 처리에 실패했습니다")
    return transcript_result

def parse_json_input(json_str: Optional[str]):
    """JSON 입력 파싱"""
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def perform_meeting_analysis(meeting_analyzer, transcript: str, speaker_stats: dict, qa_list, participants) -> dict:
    """미팅 분석 수행"""
    analysis_result = meeting_analyzer.analyze_1on1_meeting(
        transcript=transcript,
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
        analysis_data["transcript"] = transcript
    
    return analysis_data

def create_success_response(analysis_data: dict, filename: str, content: bytes, file_ext: str) -> JSONResponse:
    """성공 응답 생성"""
    response = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        **analysis_data,
        "file_info": {
            "filename": filename,
            "size": len(content),
            "format": file_ext
        }
    }
    return JSONResponse(content=response)

def cleanup_temp_file(temp_audio_path: Optional[str]) -> None:
    """임시 파일 정리"""
    if temp_audio_path and os.path.exists(temp_audio_path):
        try:
            os.unlink(temp_audio_path)
        except Exception as e:
            logger.warning(f"임시 파일 삭제 실패: {e}")

async def initialize_services(assemblyai_key: str, google_project: str, google_location: str, google_credentials: str):
    """서비스 초기화"""
    global audio_processor, meeting_analyzer
    
    from src.utils.formatter import STTProcessor
    from src.models.analysis import GeminiMeetingAnalyzer
    
    try:
        setup_google_credentials(google_credentials)
        audio_processor = STTProcessor(api_key=assemblyai_key)
        meeting_analyzer = GeminiMeetingAnalyzer(
            google_project=google_project, 
            google_location=google_location
        )
        logger.info("모든 모듈 초기화 완료")
    except Exception as e:
        logger.error(f"초기화 오류: {str(e)}")
        raise

def setup_google_credentials(google_credentials_json: str) -> None:
    """Google 자격증명 설정"""
    if google_credentials_json:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(google_credentials_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

def get_audio_processor():
    """오디오 프로세서 인스턴스 반환"""
    return audio_processor

def get_meeting_analyzer():
    """미팅 분석기 인스턴스 반환"""
    return meeting_analyzer