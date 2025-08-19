import asyncio
import json
import os
from datetime import datetime
import pytest
from dotenv import load_dotenv
from src.utils.mock_db import MOCK_USER_DATA
from src.utils.template_schemas import UsageGuideInput
from src.services.template_generator.generate_usage_guide import generate_usage_guide
from src.utils.utils import process_streaming_response

# .env 파일 로드
load_dotenv()

# 테스트할 사용자 ID 설정
USER_ID_TO_TEST = "user_010"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

# /generate_template API가 반환할 것으로 예상되는 목업 데이터
# 시나리오: 신임 팀장의 역할 전환 지원 및 리더십 개발
MOCK_GENERATED_QUESTIONS = {
    "1": "요한님, 팀장이 되신 지 한 달 정도 지났는데, 실무자일 때와 비교해서 가장 크게 달라진 점은 무엇이라고 느끼시나요?",
    "2": "팀원일 때와는 다른, 팀장으로서 느끼는 가장 큰 어려움이나 고민은 무엇인가요?",
    "3": "과거에 동료였던 팀원들에게 업무를 위임하거나 피드백을 주는 것이 어색하거나 어렵게 느껴질 때가 있으신가요?",
    "4": "요한님께서 생각하시는 '좋은 팀'이란 어떤 모습인가요? 그리고 그 모습을 만들기 위해 팀장으로서 가장 먼저 시도해보고 싶은 것은 무엇인가요?",
    "5": "팀원들의 동기 부여를 위해 어떤 방법들을 고민하고 계신가요?",
    "6": "만약 '실무는 잠시 잊고 팀장 역할에만 집중하세요'라는 미션이 주어진다면, 가장 먼저 무엇을 해보고 싶으세요?",
    "7": "요한님께서 성공적인 팀장으로 자리 잡는 데 가장 필요하다고 생각하는 지원은 무엇인가요? (예: 리더십 코칭, 다른 팀장과의 교류 등)",
    "8": "오늘 나눈 이야기 외에, 팀장으로서의 역할이나 팀 운영에 대해 더 이야기하고 싶은 부분이 있으신가요?"
}


@pytest.mark.asyncio
async def test_usage_guide_generation():
    """1on1 템플릿 활용 가이드 생성을 테스트하는 함수"""

    print("--- 1on1 템플릿 활용 가이드 생성 테스트 ---")

    guide_input = UsageGuideInput(
        user_id=user_data["user_id"],
        target_info=user_data['name'],
        purpose="Role Transition Support, Leadership Development",
        detailed_context="최근 영업팀장으로 승진했으나, 실무자 역할에서 벗어나지 못하고 있음. 특히, 과거 동료였던 팀원들에게 업무를 위임하는 데 어려움을 느끼고, 팀 동기 부여 방안에 대해 고민이 많음. 새로운 역할에 성공적으로 적응하도록 돕고자 함.",
        generated_questions=MOCK_GENERATED_QUESTIONS,
        language="Korean"
    )

    try:
        print("활용 가이드 생성 중 (스트리밍)...")
        
        guide_stream = generate_usage_guide(guide_input)
        
        full_response_content = ""
        async for chunk in guide_stream:
            if chunk.startswith('data: '):
                content_str = chunk[len('data: '):].strip()
                try:
                    unquoted_content = json.loads(content_str)
                    print(unquoted_content, end="", flush=True)
                    full_response_content += unquoted_content
                except json.JSONDecodeError:
                    pass
        
        print("\n-------------------------------------")

        guide_result = process_streaming_response(full_response_content)

        if guide_result:
            print("\n✅ 활용 가이드 생성 완료!")
            print(f"📋 시작 전략: {guide_result.get('opening_strategy', 'N/A')}")
            print(f"🎯 니즈 반영 및 코칭: {guide_result.get('needs_reflection', 'N/A')}")
            print(f"🔄 흐름 관리: {guide_result.get('flow_management', 'N/A')}")
            
            assert guide_result is not None, "가이드 생성을 실패했습니다."
            assert "opening_strategy" in guide_result, "결과에 'opening_strategy' 필드가 없습니다."
            assert "needs_reflection" in guide_result, "결과에 'needs_reflection' 필드가 없습니다."
            assert "flow_management" in guide_result, "결과에 'flow_management' 필드가 없습니다."

        else:
            print("\n⚠️ 활용 가이드 생성에 실패했습니다.")
            assert False, "활용 가이드 생성에 실패했습니다."

    except Exception as e:
        print(f"\n❌ 활용 가이드 생성 중 오류 발생: {e}")
        assert False, f"활용 가이드 생성 중 오류 발생: {e}"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_usage_guide_generation())