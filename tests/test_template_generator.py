import os
import json
from datetime import datetime

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.generate_template import generate_template
from src.services.template_generator.generate_summary import generate_summary
from src.utils.utils import save_questions_to_json
import logging

async def main():
    """
    Main function to test the template generator chain.
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info("Starting 1-on-1 template generation...")

    # --- Modify the test input data here --- #
    sample_input = TemplateGeneratorInput(
        user_id="user_001",
        target_info="김수연, 프로덕트 디자인팀 팀장, 5년차",
        purpose=['Work', 'Relationships', 'Satisfaction'],
        detailed_context="프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
        dialogue_type='Recurring',
        use_previous_data=True,
        num_questions='Advanced',
        question_composition=['Action/Implementation-focused', 'Growth/Goal-oriented', 'Relationship/Collaboration', 'Experience/Story-based'],
        tone_and_manner='Casual',
        language='English'  # Set the language for generation
    )

    # ---------------------------------------------- #
    try:
        # 1. Concurrently call the summary and question generation APIs
        logging.info("\nStarting summary and question generation...")
        summary_result, questions_result = await asyncio.gather(
            generate_summary(sample_input),
            generate_template(sample_input)
        )

        # 2. Save each result to a separate JSON file
        output_dir = "data/generated_templates"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save the summary file
        summary_file_path = os.path.join(output_dir, f"summary_{timestamp}.json")
        with open(summary_file_path, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=4)
        logging.info(f"\n✅ Summary saved to '{summary_file_path}'.")

        # Save the questions file (using the save_questions_to_json utility)
        questions_file_path = os.path.join(output_dir, f"questions_{timestamp}.json")
        # Extract only the list of questions from the API result
        generated_questions = questions_result.get('generated_questions', [])
        save_questions_to_json(generated_questions, questions_file_path)
        logging.info(f"✅ Questions saved to '{questions_file_path}'.")

    except Exception as e:
        logging.error(f"\n❌ An error occurred: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        import traceback
        logging.error(f"Detailed error: {traceback.format_exc()}")
        logging.error("Please check if your Google Cloud authentication information (e.g., .env file) is set up correctly.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
