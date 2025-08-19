from typing import Dict, Any
from langgraph.graph import StateGraph, END
import assemblyai as aai
from supabase import Client
import json
import logging
import time
from datetime import datetime

from src.utils.model import MeetingAnalyzer, SpeechTranscriber
from src.utils.stt_schemas import MeetingPipelineState, MeetingAnalysis
from src.prompts.stt_generation.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate

# 로깅 설정
logger = logging.getLogger("meeting_pipeline")

# 성능 로깅 임포트
from src.utils.performance_logging import (
    time_node_execution, 
    generate_performance_report,
    SimpleTokenCallback
)

@time_node_execution("retrieve")
def retrieve_from_supabase(state: MeetingPipelineState) -> MeetingPipelineState:
    """Supabase에서 파일 조회 및 URL 생성"""
    logger.info(f"🔍 Supabase 파일 조회 시작: {state['file_id']}")
    
    try:
        state["status"] = "retrieving_file"
        
        # supabase_client 가져오기 (함수 속성으로 전달됨)
        supabase = getattr(retrieve_from_supabase, '_supabase_client', None)
        if not supabase:
            raise ValueError("Supabase 클라이언트가 초기화되지 않았습니다")
        
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
            raise ValueError(f"파일을 찾을 수 없습니다: {file_id}")
        
        file_info = found_files[0]
        file_path = file_info.get('full_path', file_info['name'])
        file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        # state 업데이트
        state["file_url"] = file_url
        state["file_path"] = file_path
        state["file_metadata"] = file_info
        
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
    logger.info("🎙️ STT 처리 시작")
    
    try:
        state["status"] = "transcribing"
        
        if not state.get("file_url"):
            raise ValueError("파일 URL이 없습니다")
        
        # AssemblyAI 설정 및 STT 처리 (timeout 연장)
        speech_transcriber = SpeechTranscriber()
        transcriber = aai.Transcriber(config=speech_transcriber.config)
        
        logger.info(f"🎙️ STT 시작 - 파일 URL: {state['file_url']}")
        
        # 폴링 방식으로 전사 처리 (timeout 증가)
        transcript = transcriber.transcribe(state["file_url"])
        
        # 전사 상태 확인 및 대기
        import time
        max_wait_time = 900  # 15분 timeout
        check_interval = 10   # 10초마다 확인
        elapsed_time = 0
        
        while transcript.status in [aai.TranscriptStatus.processing, aai.TranscriptStatus.queued]:
            if elapsed_time >= max_wait_time:
                raise TimeoutError(f"STT 처리 시간 초과 ({max_wait_time}초)")
            
            logger.info(f"🔄 STT 처리 중... ({elapsed_time}초 경과)")
            time.sleep(check_interval)
            elapsed_time += check_interval
            transcript = transcriber.get_transcript(transcript.id)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"STT 처리 실패: {transcript.error}")
        
        # 화자 통계 계산 (원본 transcript 사용)
        speaker_stats = {}
        if transcript.utterances:
            for utterance in transcript.utterances:
                speaker = utterance.speaker or 'Unknown'
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {'word_count': 0, 'duration': 0}
                speaker_stats[speaker]['word_count'] += len(utterance.text.split()) if utterance.text else 0
                speaker_stats[speaker]['duration'] += (utterance.end or 0) - (utterance.start or 0)
        
        transcript_dict = {
            "utterances": [
                {
                    "speaker": utterance.speaker,
                    "text": utterance.text
                }
                for utterance in transcript.utterances
            ] if transcript.utterances else [],
            "metadata": {
                "file_id": state["file_id"],
                "processed_at": datetime.now().isoformat(),
                "total_duration": transcript.audio_duration
            }
        }
        
        state["transcript"] = transcript_dict
        state["speaker_stats"] = speaker_stats
        
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
    logger.info("🤖 LLM 분석 시작")
    
    try:
        state["status"] = "analyzing"
        
        if not state.get("transcript") or not state["transcript"].get("utterances"):
            raise ValueError("전사 결과가 없거나 비어있습니다. STT 처리를 확인해주세요.")
        
        # analyzer에서 LLM 가져오기
        analyzer = analyze_with_llm._analyzer if hasattr(analyze_with_llm, '_analyzer') else None
        if not analyzer:
            raise ValueError("분석기가 초기화되지 않았습니다")
        
        # 화자 통계 간소화 (발언 비율 계산)
        simplified_stats = {}
        speaker_stats = state.get("speaker_stats", {})
        if speaker_stats:
            total_words = sum(stats.get('word_count', 0) for stats in speaker_stats.values())
            for speaker_name, stats in speaker_stats.items():
                word_count = stats.get('word_count', 0)
                percentage = round((word_count / total_words) * 100, 1) if total_words > 0 else 0
                simplified_stats[speaker_name] = percentage
        
        # 프롬프트 데이터 준비
        user_prompt_template = PromptTemplate(
            input_variables=["transcript", "speaker_stats", "participants", "qa_pairs"],
            template=USER_PROMPT
        )
        
        # JSON 문자열 변환
        speaker_stats_json = json.dumps(simplified_stats, ensure_ascii=False) if simplified_stats else "{}"
        qa_pairs_json = json.dumps(state.get("qa_data"), ensure_ascii=False) if state.get("qa_data") else "[]"
        participants_json = json.dumps(state.get("participants_info"), ensure_ascii=False) if state.get("participants_info") else "{}"
        
        # 프롬프트 체인 구성
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt_template.template)
        ])
        
        # LLM에 필요한 transcript 데이터만 추출
        transcript_for_llm = [
            {
                "speaker": utterance["speaker"],
                "text": utterance["text"]
            }
            for utterance in state["transcript"].get("utterances", [])
        ]
        
        # 체인 생성 및 실행
        chain = prompt | analyzer.llm.with_structured_output(MeetingAnalysis)
        
        input_data = {
            "transcript": transcript_for_llm,
            "speaker_stats": speaker_stats_json,
            "participants": participants_json,
            "qa_pairs": qa_pairs_json
        }
        
        # 토큰 추적을 위한 콜백 설정
        token_callback = SimpleTokenCallback(state)
        
        # LLM 호출 (with_structured_output 사용하면서 콜백으로 토큰 추적)
        result = chain.invoke(input_data, config={"callbacks": [token_callback]})
        
        if result is None:
            raise ValueError("1:1 회의 분석 실패")
        
        # LLM 응답 상세 로깅
        logger.info(f"LLM 응답 타입: {type(result)}")
        if hasattr(result, 'detailed_discussion'):
            logger.info(f"detailed_discussion 길이: {len(result.detailed_discussion) if result.detailed_discussion else 0}")
            logger.info(f"detailed_discussion 마지막 100자: {result.detailed_discussion[-100:] if result.detailed_discussion else 'N/A'}")
        
        # Pydantic 객체를 직접 Dict로 변환 (JSON 변환 불필요)
        state["analysis_result"] = result.model_dump()
        state["status"] = "completed"
        
        logger.info("✅ LLM 분석 완료")
        
    except Exception as e:
        error_msg = f"LLM 분석 실패: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
    
    return state


# =============================================================================
# Pipeline 클래스
# =============================================================================

class MeetingPipeline:
    """1on1 미팅 분석 파이프라인"""
    
    def __init__(self, supabase_client: Client, analyzer: MeetingAnalyzer):
        """
        Args:
            supabase_client: Supabase 클라이언트
            analyzer: 회의 분석기
        """
        self.supabase = supabase_client
        self.analyzer = analyzer
        self.workflow = self._build_graph()
        logger.info("MeetingPipeline 초기화 완료")
    
    def _build_graph(self) -> Any:
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(MeetingPipelineState)
        
        # supabase_client와 analyzer를 노드 함수에 바인딩
        retrieve_from_supabase._supabase_client = self.supabase
        analyze_with_llm._analyzer = self.analyzer
        
        # 노드 추가
        workflow.add_node("retrieve", retrieve_from_supabase)
        workflow.add_node("transcribe", process_with_assemblyai)
        workflow.add_node("analyze", analyze_with_llm)
        
        # 엣지 연결
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "transcribe")
        workflow.add_edge("transcribe", "analyze")
        workflow.add_edge("analyze", END)
        
        return workflow.compile()
    
    async def run(self, file_id: str, **kwargs) -> Dict:
        """파이프라인 실행"""
        logger.info(f"🚀 파이프라인 실행 시작: {file_id}")
        
        # 초기 상태 설정 (파일 조회는 retrieve 노드에서 처리)
        bucket_name = kwargs.get("bucket_name", "audio-recordings")
        
        initial_state: MeetingPipelineState = {
            "file_id": file_id,
            "bucket_name": bucket_name,
            "qa_data": kwargs.get("qa_data"),
            "participants_info": kwargs.get("participants_info"),
            "meeting_datetime": kwargs.get("meeting_datetime"),
            "file_url": None,  # retrieve 노드에서 설정
            "file_path": None,  # retrieve 노드에서 설정
            "file_metadata": None,  # retrieve 노드에서 설정
            "transcript": None,
            "speaker_stats": None,
            "analysis_result": None,
            "errors": [],
            "status": "pending"
        }
        
        # LangGraph 워크플로우 실행
        result = await self.workflow.ainvoke(initial_state)
        
        # 성공적으로 완료된 경우 성능 리포트 생성 (비용 계산 포함)
        if result.get("status") == "completed":
            generate_performance_report(result)
        
        logger.info(f"✅ 파이프라인 실행 완료: {result['status']}")
        
        return result