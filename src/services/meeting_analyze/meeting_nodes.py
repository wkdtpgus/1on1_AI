import json
import logging
import time
import assemblyai as aai
from src.utils.model import SpeechTranscriber
from src.utils.stt_schemas import MeetingPipelineState, MeetingAnalysis
from src.prompts.stt_generation.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.utils.performance_logging import time_node_execution, SimpleTokenCallback
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("meeting_nodes")


@time_node_execution("retrieve")
def retrieve_from_supabase(state: MeetingPipelineState) -> MeetingPipelineState:
    """Supabase에서 파일 조회 및 URL 생성"""
    logger.info(f"Supabase 파일 조회 시작: {state['file_id']}")
    
    try:
        state["status"] = "retrieving_file"
        
        # supabase_client 가져오기 (함수 속성으로 전달됨)
        supabase = getattr(retrieve_from_supabase, '_supabase_client', None)
        if not supabase:
            logger.error("Supabase 클라이언트가 초기화되지 않았습니다")
            state["status"] = "failed"
            return state
        
        bucket_name = state["bucket_name"]
        file_id = state["file_id"]
        
        # 재귀적 파일 검색
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
        
        found_files = search_files()
        if not found_files:
            logger.error(f"파일을 찾을 수 없습니다: {file_id}")
            state["status"] = "failed"
            return state
        
        file_info = found_files[0]
        file_path = file_info.get('full_path', file_info['name'])
        file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        # state 업데이트
        state["file_url"] = file_url
        state["file_path"] = file_path
        
        logger.info(f"✅ 파일 조회 완료: {file_path}")
        
    except Exception as e:
        error_msg = f"Supabase 파일 조회 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state


@time_node_execution("transcribe")
def process_with_assemblyai(state: MeetingPipelineState) -> MeetingPipelineState:
    """AssemblyAI로 STT 처리"""
    logger.info("STT 처리 시작")
    
    try:
        state["status"] = "transcribing"
        
        if not state.get("file_url"):
            logger.error("파일 URL이 없습니다")
            state["status"] = "failed"
            return state
        
        # AssemblyAI 설정 및 전사 시작
        speech_transcriber = SpeechTranscriber()
        transcriber = aai.Transcriber(config=speech_transcriber.config)
        
        logger.info(f"STT 시작 - 파일 URL: {state['file_url']}")
        transcript = transcriber.transcribe(state["file_url"])
        
        # 전사 상태 확인 및 대기
        elapsed_time = 0
        max_wait_time = 900
        check_interval = 10
        
        while transcript.status in [aai.TranscriptStatus.processing, aai.TranscriptStatus.queued]:
            if elapsed_time >= max_wait_time:
                logger.error(f"STT 처리 시간 초과 ({max_wait_time}초)")
                state["status"] = "failed"
                return state
            
            logger.info(f"🔄 STT 처리 중... ({elapsed_time}초 경과)")
            time.sleep(check_interval)
            elapsed_time += check_interval
            transcript = transcriber.get_transcript(transcript.id)
        
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"STT 처리 실패: {transcript.error}")
            state["status"] = "failed"
            return state
        
        # LLM용 포맷된 transcript (speaker, text만 포함)
        formatted_transcript = []
        if transcript.utterances:
            formatted_transcript = [
                {
                    "speaker": utterance.speaker,
                    "text": utterance.text
                }
                for utterance in transcript.utterances
            ]
        
        # 화자별 발화 시간 비율 계산
        speaker_stats_percent = {}
        if transcript.utterances:
            speaker_stats = {}
            total_duration_ms = 0
            
            # 화자별 발화 시간 계산
            for utterance in transcript.utterances:
                speaker = utterance.speaker or 'Unknown'
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {'duration': 0}
                duration_ms = (utterance.end or 0) - (utterance.start or 0)
                speaker_stats[speaker]['duration'] += duration_ms
                total_duration_ms += duration_ms
            
            # 퍼센트 계산
            for speaker_name, stats in speaker_stats.items():
                duration_ms = stats.get('duration', 0)
                percentage = round((duration_ms / total_duration_ms) * 100, 1) if total_duration_ms > 0 else 0
                speaker_stats_percent[speaker_name] = percentage
        
        # state 업데이트
        state["transcript"] = {
            "utterances": formatted_transcript,
            "total_duration": transcript.audio_duration  # STT 비용 계산용
        }
        state["speaker_stats_percent"] = speaker_stats_percent
        
        logger.info("✅ STT 처리 완료")
        
    except TimeoutError as e:
        error_msg = str(e)
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    except Exception as e:
        error_msg = f"STT 처리 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state


@time_node_execution("analyze")
def analyze_with_llm(state: MeetingPipelineState) -> MeetingPipelineState:
    """LLM으로 회의 분석"""
    logger.info("LLM 분석 시작")
    
    try:
        state["status"] = "analyzing"
        
        if not state.get("transcript") or not state["transcript"].get("utterances"):
            logger.error("전사 결과가 없거나 비어있습니다")
            state["status"] = "failed"
            return state
        
        # analyzer에서 LLM 가져오기
        analyzer = getattr(analyze_with_llm, '_analyzer', None)
        if not analyzer:
            logger.error("분석기가 초기화되지 않았습니다")
            state["status"] = "failed"
            return state
        
        # 프롬프트 데이터 준비
        user_prompt_template = PromptTemplate(
            input_variables=["meeting_datetime", "transcript", "speaker_stats", "participants", "qa_pairs"],
            template=USER_PROMPT
        )
        
        # 프롬프트 체인 구성
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt_template.template)
        ])
        
        # LLM 입력 데이터 준비 (JSON 변환)
        transcript_for_llm = state.get("transcript", {}).get("utterances", [])
        
        # 화자 통계 JSON 변환
        speaker_stats = state.get("speaker_stats_percent", {})
        speaker_stats_json = json.dumps(speaker_stats, ensure_ascii=False) if speaker_stats else "{}"
        
        # Q&A 데이터 JSON 변환
        qa_data = state.get("qa_data")
        qa_pairs_json = json.dumps(qa_data, ensure_ascii=False) if qa_data else "[]"
        
        # 참가자 정보 JSON 변환
        participants_info = state.get("participants_info")
        participants_json = json.dumps(participants_info, ensure_ascii=False) if participants_info else "{}"
        
        input_data = {
            "meeting_datetime": state.get("meeting_datetime", "날짜/시간 정보 없음"),
            "transcript": transcript_for_llm,
            "speaker_stats": speaker_stats_json,
            "participants": participants_json,
            "qa_pairs": qa_pairs_json
        }
        
        # 체인 생성 및 실행
        chain = prompt | analyzer.llm.with_structured_output(MeetingAnalysis)
        
        # 토큰 추적을 위한 콜백 설정
        token_callback = SimpleTokenCallback(state)
        
        # LLM 호출
        result = chain.invoke(input_data, config={"callbacks": [token_callback]})
        
        if result is None:
            logger.error("회의 분석 실패")
            state["status"] = "failed"
            return state
        
        logger.info(f"LLM 분석 결과: {type(result).__name__}")
        
        # Pydantic 객체를 Dict로 변환
        state["analysis_result"] = result.model_dump()
        state["status"] = "completed"
        
        logger.info("✅ LLM 분석 완료")
        
    except Exception as e:
        error_msg = f"LLM 분석 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state