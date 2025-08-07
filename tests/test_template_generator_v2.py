import asyncio
import os
from datetime import datetime

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.chains import generate_template
import logging
from src.utils.utils import save_questions_to_json
from src.config.config import GEMINI_MODEL, GPT_MODEL, CLAUDE_MODEL

async def main():
    """
    템플릿 생성기 체인을 테스트하기 위한 메인 함수입니다.
    v2: 테스트할 모델을 선택할 수 있습니다.
    """
    # 간단한 로깅 기본 설정
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # --- 테스트할 모델을 여기서 선택하세요 --- #
    # model_to_test = GPT_MODEL
    # model_to_test = CLAUDE_MODEL
    model_to_test = GEMINI_MODEL  # 기본값
    # ------------------------------------ #

    logging.info(f"[{model_to_test}] 모델로 1on1 템플릿 생성을 시작합니다...")
    
    # --- 테스트할 입력 데이터를 여기에서 수정하세요 --- #
    sample_input = TemplateGeneratorInput(
        # 템플릿 필수정보
        user_id="user_001",
        purpose=['Work','Growth','Satisfaction','Relationships','Junior Development'],
        detailed_context="보상이 만족스럽지않아 이직을 고민중이라고 함. 최근 심한 논쟁이 있었음. 하지만 핵심인재라 잡아야 함.",
        dialogue_type='New',

        # 템플릿 추가 커스텀
        use_previous_data=False,
        num_questions='Advanced', # Simple, Standard, Advanced
        question_composition=['Action/Implementation-focused', 'Growth/Goal-oriented', 'Relationship/Collaboration','Multiple choice'],
        tone_and_manner='Formal', # Formal or Casual
    )
    
    # ---------------------------------------------- #
    try:
        # 템플릿 생성 함수를 호출합니다. (model_name 추가)
        result = await generate_template(sample_input, model_name=model_to_test)

        logging.info("\n✨ 생성된 1on1 템플릿 결과 ✨")
        logging.info("="*50)
        
        # template_summary 출력 (사용자 요청에 따라 print 사용)
        print("\n📋 템플릿 구성 요약:")
        print(result.get('template_summary', '요약 정보 없음'))

        # 생성된 질문을 타임스탬프를 포함한 JSON 파일로 저장
        output_dir = "data/generated_templates"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join(output_dir, f"test_output_{model_to_test.replace('/', '_')}_{timestamp}.json")

        save_questions_to_json(result.get('generated_questions', []), output_file_path)
        logging.info(f"\n✅ 질문이 '{output_file_path}' 파일에 성공적으로 저장되었습니다.")

    except Exception as e:
        logging.error(f"\n❌ 에러가 발생했습니다: {e}")
        logging.error(f"에러 타입: {type(e).__name__}")
        import traceback
        logging.error(f"상세 에러: {traceback.format_exc()}")
        logging.error("API 키 및 Google Cloud 인증 정보(.env 파일 등)가 올바르게 설정되었는지 확인해주세요.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
