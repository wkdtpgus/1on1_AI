import json
from src.utils.mock_db import MOCK_USER_DATA
from typing import Optional, Dict, Any, List

# Pre-process the mock data into a dictionary for faster lookups
_MOCK_USER_DATA_BY_ID = {user['user_id']: user for user in MOCK_USER_DATA}

def get_user_data_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Finds user data in MOCK_USER_DATA by user_id using a pre-processed dictionary.
    """
    if not user_id:
        return None
    return _MOCK_USER_DATA_BY_ID.get(user_id)

def get_user_data_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Finds user data in MOCK_USER_DATA by name.
    """
    if not name:
        return None
    for user in MOCK_USER_DATA:
        if user.get("name") == name:
            return user
    return None


def save_questions_to_json(questions: List[str], file_path: str):
    """
    Saves a list of questions to a JSON file as a numbered dictionary.

    Args:
        questions (List[str]): A list of questions.
        file_path (str): The path to the JSON file to be saved.
    """
    output_data = {str(i + 1): question for i, question in enumerate(questions)}

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
