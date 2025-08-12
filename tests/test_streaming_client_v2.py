import requests
import json

# FastAPI 서버의 v2 스트리밍 엔드포인트 URL
url = "http://127.0.0.1:8002/templates/generate-streaming-v2"

# 요청에 포함할 데이터 (TemplateGeneratorInput 스키마에 맞춰서)
payload = {
    "user_id": "shjang",
    "target_info": "장서현, Data anaylst, Growth-Squad",
    "purpose": ["Growth", "Work"],
    "detailed_context": "최근 데이터 분석 업무에 어려움을 느끼고 있어, 함께 해결 방안을 논의하고 싶습니다.",
    "dialogue_type": "Recurring",
    "use_previous_data": True,
    "num_questions": "Standard",
    "question_composition": ["Growth/Goal-oriented", "Reflection/Thought-provoking", "Action/Implementation-focused"],
    "tone_and_manner": "친근하고 부드럽게",
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
