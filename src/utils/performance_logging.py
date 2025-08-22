import time
import logging
from typing import Dict, Any, Callable
from functools import wraps
from datetime import datetime

logger = logging.getLogger("performance_logging")

def time_node_execution(node_name: str):
    """노드 실행 시간 측정 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            # state에서 performance_metrics 가져오기 또는 생성
            if "performance_metrics" not in state or state["performance_metrics"] is None:
                state["performance_metrics"] = {}
                
            start_time = time.time()
            
            try:
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

def generate_performance_report(state: Dict) -> Dict[str, Any]:
    """성능 리포트 생성 (시간 추적만) 및 state에 저장"""
    
    # 노드별 상세 정보 수집
    performance_metrics = state.get("performance_metrics", {})
    
    node_info = {}
    total_duration = 0
    
    # duration이 있는 노드들을 기준으로 정보 수집
    duration_keys = [k for k in performance_metrics.keys() if k.endswith("_duration")]
    
    for duration_key in duration_keys:
        node_name = duration_key.replace("_duration", "")
        duration = performance_metrics[duration_key]
        status = performance_metrics.get(f"{node_name}_status", "unknown")
        error = performance_metrics.get(f"{node_name}_error", None)
        
        node_detail = {
            "실행시간": f"{duration:.2f}초",
            "상태": status
        }
        
        if error:
            node_detail["에러"] = str(error)
        
        node_info[node_name] = node_detail
        total_duration += duration
    
    if node_info:
        node_info["전체"] = {
            "총_실행시간": f"{total_duration:.2f}초",
            "실행된_노드수": len(duration_keys),
            "성공한_노드수": len([k for k in duration_keys if performance_metrics.get(k.replace("_duration", "_status")) == "success"]),
            "실패한_노드수": len([k for k in duration_keys if performance_metrics.get(k.replace("_duration", "_status")) == "failed"])
        }
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "파이프라인_상태": state.get("status", "unknown"),
        "노드별_상세정보": node_info
    }
    
    state["performance_report"] = report
    
    logger.info(f"파이프라인 상태: {report.get('파이프라인_상태', 'unknown')}")
    
    node_details = report.get('노드별_상세정보', {})
    for node_name, details in node_details.items():
        if node_name == "전체":
            logger.info(f"[{node_name}] {details.get('총_실행시간', 'N/A')}, 성공: {details.get('성공한_노드수', 0)}/{details.get('실행된_노드수', 0)} 노드")
        else:
            status_emoji = "✅" if details.get('상태') == 'success' else "❌" if details.get('상태') == 'failed' else "⚠️"
            error_info = f", 에러: {details.get('에러', '')}" if details.get('에러') else ""
            
            logger.info(f"{status_emoji} [{node_name}] {details.get('실행시간', 'N/A')}, 상태: {details.get('상태', 'unknown')}{error_info}")
    
    logger.info(f"성능 리포트 생성 완료")
    return report