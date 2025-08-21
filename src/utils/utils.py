import json
import os
from typing import Optional, Dict, Any
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


def save_questions_to_json(questions_data: Dict[str, str], file_path: str) -> Dict[str, str]:
    """
    번호가 매겨진 질문 딕셔너리를 JSON 파일에 그대로 저장합니다.

    Args:
        questions_data (Dict[str, str]): 저장할 질문 딕셔너리 (e.g., {"1": "...", "2": "..."})
        file_path (str): 저장할 JSON 파일 경로
    
    Returns:
        dict: 저장된 데이터 (입력과 동일)
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(questions_data, f, ensure_ascii=False, indent=4)
    return questions_data


def save_guide_to_json(guide_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    생성된 활용 가이드를 JSON 파일에 저장합니다.

    Args:
        guide_data (Dict[str, Any]): 저장할 가이드 딕셔너리 (e.g., {"usage_guide": "..."})
        file_path (str): 저장할 JSON 파일 경로
    
    Returns:
        dict: 저장된 데이터 (입력과 동일)
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(guide_data, f, ensure_ascii=False, indent=4)
    return guide_data


def save_email_to_json(email_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    생성된 이메일을 JSON 파일에 저장합니다.

    Args:
        email_data (Dict[str, Any]): 저장할 이메일 딕셔너리 (e.g., {"generated_email": "..."})
        file_path (str): 저장할 JSON 파일 경로
    
    Returns:
        dict: 저장된 데이터 (입력과 동일)
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(email_data, f, ensure_ascii=False, indent=4)
    return email_data
