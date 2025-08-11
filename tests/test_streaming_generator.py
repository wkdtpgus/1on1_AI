import asyncio
import os
import json
from datetime import datetime
import logging

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.generate_template import generate_template
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
        # Call the original function to get the full result at once
        full_response = await generate_template(sample_input)

        generated_questions = full_response.get('generated_questions', [])
        
        if generated_questions:
            # Simulate streaming by printing the result character by character
            print("\n--- Simulating Streaming Output ---")
            # Simulate streaming by printing each numbered question character by character
            for i, question in enumerate(generated_questions):
                numbered_question = f"{i + 1}. {question}\n"
                for char in numbered_question:
                    print(char, end="", flush=True)
                    await asyncio.sleep(0.02)  # Adjust delay for desired speed
            print("\n--- End of Simulation ---")

            # Save the generated questions using the utility function
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/generated_templates/questions_simulated_stream_{timestamp}.json"
            save_questions_to_json(generated_questions, output_path)
            logging.info(f"\n✅ Questions saved to '{output_path}'.")
        else:
            logging.warning("\nNo questions were generated or stream was empty.")

    except Exception as e:
        logging.error(f"\n❌ An error occurred: {e}")
        import traceback
        logging.error(f"Detailed error: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
