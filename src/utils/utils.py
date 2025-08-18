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
