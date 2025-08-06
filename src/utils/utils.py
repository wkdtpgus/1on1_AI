import json
from src.utils.mock_db import MOCK_USER_DATA
from typing import Optional, Dict, Any, List

def get_user_data_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    user_id로 MOCK_USER_DATA에서 사용자 데이터를 찾습니다.
    """
    if not user_id:
        return None
    for user in MOCK_USER_DATA:
        if user.get("user_id") == user_id:
            return user
    return None

def get_user_data_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    이름으로 MOCK_USER_DATA에서 사용자 데이터를 찾습니다.
    """
    if not name:
        return None
    for user in MOCK_USER_DATA:
        if user.get("name") == name:
            return user
    return None


def save_questions_to_json(questions: List[str], file_path: str):
    """
    질문 리스트에 번호를 매겨 JSON 파일에 저장합니다.

    Args:
        questions (List[str]): 질문 목록.
        file_path (str): 저장할 JSON 파일 경로.
    """
    numbered_questions = [f"{i+1}. {question}" for i, question in enumerate(questions)]
    output_data = {
        "questions": numbered_questions
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
