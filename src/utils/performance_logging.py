import time
import logging
from typing import Dict, Any, Callable
from functools import wraps
from datetime import datetime

logger = logging.getLogger("performance_logging")

# 비용 계산 상수 (USD)
PRICING = {
    "assemblyai": 0.27 / 3600,  # $0.27/hour = $0.000075/sec
    "vertex_ai": {
        "input_small": 1.25 / 1000000,   # $1.25 per 1M tokens (<= 20만 토큰)
        "output_small": 10.00 / 1000000,  # $10.00 per 1M tokens (<= 20만 토큰)
        "input_large": 2.50 / 1000000,   # $2.50 per 1M tokens (> 20만 토큰)
        "output_large": 15.00 / 1000000,  # $15.00 per 1M tokens (> 20만 토큰)
    }
}

# 환율 (USD to KRW)
USD_TO_KRW = 1380




def time_node_execution(node_name: str):
    """노드 실행 시간 측정 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            # state에서 performance_metrics 가져오기 또는 생성
            if "performance_metrics" not in state or state["performance_metrics"] is None:
                state["performance_metrics"] = {}
                
            # 시작 시간 기록
            start_time = time.time()
            
            try:
                # 원본 함수 실행
                result = func(state, *args, **kwargs)
                
                # 실행 시간 계산 및 기록
                duration = time.time() - start_time
                state["performance_metrics"][f"{node_name}_duration"] = duration
                state["performance_metrics"][f"{node_name}_status"] = "success"
                
                logger.info(f"⏱️ {node_name} 실행 시간: {duration:.2f}초")
                
                return result
                
            except Exception as e:
                # 에러 발생 시에도 시간 기록
                duration = time.time() - start_time
                state["performance_metrics"][f"{node_name}_duration"] = duration
                state["performance_metrics"][f"{node_name}_status"] = "failed"
                state["performance_metrics"][f"{node_name}_error"] = str(e)
                
                logger.error(f"❌ {node_name} 실행 실패 ({duration:.2f}초): {e}")
                raise
                
        return wrapper
    return decorator


class SimpleTokenCallback:
    """간단한 토큰 추적 콜백"""
    
    def __init__(self, state: Dict):
        self.state = state
        # LangChain 콜백에서 요구하는 속성들
        self.raise_error = False
        self.ignore_llm = False
        self.ignore_chain = False
        self.ignore_agent = False
        self.ignore_retriever = False
        self.ignore_chat_model = False
        
        
    def on_llm_end(self, response, **kwargs):
        """LLM 응답에서 토큰 정보 추출"""
        try:
            # LLMResult에서 generation_info의 usage_metadata 추출
            if hasattr(response, 'generations') and response.generations:
                for generation_list in response.generations:
                    for generation in generation_list:
                        if hasattr(generation, 'generation_info') and generation.generation_info:
                            usage_metadata = generation.generation_info.get('usage_metadata', {})
                            if usage_metadata:
                                input_tokens = usage_metadata.get('prompt_token_count', 0)
                                output_tokens = usage_metadata.get('candidates_token_count', 0)
                                total_tokens = usage_metadata.get('total_token_count', input_tokens + output_tokens)
                                
                                logger.info(f"✅ 콜백으로 토큰 추출 성공")
                                logger.info(f"📊 입력: {input_tokens:,}, 출력: {output_tokens:,}, 총: {total_tokens:,}")
                                
                                # state에 토큰 정보 저장
                                if "token_usage" not in self.state:
                                    self.state["token_usage"] = {}
                                
                                self.state["token_usage"].update({
                                    "input_tokens": input_tokens,
                                    "output_tokens": output_tokens,
                                    "total_tokens": total_tokens
                                })
                                return  # 첫 번째 성공한 토큰 정보 사용
                                
        except Exception as e:
            logger.error(f"❌ 콜백 토큰 추출 실패: {e}")
    
    def on_chat_model_start(self, serialized, messages, **kwargs):
        """Chat 모델 시작 시 호출 (필수 메서드)"""
        pass






def generate_performance_report(state: Dict) -> Dict[str, Any]:
    """성능 리포트 생성 (비용 계산 포함) 및 state에 저장"""
    
    # 1. 비용 계산
    costs = {}
    
    # STT 비용 계산
    transcript = state.get("transcript", {})
    if transcript and "metadata" in transcript:
        audio_duration = transcript["metadata"].get("total_duration", 0)
        if audio_duration:
            costs["stt_usd"] = audio_duration * PRICING["assemblyai"]
            costs["stt_krw"] = costs["stt_usd"] * USD_TO_KRW
    
    # LLM 비용 계산 (20만 토큰 기준 분기)
    token_usage = state.get("token_usage", {})
    if token_usage:
        input_tokens = token_usage.get("input_tokens", 0)
        output_tokens = token_usage.get("output_tokens", 0)
        
        # 입력 토큰이 20만개 초과인지 확인
        if input_tokens > 200000:
            input_cost = input_tokens * PRICING["vertex_ai"]["input_large"]
            output_cost = output_tokens * PRICING["vertex_ai"]["output_large"]
        else:
            input_cost = input_tokens * PRICING["vertex_ai"]["input_small"]
            output_cost = output_tokens * PRICING["vertex_ai"]["output_small"]
        
        costs["llm_input_usd"] = input_cost
        costs["llm_output_usd"] = output_cost
        costs["llm_total_usd"] = input_cost + output_cost
        costs["llm_total_krw"] = costs["llm_total_usd"] * USD_TO_KRW
    
    # 총 비용
    total_usd = sum(v for k, v in costs.items() if k.endswith("_usd"))
    costs["total_usd"] = total_usd
    costs["total_krw"] = total_usd * USD_TO_KRW
    
    # state에 비용 저장
    state["costs"] = costs
    
    # 2. 노드별 상세 정보 수집
    performance_metrics = state.get("performance_metrics", {})
    
    # 모든 노드 정보 수집
    node_info = {}
    total_duration = 0
    
    # duration이 있는 노드들을 기준으로 정보 수집
    duration_keys = [k for k in performance_metrics.keys() if k.endswith("_duration")]
    
    for duration_key in duration_keys:
        node_name = duration_key.replace("_duration", "")
        duration = performance_metrics[duration_key]
        status = performance_metrics.get(f"{node_name}_status", "unknown")
        error = performance_metrics.get(f"{node_name}_error", None)
        
        # 노드별 상세 정보 구성
        node_detail = {
            "실행시간": f"{duration:.2f}초",
            "상태": status
        }
        
        # 에러가 있는 경우 추가
        if error:
            node_detail["에러"] = str(error)
        
        node_info[node_name] = node_detail
        total_duration += duration
    
    # 총 실행 시간 추가
    if node_info:
        node_info["전체"] = {
            "총_실행시간": f"{total_duration:.2f}초",
            "실행된_노드수": len(duration_keys),
            "성공한_노드수": len([k for k in duration_keys if performance_metrics.get(k.replace("_duration", "_status")) == "success"]),
            "실패한_노드수": len([k for k in duration_keys if performance_metrics.get(k.replace("_duration", "_status")) == "failed"])
        }
    
    # 3. 통합 리포트 구성
    report = {
        "timestamp": datetime.now().isoformat(),
        "파이프라인_상태": state.get("status", "unknown"),
        "노드별_상세정보": node_info
    }
    
    # 토큰 사용량 추가
    if token_usage:
        report["토큰_사용량"] = {
            "input": f"{token_usage.get('input_tokens', 0):,}",
            "output": f"{token_usage.get('output_tokens', 0):,}",
            "total": f"{token_usage.get('total_tokens', 0):,}"
        }
    
    # 비용 정보 추가
    if costs:
        cost_report = {}
        if "stt_usd" in costs:
            cost_report["stt"] = f"${costs['stt_usd']:.4f}"
        if "llm_total_usd" in costs:
            cost_report["llm"] = f"${costs['llm_total_usd']:.4f}"
        if "total_usd" in costs:
            cost_report["total_usd"] = f"${costs['total_usd']:.4f}"
            cost_report["total_krw"] = f"₩{costs['total_krw']:.0f}"
        
        if cost_report:
            report["비용_분석"] = cost_report
    
    # state에 리포트 저장
    state["performance_report"] = report
    
    logger.info(f"💰 총 비용: ${total_usd:.4f} (₩{costs.get('total_krw', 0):.0f})")
    logger.info(f"📈 성능 리포트 생성 완료")
    return report