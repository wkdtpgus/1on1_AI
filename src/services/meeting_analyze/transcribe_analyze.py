import json
import logging
import time
import assemblyai as aai
from src.utils.model import SpeechTranscriber
from src.utils.stt_schemas import MeetingPipelineState, MeetingAnalysis
from src.prompts.stt_generation.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.utils.performance_logging import time_node_execution, SimpleTokenCallback
from src.config.config import SUPABASE_BUCKET_NAME
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
        
        bucket_name = SUPABASE_BUCKET_NAME
        file_id = state["file_id"]
        
        # 파일 경로 
        file_path = f"recordings/{file_id}"
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
            
            # (합이 100이 되도록 보장)
            if total_duration_ms > 0:
                speakers = list(speaker_stats.keys())
                percentages = []
                
                # 먼저 모든 비율을 계산
                for speaker_name, stats in speaker_stats.items():
                    duration_ms = stats.get('duration', 0)
                    percentage = (duration_ms / total_duration_ms) * 100
                    percentages.append(percentage)
                
                # 반올림하되 합이 100이 되도록 조정
                rounded_percentages = [round(p, 1) for p in percentages]
                current_sum = sum(rounded_percentages)
                
                # 합이 100이 아니면 가장 큰 값을 조정
                if current_sum != 100.0:
                    diff = round(100.0 - current_sum, 1)
                    max_index = percentages.index(max(percentages))
                    rounded_percentages[max_index] = round(rounded_percentages[max_index] + diff, 1)
                
                # 결과 저장
                for i, speaker_name in enumerate(speakers):
                    speaker_stats_percent[speaker_name] = rounded_percentages[i]
            else:
                # total_duration_ms가 0이면 모든 화자에게 0 할당
                for speaker_name in speaker_stats.keys():
                    speaker_stats_percent[speaker_name] = 0.0
        
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
        
        # LLM 입력 데이터 준비 (Python 객체로 통일)
        transcript_for_llm = state.get("transcript", {}).get("utterances", [])
        
        # 화자 통계
        speaker_stats = state.get("speaker_stats_percent", {})
        
        # Q&A 데이터 파싱
        qa_pairs = json.loads(state.get("qa_pairs")) if state.get("qa_pairs") else []
        
        # 참가자 정보 파싱
        participants_info = json.loads(state.get("participants_info")) if state.get("participants_info") else {}
        
        input_data = {
            "meeting_datetime": state.get("meeting_datetime", "날짜/시간 정보 없음"),
            "transcript": transcript_for_llm,
            "speaker_stats": speaker_stats,
            "participants": participants_info,
            "qa_pairs": qa_pairs
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
        
        # Pydantic 객체를 Dict로 변환하고 추가 데이터 포함
        analysis_dict = result.model_dump()
        
        # speaker_mapping을 사용해 speaker_stats_percent를 실제 이름으로 변환
        original_stats = state.get("speaker_stats_percent", {})
        speaker_mapping_list = analysis_dict.pop("speaker_mapping", ["리더", "팀원"])
        
        # speaker_mapping_list와 participants를 비교해서 누가 리더인지 판단
        leader_name = participants_info.get("leader", "리더")
        member_name = participants_info.get("member", "팀원")
        
        # A와 B 중 누가 리더인지 확인
        if speaker_mapping_list[0] == leader_name:
            # A가 리더인 경우
            leader_ratio = original_stats.get("A", 0)
            member_ratio = original_stats.get("B", 0)
        else:
            # B가 리더인 경우 (또는 기본값)
            leader_ratio = original_stats.get("B", 0)
            member_ratio = original_stats.get("A", 0)
        
        mapped_stats = {
            "speaking_ratio_leader": leader_ratio,
            "speaking_ratio_member": member_ratio
        }
        
        analysis_dict["speaker_stats_percent"] = mapped_stats
        
        # transcript의 utterances에서도 A, B를 실제 이름으로 변경
        original_utterances = state.get("transcript", {}).get("utterances", [])
        mapped_utterances = []
        
        for utterance in original_utterances:
            mapped_utterance = utterance.copy()
            if utterance.get("speaker") == "A":
                mapped_utterance["speaker"] = speaker_mapping_list[0]
            elif utterance.get("speaker") == "B":
                mapped_utterance["speaker"] = speaker_mapping_list[1]
            mapped_utterances.append(mapped_utterance)
        
        analysis_dict["transcript"] = mapped_utterances
        
        state["analysis_result"] = analysis_dict
        state["status"] = "completed"
        
        logger.info("✅ LLM 분석 완료")
        
    except Exception as e:
        error_msg = f"LLM 분석 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state