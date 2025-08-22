import json
from datetime import datetime

import httpx
import pytest
from dotenv import load_dotenv
from langsmith import traceable

from src.utils.mock_db import MOCK_USER_DATA
from src.utils.utils import save_to_json

# .env 파일 로드
load_dotenv()

# FastAPI 서버의 기본 URL (통합된 main.py 서버)
base_url = "http://127.0.0.1:8000/api/template"

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)
if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

# 초기 페이로드 (사용자 입력값)
initial_payload = {
    "user_id": user_data["user_id"],
    "target_info": user_data['name'],
    "purpose": "Growth, Work",
    "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
    "use_previous_data": False,
    "previous_summary": None,
    "num_questions": "Standard",
    "question_composition": "Growth/Goal-oriented, Reflection/Thought-provoking, Action/Implementation-focused",
    "tone_and_manner": "Casual",
    "language": "Korean",
    "include_guide": True,
}

headers = {
    'Content-Type': 'application/json'
}

@pytest.mark.asyncio
@traceable(run_type="chain", name="test_client_generation_flow")
async def test_client_generation_flow():
    """
    클라이언트 관점의 사용자 흐름(템플릿 생성 -> 가이드 생성 -> 이메일 생성)을 
    시뮬레이션하는 통합 테스트
    """
    print("\\n--- 클라이언트 통합 생성 흐름 테스트 시작 ---")
    
    # 클라이언트의 상태를 시뮬레이션하는 변수
    client_state = {
        "user_input": initial_payload,
        "generated_questions": None
    }

    async with httpx.AsyncClient() as client:
        # --- 1단계: 템플릿 생성 ---
        print("\\n[1단계] 템플릿 생성 요청")
        try:
            url = f"{base_url}?generation_type=template"
            response = await client.post(url, data=json.dumps(client_state["user_input"]), headers=headers, timeout=300)
            assert response.status_code == 200, "템플릿 생성 API 호출 실패"
            
            response_data = response.json()
            client_state["generated_questions"] = response_data.get("generated_questions")
            assert client_state["generated_questions"], "생성된 질문이 없습니다."
            
            # 📁 파일 저장: 통합된 save_to_json 함수 사용
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/questions_{timestamp}.json"
            save_to_json(client_state["generated_questions"], output_path)
            print(f"✅ 템플릿 생성 성공, 결과를 {output_path}에 저장 완료")

        except Exception as e:
            assert False, f"1단계 (템플릿 생성) 중 오류 발생: {e}"

        # --- 2단계: 활용 가이드 생성 ---
        print("\\n[2단계] 활용 가이드 생성 요청 (스트리밍)")
        try:
            url = f"{base_url}?generation_type=guide"
            
            # 가이드 생성에는 생성된 질문이 필요
            guide_payload = client_state["user_input"].copy()
            guide_payload["generated_questions"] = client_state["generated_questions"]
            
            raw_response_content = ""
            print("--- 스트리밍 시작 ---")
            async with client.stream("POST", url, data=json.dumps(guide_payload), headers=headers, timeout=300) as response:
                assert response.status_code == 200, "가이드 생성 API 호출 실패"
                
                async for chunk in response.aiter_text():
                    print(chunk, end="")  # 터미널에 스트리밍 출력
                    if chunk.startswith("data: "):
                        # "data: "와 개행문자 제거
                        data_part = chunk[6:].strip()
                        if data_part:
                            try:
                                # 각 청크는 JSON 문자열 조각이므로, 파싱하여 내부 문자열을 추출
                                content = json.loads(data_part)
                                raw_response_content += content
                            except json.JSONDecodeError:
                                print(f"\\nJSON 파싱 오류: {data_part}")

            print("\\n--- 스트리밍 종료 ---")
            assert raw_response_content, "스트리밍된 내용이 없습니다."
            
            # 전체 응답 문자열에서 마크다운 코드 블록 제거
            if raw_response_content.startswith("```json"):
                cleaned_json_str = raw_response_content[7:-3].strip()
            else:
                cleaned_json_str = raw_response_content

            guide_data = json.loads(cleaned_json_str)
            usage_guide = guide_data.get("usage_guide")
            assert usage_guide, "응답에 'usage_guide'가 없습니다."

            # 📁 파일 저장: 통합된 save_to_json 함수 사용
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/guide_{timestamp}.json"
            save_to_json(guide_data, output_path)
            print(f"\\n✅ 활용 가이드 생성 성공, 결과를 {output_path}에 저장 완료")

        except Exception as e:
            assert False, f"2단계 (가이드 생성) 중 오류 발생: {e}"
            
        # --- 3단계: 이메일 생성 ---
        print("\\n[3단계] 이메일 생성 요청")
        try:
            # 초기 사용자 입력값으로 이메일 생성 요청
            url = f"{base_url}?generation_type=email"
            response = await client.post(url, data=json.dumps(client_state["user_input"]), headers=headers, timeout=300)
            assert response.status_code == 200, "이메일 생성 API 호출 실패"

            response_data = response.json()
            generated_email = response_data.get("generated_email")
            assert generated_email, "생성된 이메일이 없습니다."

            # 📁 파일 저장: 통합된 save_to_json 함수 사용
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/email_{timestamp}.json"
            save_to_json(response_data, output_path)
            print(f"✅ 이메일 생성 성공, 결과를 {output_path}에 저장 완료")
            
        except Exception as e:
            assert False, f"3단계 (이메일 생성) 중 오류 발생: {e}"

    print("\\n--- 클라이언트 통합 생성 흐름 테스트 완료 ---")
