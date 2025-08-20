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
