import json
import os
from typing import Optional, Dict, Any, List
from src.utils.mock_db import MOCK_USER_DATA

# 빠른 확인이 가능하도록 딕셔너리형태로 가상데이터 전처리
_MOCK_USER_DATA_BY_ID = {user['user_id']: user for user in MOCK_USER_DATA}

def get_user_data_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    user_id를 사용하여 MOCK_USER_DATA에서 사용자 데이터를 찾습니다.
    사전 처리된 딕셔너리를 사용하여 빠른 검색을 수행합니다.
    """
    if not user_id:
        return None
    return _MOCK_USER_DATA_BY_ID.get(user_id)


def save_to_json(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    딕셔너리 데이터를 JSON 파일에 저장합니다.
    파일 경로에 디렉토리가 없으면 자동으로 생성합니다.

    Args:
        data (Dict[str, Any]): 저장할 딕셔너리 데이터
        file_path (str): 저장할 JSON 파일 경로

    Returns:
        dict: 저장된 데이터 (입력과 동일)
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return data

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

