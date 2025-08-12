import requests
import json
from src.utils.mock_db import MOCK_USER_DATA

# FastAPI 서버의 v2 스트리밍 엔드포인트 URL
url = "http://127.0.0.1:8002/templates/generate-streaming-v2"

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

# 요청에 포함할 데이터 (TemplateGeneratorInput 스키마에 맞춰서)
payload = {
    "user_id": user_data["user_id"],
    "target_info": user_data['name'],
    "purpose": ["Growth", "Work"], # Enum에 맞는 값으로 설정
    "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
    "dialogue_type": "Recurring", # Enum에 맞는 값으로 설정
    "use_previous_data": True,
    "num_questions": "Standard", # Enum에 맞는 값으로 설정
    "question_composition": ["Growth/Goal-oriented", "Reflection/Thought-provoking", "Action/Implementation-focused"], # Enum에 맞는 값으로 설정
    "tone_and_manner": "Casual",
    "language": "Korean"
}

headers = {
    'Content-Type': 'application/json'
}

try:
    # 스트리밍 요청 보내기
    with requests.post(url, data=json.dumps(payload), headers=headers, stream=True, timeout=300) as response:
        # 응답 상태 코드 확인
        if response.status_code == 200:
            print("--- 스트리밍 시작 ---")
            # 인코딩 설정
            response.encoding = 'utf-8'
            # 청크 단위로 응답 내용 출력
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    print(chunk, end='', flush=True)
            print("\n--- 스트리밍 종료 ---")
        else:
            print(f"에러 발생: {response.status_code}")
            print(f"응답 내용: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"요청 중 에러 발생: {e}")
