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
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

# /generate_template API가 반환할 것으로 예상되는 목업 데이터
# 시나리오: 팀 내 갈등 중재 및 매니징 역량 강화
MOCK_GENERATED_QUESTIONS = {
    "1": "수연님, 최근 여가 시간에는 주로 어떤 활동을 하시면서 에너지를 얻으시나요?",
    "2": "최근 팀 프로젝트를 진행하면서 가장 큰 보람을 느끼셨던 순간은 언제였나요? 어떤 점에서 특히 만족스러우셨어요?",
    "3": "반대로, 프로젝트나 팀원들과의 협업 과정에서 '이 부분은 조금 아쉽다'거나 개선되었으면 하는 점이 있었다면 어떤 것이었나요?",
    "4": "팀 내에서 의견 충돌이나 갈등 상황이 발생했을 때, 수연님은 주로 어떤 방식으로 해결하려고 노력하시는 편인가요?",
    "5": "만약 팀원 중 한 명이 수연님의 의견에 지속적으로 반대하거나 비판적인 태도를 보인다면, 어떻게 소통하고 관계를 개선해 나가실 것 같으세요?",
    "6": "수연님께서 생각하시는 '좋은 팀장' 또는 '좋은 리더'는 어떤 모습인가요? 현재 수연님의 리더십 스타일에서 더 발전시키고 싶은 부분이 있다면 무엇일까요?",
    "7": "앞으로 팀을 이끌어 나가면서 가장 도전적인 과제는 무엇이라고 생각하시나요? 그 과제를 해결하기 위해 어떤 준비나 지원이 필요하다고 느끼세요?",
    "8": "오늘 나눈 이야기 외에, 팀 운영이나 개인의 성장에 대해 더 논의하고 싶거나 제게 바라는 점이 있다면 편하게 말씀해주세요."
}


@pytest.mark.asyncio
async def test_usage_guide_generation():
    """1on1 템플릿 활용 가이드 생성을 테스트하는 함수"""

    print("--- 1on1 템플릿 활용 가이드 생성 테스트 ---")

    guide_input = UsageGuideInput(
        user_id=user_data["user_id"],
        target_info=user_data['name'],
        purpose="Conflict Management, Leadership Development",
        detailed_context="최근 팀 내 의견 충돌이 잦아지고 있으며, 팀의 리더인 김수연님은 이 상황을 원만하게 해결하고 자신의 매니징 역량을 강화하고자 함. 팀원들의 동기 부여와 심리적 안정감을 높이는 것이 주요 목표.",
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