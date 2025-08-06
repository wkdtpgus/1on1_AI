import asyncio
import pprint
import os
from datetime import datetime

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.chains import generate_template
from src.utils.utils import save_questions_to_json

async def main():
    """
    템플릿 생성기 체인을 테스트하기 위한 메인 함수입니다.
    """
    print("1on1 템플릿 생성을 시작합니다...")
    
    # --- 테스트할 입력 데이터를 여기에서 수정하세요 --- #
    sample_input = TemplateGeneratorInput(
        # 템플릿 필수정보
        user_id="user_001",
        purpose=['Satisfaction', 'Growth'],
        detailed_context="지난 액션아이템 전반에 관한 논의를 진행하고 싶습니다.",
        dialogue_type='Recurring',

        # 템플릿 추가 커스텀
        use_previous_data=True,
        num_questions='Advanced', # Simple, Standard, Advanced
        question_composition=['Action/Implementation-focused', 'Growth/Goal-oriented'],
        tone_and_manner='Formal', # Formal or Casual

    )
    
    # ---------------------------------------------- #
    try:
        # 템플릿 생성 함수를 호출합니다.
        result = await generate_template(sample_input)
        
        print("\n✨ 생성된 1on1 템플릿 결과 ✨")
        print("="*50)
        
        # template_summary 출력
        print("\n📋 템플릿 구성 요약:")
        print(result.get('template_summary', '요약 정보 없음'))

        # 생성된 질문을 타임스탬프를 포함한 JSON 파일로 저장
        output_dir = "data/generated_templates"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join(output_dir, f"test_output_{timestamp}.json")

        save_questions_to_json(result.get('generated_questions', []), output_file_path)
        print(f"\n✅ 질문이 '{output_file_path}' 파일에 성공적으로 저장되었습니다.")

    except Exception as e:
        print(f"\n❌ 에러가 발생했습니다: {e}")
        print(f"에러 타입: {type(e).__name__}")
        import traceback
        print(f"상세 에러: {traceback.format_exc()}")
        print("Google Cloud 인증 정보(.env 파일 등)가 올바르게 설정되었는지 확인해주세요.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
