import asyncio
import json
import os
from datetime import datetime
import pytest
from dotenv import load_dotenv
from src.utils.mock_db import MOCK_USER_DATA
from src.services.template_generator.generate_summary import generate_summary
from src.utils.template_schemas import TemplateGeneratorInput

# .env 파일 로드
load_dotenv()

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

def create_previous_summary_from_user_data(user_data: dict, use_previous_data: bool = True) -> str:
    """
    사용자 데이터에서 이전 미팅 기록을 추출하여 요약 형식으로 변환합니다.
    테스트 전용 함수입니다.

    Args:
        user_data (dict): 사용자 데이터 (one_on_one_history 포함)
        use_previous_data (bool): 이전 기록 사용 여부

    Returns:
        str: 포맷팅된 이전 미팅 요약 또는 빈 문자열
    """
    if not use_previous_data or not user_data.get("one_on_one_history"):
        return ""
    
    # 가장 최근 미팅 기록 가져오기
    latest_meeting = user_data["one_on_one_history"][-1]
    
    # summary 데이터를 프롬프트 형식으로 변환
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
    
    return (
        f"<Previous Conversation Summary>\n"
        f"- Date: {latest_meeting['date']}\n"
        f"- Summary Categories:\n"
        f"{chr(10).join(summary_sections)}"
    )

@pytest.mark.asyncio
async def test_summary_generation():
    """1on1 템플릿 요약 생성을 테스트하는 함수"""
    
    print("--- 1on1 템플릿 요약 생성 테스트 ---")
    
    # 테스트 시나리오 설정
    use_previous_data = True  # 테스트 시 이 값을 변경하여 동작 확인 가능
    
    # 테스트 파일 내 함수를 사용하여 이전 미팅 기록 생성
    previous_summary_data = create_previous_summary_from_user_data(user_data, use_previous_data)
    
    # TemplateGeneratorInput 생성
    input_data = TemplateGeneratorInput(
        user_id=user_data["user_id"],
        target_info=user_data['name'],
        purpose="Growth, Work",  # 문자열로 전달 (쉼표로 구분)
        detailed_context="보상 관련 논의예정",
        use_previous_data=use_previous_data,
        previous_summary=previous_summary_data,  
        num_questions="Standard",
        question_composition="Growth/Goal-oriented, Reflection/Thought-provoking",
        tone_and_manner="Formal",
        language="Korean"
    )
    
    try:
        # 요약 생성 실행
        print("요약 생성 중...")
        summary_result = await generate_summary(input_data)
        
        if summary_result:
            print("\n✅ 요약 생성 완료!")
            print(f"📊 생성된 요약: {summary_result.get('template_summary', 'N/A')}")
            
            # 파일에 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/summary_{timestamp}.json"
            
            # 디렉토리 생성
            os.makedirs("data/generated_templates", exist_ok=True)
            
            # JSON 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary_result, f, ensure_ascii=False, indent=4)
            
            print(f"💾 요약이 '{output_path}'에 저장되었습니다.")
            
            # 테스트 검증
            assert summary_result is not None, "요약 생성이 실패했습니다"
            assert isinstance(summary_result, dict), "요약 결과가 딕셔너리 형태가 아닙니다"
            
        else:
            print("\n⚠️ 요약 생성에 실패했습니다.")
            assert False, "요약 생성에 실패했습니다"
            
    except Exception as e:
        print(f"\n❌ 요약 생성 중 오류 발생: {e}")
        assert False, f"요약 생성 중 오류 발생: {e}"

# 메인 실행
if __name__ == "__main__":
    # asyncio 이벤트 루프에서 테스트 실행
    asyncio.run(test_summary_generation())
    print("\n✅ 테스트 완료!")
