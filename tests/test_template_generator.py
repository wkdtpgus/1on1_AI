import asyncio
import asyncio
import os
import json
from datetime import datetime

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.generate_template import generate_template
from src.services.template_generator.generate_summary import generate_summary
import logging

async def main():
    """
    템플릿 생성기 체인을 테스트하기 위한 메인 함수입니다.
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info("1on1 템플릿 생성을 시작합니다...")

    # --- 테스트할 입력 데이터를 여기에서 수정하세요 --- #
    sample_input = TemplateGeneratorInput(
        user_id="user_002",
        purpose=['Work', 'Growth', 'Satisfaction'],
        detailed_context="어려움이나 문제가 있는지 위주로 묻고 싶습니다.",
        dialogue_type='Recurring',
        use_previous_data=True,
        num_questions='Advanced',
        question_composition=['Action/Implementation-focused', 'Growth/Goal-oriented', 'Multiple choice'],
        tone_and_manner='Formal',
    )

    # ---------------------------------------------- #
    try:
        # 1. 요약과 질문 생성 API 동시 호출
        logging.info("\n요약 및 질문 생성을 시작합니다...")
        summary_result, questions_result = await asyncio.gather(
            generate_summary(sample_input),
            generate_template(sample_input)
        )

        # 2. 각 결과를 별도의 JSON 파일로 저장
        output_dir = "data/generated_templates"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 요약 파일 저장
        summary_file_path = os.path.join(output_dir, f"summary_{timestamp}.json")
        with open(summary_file_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=4)
        logging.info(f"\n✅ 요약이 '{summary_file_path}' 파일에 저장되었습니다.")

        # 질문 파일 저장
        questions_file_path = os.path.join(output_dir, f"questions_{timestamp}.json")
        with open(questions_file_path, 'w', encoding='utf-8') as f:
            json.dump(questions_result, f, ensure_ascii=False, indent=4)
        logging.info(f"✅ 질문이 '{questions_file_path}' 파일에 저장되었습니다.")

    except Exception as e:
        logging.error(f"\n❌ 에러가 발생했습니다: {e}")
        logging.error(f"에러 타입: {type(e).__name__}")
        import traceback
        logging.error(f"상세 에러: {traceback.format_exc()}")
        logging.error("Google Cloud 인증 정보(.env 파일 등)가 올바르게 설정되었는지 확인해주세요.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
