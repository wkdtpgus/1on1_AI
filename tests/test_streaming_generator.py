import asyncio
import os
import json
from datetime import datetime
import logging

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.generate_template_streaming import generate_template_streaming
from src.utils.utils import save_questions_to_json

async def main():
    """
    Main function to test the template generator chain with streaming.
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info("Starting 1-on-1 template generation (Streaming Test)...")

    # --- Modify the test input data here --- #
    sample_input = TemplateGeneratorInput(
        user_id="user_002",
        target_info="박준호, 데이터 엔지니어팀, 2년차 주니어",
        purpose=['Work', 'Growth', 'Satisfaction'],
        detailed_context="팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
        dialogue_type='Recurring',
        use_previous_data=True,
        num_questions='Advanced',
        question_composition=['Action/Implementation-focused', 'Growth/Goal-oriented', 'Multiple choice'],
        tone_and_manner='Casual',
        language='English'
    )
    # ---------------------------------------------- #

    try:
        logging.info("\n--- Live Streaming Output ---")
        full_response_str = ""
        # Call the streaming function and iterate through the chunks
        async for chunk in generate_template_streaming(sample_input):
            print(chunk, end="", flush=True)
            full_response_str += chunk
        
        print("\n\n--- End of Stream ---")

        # Once streaming is complete, parse the full JSON string
        try:
            # The model might not return a perfect JSON, so we clean it up a bit
            clean_json_str = full_response_str.strip().replace("```json", "").replace("```", "").strip()
            full_response = json.loads(clean_json_str)
            generated_questions = full_response.get('generated_questions', [])
        except json.JSONDecodeError:
            logging.warning("\nCould not decode JSON from the streamed response.")
            logging.info(f"Raw response: {full_response_str}")
            generated_questions = []

        if generated_questions:
            # Save the generated questions using the utility function
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/questions_streamed_{timestamp}.json"
            save_questions_to_json(generated_questions, output_path)
            logging.info(f"\n✅ Questions saved to '{output_path}'.")
        else:
            logging.warning("\nNo questions were generated or the stream was empty/invalid.")

    except Exception as e:
        logging.error(f"\n❌ An error occurred: {e}")
        import traceback
        logging.error(f"Detailed error: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
