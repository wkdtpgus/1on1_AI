import asyncio
import pprint
import os
from datetime import datetime

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.chains import generate_template
import logging
from src.utils.utils import save_questions_to_json

async def main():
    """
    템플릿 생성기 체인을 테스트하기 위한 메인 함수입니다.
    """
    # 간단한 로깅 기본 설정
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info("1on1 템플릿 생성을 시작합니다...")
    
    # --- 테스트할 입력 데이터를 여기에서 수정하세요 --- #
    sample_input = TemplateGeneratorInput(
        # 템플릿 필수정보
        user_id="user_003",
        purpose=['Junior Development', 'Growth'],
        detailed_context="신규 입사 후 3달차의 성장과 개선을 위한 논의를 진행하고 싶습니다. 어떤 점이 어려운지, 팀 내 관계는 어떠신지, 협업 현황과 성장욕구는 어떤지 알고 싶습니다. 특히 지난 프로젝트에서 표현이 다소 직설적이라는 피드백이 있었는데, 해당 건에 관하여 논의해보고 싶습니다.",
        dialogue_type='Recurring',

        # 템플릿 추가 커스텀
        use_previous_data=True,
        num_questions='Advanced', # Simple, Standard, Advanced
        question_composition=['Action/Implementation-focused', 'Growth/Goal-oriented', 'Relationship/Collaboration','Multiple choice'],
        tone_and_manner='Casual', # Formal or Casual

    )
    
    # ---------------------------------------------- #
    try:
        # 템플릿 생성 함수를 호출합니다.
        result = await generate_template(sample_input)

        logging.info("\n✨ 생성된 1on1 템플릿 결과 ✨")
        logging.info("="*50)
        
        # template_summary 출력 (사용자 요청에 따라 print 사용)
        print("\n📋 템플릿 구성 요약:")
        print(result.get('template_summary', '요약 정보 없음'))

        # 생성된 질문을 타임스탬프를 포함한 JSON 파일로 저장
        output_dir = "data/generated_templates"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join(output_dir, f"test_output_{timestamp}.json")

        save_questions_to_json(result.get('generated_questions', []), output_file_path)
        logging.info(f"\n✅ 질문이 '{output_file_path}' 파일에 성공적으로 저장되었습니다.")

    except Exception as e:
        logging.error(f"\n❌ 에러가 발생했습니다: {e}")
        logging.error(f"에러 타입: {type(e).__name__}")
        import traceback
        logging.error(f"상세 에러: {traceback.format_exc()}")
        logging.error("Google Cloud 인증 정보(.env 파일 등)가 올바르게 설정되었는지 확인해주세요.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
