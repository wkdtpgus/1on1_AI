import json
import logging
import time
import assemblyai as aai
from src.utils.model import SpeechTranscriber, title_llm, meeting_llm
from src.utils.schemas import MeetingPipelineState, MeetingAnalysis
from src.prompts.stt_generation.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.prompts.stt_generation.title_generation_prompts import TITLE_ONLY_SYSTEM_PROMPT, TITLE_ONLY_USER_PROMPT
from src.utils.performance_logging import time_node_execution
from src.config.config import STT_MAX_WAIT_TIME, STT_CHECK_INTERVAL
from src.utils.utils import calculate_speaker_percentages, map_speaker_data
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("meeting_nodes")


@time_node_execution("retrieve")
def retrieve_from_supabase(state: MeetingPipelineState) -> MeetingPipelineState:
    """프론트에서 전달받은 URL 처리"""
    logger.info(f"Recording URL 처리 시작: {state.get('recording_url', 'No URL provided')}")
    
    try:
        state["status"] = "retrieving_file"
        
        # recording_url이 있는지 확인
        if not state.get("recording_url"):
            logger.error("Recording URL이 제공되지 않았습니다")
            state["status"] = "failed"
            return state
        
        # 프론트에서 전달받은 URL을 그대로 사용
        state["file_url"] = state["recording_url"]
        
        logger.info(f"✅ URL 설정 완료: {state['file_url']}")
        
    except Exception as e:
        error_msg = f"Recording URL 처리 실패: {str(e)}"
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
        
        speech_transcriber = SpeechTranscriber()
        transcriber = aai.Transcriber(config=speech_transcriber.config)
        
        logger.info(f"STT 시작 - 파일 URL: {state['file_url']}")
        transcript = transcriber.transcribe(state["file_url"])
        
        # 전사 상태 확인 및 대기
        elapsed_time = 0
        max_wait_time = STT_MAX_WAIT_TIME
        check_interval = STT_CHECK_INTERVAL
        
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
        
        formatted_transcript = []
        if transcript.utterances:
            formatted_transcript = [
                {
                    "speaker": utterance.speaker,
                    "text": utterance.text
                }
                for utterance in transcript.utterances
            ]
            
            # STT 결과 로그 출력
            logger.info(f"📝 STT 전사 결과 - 총 {len(formatted_transcript)}개 발화")
            
            # 화자별 발화 수 계산
            speaker_counts = {}
            for utterance in formatted_transcript:
                speaker = utterance.get("speaker", "Unknown")
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            logger.info(f"🎭 화자별 발화 수: {speaker_counts}")
            
            # 처음 5개 발화 샘플 출력
            logger.info("📋 처음 5개 발화 샘플:")
            for i, utterance in enumerate(formatted_transcript[:5]):
                speaker = utterance.get("speaker", "Unknown")
                text = utterance.get("text", "")
                # 텍스트가 너무 길면 잘라서 표시
                if len(text) > 100:
                    text = text[:100] + "..."
                logger.info(f"  [{i+1}] {speaker}: {text}")
        
        # 화자별 발화 시간 비율 계산
        speaker_stats_percent = calculate_speaker_percentages(transcript.utterances)
        
        # 화자별 발화 비율 로그 출력
        logger.info(f"📊 화자별 발화 시간 비율: {speaker_stats_percent}")
        
        state["transcript"] = {
            "utterances": formatted_transcript,
            "total_duration": transcript.audio_duration  # STT 비용 계산용
        }
        state["speaker_stats_percent"] = speaker_stats_percent
        
        logger.info("✅ STT 처리 완료")
        
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
        
        user_prompt_template = PromptTemplate(
            input_variables=["meeting_datetime", "transcript", "speaker_stats", "participants", "qa_pairs"],
            template=USER_PROMPT
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt_template.template)
        ])
        
        transcript_for_llm = state.get("transcript", {}).get("utterances", [])
        
        # 화자 통계
        speaker_stats = state.get("speaker_stats_percent", {})
        
        qa_pairs = json.loads(state.get("qa_pairs")) if state.get("qa_pairs") else []
        
        participants_info = json.loads(state.get("participants_info")) if state.get("participants_info") else {}
        
        input_data = {
            "meeting_datetime": state.get("meeting_datetime", "날짜/시간 정보 없음"),
            "transcript": transcript_for_llm,
            "speaker_stats": speaker_stats,
            "participants": participants_info,
            "qa_pairs": qa_pairs
        }
        
        chain = prompt | meeting_llm.with_structured_output(MeetingAnalysis)
        
        result = chain.invoke(input_data)
        
        if result is None:
            logger.error("회의 분석 실패")
            state["status"] = "failed"
            return state
        
        logger.info(f"LLM 분석 결과: {type(result).__name__}")
        
        analysis_dict = result.model_dump()
        
        # 화자 매핑 및 통계 변환
        original_stats = state.get("speaker_stats_percent", {})
        original_utterances = state.get("transcript", {}).get("utterances", [])
        
        analysis_dict = map_speaker_data(analysis_dict, original_stats, original_utterances, participants_info)
        
        state["analysis_result"] = analysis_dict
        state["status"] = "completed"
        
        logger.info("✅ LLM 분석 완료")
        
    except Exception as e:
        error_msg = f"LLM 분석 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state


@time_node_execution("generate_title")
def generate_title_only(state: MeetingPipelineState) -> MeetingPipelineState:
    """제목만 생성하는 노드"""
    logger.info("제목 전용 생성 시작")
    
    try:
        state["status"] = "analyzing"
        
        title_user_prompt_template = PromptTemplate(
            input_variables=["participants", "qa_pairs"],
            template=TITLE_ONLY_USER_PROMPT
        )
        
        title_prompt = ChatPromptTemplate.from_messages([
            ("system", TITLE_ONLY_SYSTEM_PROMPT),
            ("human", title_user_prompt_template.template)
        ])
        
        qa_pairs = json.loads(state.get("qa_pairs")) if state.get("qa_pairs") else []
        participants_info = json.loads(state.get("participants_info")) if state.get("participants_info") else {}
        
        title_input_data = {
            "participants": participants_info,
            "qa_pairs": qa_pairs
        }
        
        title_chain = title_prompt | title_llm
        
        title_result = title_chain.invoke(title_input_data)
        
        if title_result is None:
            logger.error("제목 생성 실패")
            state["status"] = "failed"
            return state
        
        state["analysis_result"] = {"title": title_result.content.strip()}
        state["status"] = "completed"
        
        logger.info("✅ 제목 생성 완료")
        
    except Exception as e:
        error_msg = f"제목 생성 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state