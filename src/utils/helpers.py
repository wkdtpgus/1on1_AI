from src.utils.mock_db import MOCK_USER_DATA
from typing import Optional, Dict, Any

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
