import asyncio
import json
import os
from datetime import datetime
import pytest
from dotenv import load_dotenv
from src.utils.mock_db import MOCK_USER_DATA
from src.services.template_generator.generate_usage_guide import generate_usage_guide
from src.utils.template_schemas import UsageGuideInput

# .env 파일 로드
load_dotenv()

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")


# 모의 생성된 템플릿 데이터 (실제로는 generate_template의 결과)
MOCK_GENERATED_QUESTIONS = [
    {
        "question": "수연님, 요즘 퇴근 후나 주말에는 주로 어떻게 시간을 보내세요? 혹시 최근에 새롭게 시작한 취미나 흥미로운 활동이 있으신가요?",
        "intent": "관계 구축"
    },
    {
        "question": "최근 프로덕트 디자인 팀에서 진행했던 프로젝트 중에 수연님께서 가장 큰 보람을 느끼셨던 순간은 언제였을까요?",
        "intent": "성취감 회고"
    },
    {
        "question": "팀 내에서 동료들과 협업할 때, 수연님께서 가장 중요하게 생각하시는 부분은 무엇인가요?",
        "intent": "협업 방식"
    },
    {
        "question": "만약 팀 내에서 발생하고 있는 갈등 상황이 있다면, 가장 크게 영향을 미치고 있는 부분이 무엇이라고 보시나요?",
        "intent": "갈등 원인 분석"
    },
    {
        "question": "팀 내 갈등 상황을 해결하기 위해 수연님이 리더로서 시도해보고 싶은 방법이나 아이디어가 있다면 어떤 것들이 있을까요?",
        "intent": "갈등 해결 계획"
    },
    {
        "question": "수연님의 매니징 역량을 더욱 강화하기 위해 어떤 부분에 대한 지원이나 교육이 필요하다고 느끼시나요?",
        "intent": "매니징 역량 개발"
    },
    {
        "question": "앞으로 6개월에서 1년 안에 수연님이 개인적으로 성장하고 싶거나, 팀에 기여하고 싶은 새로운 목표가 있다면 어떤 것이 있을까요?",
        "intent": "개인 성장 목표"
    },
    {
        "question": "오늘 나눈 이야기 외에, 수연님께서 저에게 공유하고 싶거나 궁금한 점이 있으실까요?",
        "intent": "자유 의견"
    }
]


@pytest.mark.asyncio
async def test_usage_guide_generation():
    """1on1 템플릿 활용 가이드 생성을 테스트하는 함수"""
    
    print("--- 1on1 템플릿 활용 가이드 생성 테스트 ---")
    
    # UsageGuideInput 생성
    guide_input = UsageGuideInput(
        user_id=user_data["user_id"],
        target_info=user_data['name'],
        purpose="Growth, Work",
        detailed_context="프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
        generated_questions=MOCK_GENERATED_QUESTIONS,
        language="Korean"
    )
    
    try:
        # 활용 가이드 생성 실행
        print("활용 가이드 생성 중...")
        guide_result = await generate_usage_guide(guide_input)
        
        if guide_result:
            print("\n✅ 활용 가이드 생성 완료!")
            print(f"📋 시작 전략: {guide_result.get('opening_strategy', 'N/A')}")
            print(f"🎯 니즈 반영: {guide_result.get('needs_reflection', 'N/A')}")  
            print(f"🔄 흐름 관리: {guide_result.get('flow_management', 'N/A')}")
            
            # 파일에 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/usage_guide_{timestamp}.json"
            
            # 디렉토리 생성
            os.makedirs("data/generated_templates", exist_ok=True)
            
            # 전체 결과를 JSON 파일로 저장 (입력 데이터 + 가이드 결과)
            full_result = {
                "input": guide_input.dict(),
                "guide": guide_result
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_result, f, ensure_ascii=False, indent=4)
            
            print(f"💾 활용 가이드가 '{output_path}'에 저장되었습니다.")
            
            # 테스트 검증
            assert guide_result is not None, "가이드 생성을 실패했습니다."
            assert "opening_strategy" in guide_result, "결과에 'opening_strategy' 필드가 없습니다."
            assert "needs_reflection" in guide_result, "결과에 'needs_reflection' 필드가 없습니다."
            assert "flow_management" in guide_result, "결과에 'flow_management' 필드가 없습니다."
            assert isinstance(guide_result["opening_strategy"], str) and guide_result["opening_strategy"], "'opening_strategy'가 비어있습니다."

        else:
            print("\n⚠️ 활용 가이드 생성에 실패했습니다.")
            assert False, "활용 가이드 생성에 실패했습니다."
            
    except Exception as e:
        print(f"\n❌ 활용 가이드 생성 중 오류 발생: {e}")
        assert False, f"활용 가이드 생성 중 오류 발생: {e}"


# 메인 실행 블록은 pytest 실행 시에는 필요하지 않으므로, 직접 실행할 때의 디버깅 용도로 남겨둡니다.
if __name__ == "__main__":
    asyncio.run(test_usage_guide_generation())