# 1. 표준 라이브러리
import json
import os
from datetime import datetime
import asyncio

# 2. 서드파티 라이브러리
import httpx
from dotenv import load_dotenv
from langsmith import traceable
import pytest

# 3. 내부 모듈
from src.utils.mock_db import MOCK_USER_DATA
from src.utils.utils import save_questions_to_json

# .env 파일 로드
load_dotenv()

# FastAPI 서버의 v2 엔드포인트 URL
url = "http://127.0.0.1:8000/generate_template"

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

def create_previous_summary_from_mock_db(user_data, use_previous_data: bool = True):
    """mock_db의 실제 데이터를 사용하여 이전 미팅 기록 생성"""
    if not use_previous_data or not user_data.get("one_on_one_history"):
        return ""
    
    latest_meeting = user_data["one_on_one_history"][-1]
    
    summary_sections = []
    for category, items in latest_meeting["summary"].items():
        done_items = items.get("Done", [])
        todo_items = items.get("ToDo", [])
        
        section = (
            f"  - {category}:\n"
            f"    Done: {', '.join(done_items) if done_items else 'None'}\n"
            f"    ToDo: {', '.join(todo_items) if todo_items else 'None'}"
        )
        summary_sections.append(section)
    
    summary_text = "<Previous Conversation Summary>\n"
    summary_text += f"- Date: {latest_meeting['date']}\n"
    summary_text += "- Summary Categories:\n"
    summary_text += "\n".join(summary_sections)
    
    return summary_text

# use_previous_data 설정에 따라 이전 미팅 기록 동적 생성
use_previous_data = False  # 테스트 시 이 값을 변경하여 동작 확인 가능
if use_previous_data:
    previous_summary_data = create_previous_summary_from_mock_db(user_data, use_previous_data=True)
else:
    previous_summary_data = None

# 모든 데이터를 문자열로 전처리
purpose_str = "Growth, Work"  # 직접 문자열로 정의
question_composition_str = "Growth/Goal-oriented, Reflection/Thought-provoking, Action/Implementation-focused"  # 직접 문자열로 정의

payload = {
    "user_id": user_data["user_id"], #필수
    "target_info": user_data['name'], #필수
    "purpose": purpose_str,  # 필수, 문자열로 전처리 완료
    "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
    "use_previous_data": use_previous_data,  # 프론트엔드에서 사용자 선택값
    "previous_summary": previous_summary_data,  # 조건에 따라 동적 설정
    "num_questions": "Standard", # Enum에 맞는 값으로 설정
    "question_composition": question_composition_str,  # 문자열로 전처리 완료
    "tone_and_manner": "Casual",
    "language": "Korean",
    "include_guide": True, # 가이드 포함 테스트
}

headers = {
    'Content-Type': 'application/json'
}

@pytest.mark.asyncio
@traceable(run_type="chain", name="test_template_generator")
async def test_api_call():
    """API 테스트를 위한 비동기 함수"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=json.dumps(payload), headers=headers, timeout=300)
            
            if response.status_code == 200:
                print("--- API 응답 ---")
                response_data = response.json()
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                generated_questions = response_data.get("generated_questions")
                usage_guide_data = response_data.get("usage_guide")

                assert generated_questions, "생성된 질문이 없습니다."
                assert isinstance(generated_questions, dict), "질문이 딕셔너리 형태가 아닙니다."
                
                if payload["include_guide"]:
                    assert usage_guide_data, "활용 가이드가 생성되지 않았습니다."
                    assert isinstance(usage_guide_data, dict), "가이드가 딕셔너리 형태가 아닙니다."
                    assert "usage_guide" in usage_guide_data, "가이드 데이터에 'usage_guide' 키가 없습니다."
                    
                    # 실제 가이드 텍스트 내용 검증
                    usage_guide_text = usage_guide_data["usage_guide"]
                    assert isinstance(usage_guide_text, str), "가이드 내용이 문자열이 아닙니다."

                # 파일 저장 로직은 필요시 유지
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"data/generated_templates/questions_{timestamp}.json"
                save_questions_to_json(generated_questions, output_path)
                print(f"\n--- 질문 저장 완료: {output_path} ---")

            else:
                print(f"에러 발생: {response.status_code}")
                print(f"응답 내용: {response.text}")
                assert False, f"API returned status code {response.status_code}"

        except httpx.RequestError as e:
            print(f"요청 중 에러 발생: {e}")
            assert False, f"Request failed: {e}"
