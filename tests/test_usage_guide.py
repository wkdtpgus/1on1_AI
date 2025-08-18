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

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

# /generate_template API가 반환할 것으로 예상되는 목업 데이터
# 실제 API의 출력 형식인 Dict[str, str]과 일치해야 함
MOCK_GENERATED_QUESTIONS = {
    "1": "수연님, 요즘 퇴근 후나 주말에는 주로 어떻게 시간을 보내세요? 혹시 최근에 새롭게 시작한 취미나 흥미로운 활동이 있으신가요?",
    "2": "최근 프로덕트 디자인 팀에서 진행했던 프로젝트 중에 수연님께서 가장 큰 보람을 느끼셨던 순간은 언제였을까요?",
    "3": "팀 내에서 동료들과 협업할 때, 수연님께서 가장 중요하게 생각하시는 부분은 무엇인가요?",
    "4": "만약 팀 내에서 발생하고 있는 갈등 상황이 있다면, 가장 크게 영향을 미치고 있는 부분이 무엇이라고 보시나요?",
    "5": "팀 내 갈등 상황을 해결하기 위해 수연님이 리더로서 시도해보고 싶은 방법이나 아이디어가 있다면 어떤 것들이 있을까요?",
    "6": "수연님의 매니징 역량을 더욱 강화하기 위해 어떤 부분에 대한 지원이나 교육이 필요하다고 느끼시나요?",
    "7": "앞으로 6개월에서 1년 안에 수연님이 개인적으로 성장하고 싶거나, 팀에 기여하고 싶은 새로운 목표가 있다면 어떤 것이 있을까요?",
    "8": "오늘 나눈 이야기 외에, 수연님께서 저에게 공유하고 싶거나 궁금한 점이 있으실까요?"
}


@pytest.mark.asyncio
async def test_usage_guide_generation():
    """1on1 템플릿 활용 가이드 생성을 테스트하는 함수"""

    print("--- 1on1 템플릿 활용 가이드 생성 테스트 ---")

    guide_input = UsageGuideInput(
        user_id=user_data["user_id"],
        target_info=user_data['name'],
        purpose="Growth, Work",
        detailed_context="프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
        generated_questions=MOCK_GENERATED_QUESTIONS,
        language="Korean"
    )

    try:
        print("활용 가이드 생성 중 (스트리밍)...")
        
        guide_stream = generate_usage_guide(guide_input)
        
        # 스트리밍 청크를 하나의 긴 문자열로 합침
        full_response_content = ""
        async for chunk in guide_stream:
            if chunk.startswith('data: '):
                content_str = chunk[len('data: '):].strip()
                try:
                    unquoted_content = json.loads(content_str)
                    # 실시간 출력을 위해 print 구문 추가
                    print(unquoted_content, end="", flush=True)
                    full_response_content += unquoted_content
                except json.JSONDecodeError:
                    pass
        
        print("\n-------------------------------------")

        # process_streaming_response 유틸리티 함수를 사용하여 JSON 추출
        guide_result = process_streaming_response(full_response_content)

        if guide_result:
            print("\n✅ 활용 가이드 생성 완료!")
            
            # 테스트 검증
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