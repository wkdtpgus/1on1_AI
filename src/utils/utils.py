import json
import os
import re
from typing import Optional, Dict, Any, List
from src.utils.mock_db import MOCK_USER_DATA

# Pre-process the mock data into a dictionary for faster lookups
_MOCK_USER_DATA_BY_ID = {user['user_id']: user for user in MOCK_USER_DATA}

def get_user_data_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    user_id를 사용하여 MOCK_USER_DATA에서 사용자 데이터를 찾습니다.
    사전 처리된 딕셔너리를 사용하여 빠른 검색을 수행합니다.
    """
    if not user_id:
        return None
    return _MOCK_USER_DATA_BY_ID.get(user_id)


def save_questions_to_json(questions: List[str], file_path: str):
    """
    질문 리스트를 번호가 키인 딕셔너리 형태로 JSON 파일에 저장합니다.

    Args:
        questions (List[str]): 저장할 질문 리스트
        file_path (str): 저장할 JSON 파일 경로
    
    Returns:
        dict: 저장된 데이터를 딕셔너리 형태로 반환 (즉시 사용 가능)
    """
    output_data = {str(i + 1): question for i, question in enumerate(questions)}

    # 디렉토리 생성
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    return output_data

def process_streaming_response(response_text: str) -> Optional[List[str]]:
    """
    스트리밍 응답에서 JSON을 추출하고 generated_questions를 반환합니다.

    Args:
        response_text (str): 스트리밍 응답 텍스트

    Returns:
        Optional[List[str]]: 추출된 질문 리스트 또는 None
    """
    try:
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            full_response = json.loads(json_str)
            return full_response.get('generated_questions', [])
        return None
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        return None

def collect_streaming_response(response) -> str:
    """
    SSE 스트리밍 응답을 수집하여 전체 텍스트를 반환합니다.

    Args:
        response: requests.Response 객체 (stream=True)

    Returns:
        str: 수집된 전체 응답 텍스트
    """
    full_response_str = ""
    
    for line in response.iter_lines(decode_unicode=True):
        # SSE 데이터는 "data: "로 시작합니다.
        if line.startswith('data: '):
            # "data: " 접두사를 제거하여 실제 JSON 데이터를 추출합니다.
            json_data = line[len('data: '):]
            try:
                # 서버에서 오는 데이터 조각(chunk)을 파싱합니다.
                content_chunk = json.loads(json_data)
                # 줄바꿈 없이 이어서 출력하여 타이핑 효과를 냅니다.
                print(content_chunk, end="", flush=True)
                
                # 전체 응답을 모으기
                full_response_str += str(content_chunk)
                
            except json.JSONDecodeError:
                # 파싱에 실패한 경우, 원본 데이터를 출력하여 디버깅을 돕습니다.
                print(f"JSON 파싱 오류: {json_data}")
    
    return full_response_str


def calculate_speaker_percentages(utterances) -> Dict[str, float]:
    
    speaker_stats_percent = {}
    if utterances:
        speaker_stats = {}
        total_duration_ms = 0
        
        # 화자별 발화 시간 계산
        for utterance in utterances:
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
    
    return speaker_stats_percent


def map_speaker_data(analysis_dict: Dict[str, Any], original_stats: Dict[str, float], 
                    original_utterances: List[Dict], participants_info: Dict[str, str]) -> Dict[str, Any]:
    # speaker_mapping을 사용해 speaker_stats_percent를 실제 이름으로 변환
    speaker_mapping_list = analysis_dict.pop("speaker_mapping", ["리더", "팀원"])
    
    # speaker_mapping_list와 participants를 비교해서 누가 리더인지 판단
    leader_name = participants_info.get("leader", "리더")
    
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
    mapped_utterances = []
    
    for utterance in original_utterances:
        mapped_utterance = utterance.copy()
        if utterance.get("speaker") == "A":
            mapped_utterance["speaker"] = speaker_mapping_list[0]
        elif utterance.get("speaker") == "B":
            mapped_utterance["speaker"] = speaker_mapping_list[1]
        mapped_utterances.append(mapped_utterance)
    
    analysis_dict["transcript"] = mapped_utterances
    
    return analysis_dict
