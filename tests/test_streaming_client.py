import requests
import json
from src.utils.mock_db import MOCK_USER_DATA

# FastAPI 서버의 v2 스트리밍 엔드포인트 URL
url = "http://127.0.0.1:8000/generate"

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
            # 인코딩 설정
            # SSE (Server-Sent Events) 스트림을 실시간으로 처리
            print("--- 생성된 1on1 질문 목록 (스트리밍) ---")
            question_count = 1
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
                    except json.JSONDecodeError:
                        # 파싱에 실패한 경우, 원본 데이터를 출력하여 디버깅을 돕습니다.
                        print(f"JSON 파싱 오류: {json_data}")
            # 스트리밍이 모두 끝난 후 한 줄을 띄워줍니다.
            print("\n-------------------------------------") # Add a newline for cleaner terminal output after the stream.
        else:
            print(f"에러 발생: {response.status_code}")
            print(f"응답 내용: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"요청 중 에러 발생: {e}")
