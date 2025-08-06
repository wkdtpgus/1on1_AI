import asyncio
import pprint

from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.chains import generate_template

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
        detailed_context="최근 연봉 협상 과정에서 팀원과 의견 차이가 있었습니다. 회사 전체의 보상 테이블 기준을 설명했지만, 팀원은 본인의 기여도에 비해 보상이 부족하다고 느끼는 것 같습니다. 이로 인해 전반적인 업무 만족도나 동기 부여에 영향이 있을까 우려됩니다. 단순히 보상 문제를 넘어, 팀원의 기여를 어떻게 인정하고 있는지, 앞으로의 성장 가능성은 어떻게 보고 있는지에 대해 깊이 있는 대화를 나누고 싶습니다.",
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
        
        # generated_questions 출력
        print(f"\n❓ 생성된 질문들 ({len(result.get('generated_questions', []))}개):")
        for i, question in enumerate(result.get('generated_questions', []), 1):
            print(f"{i}. {question}")
        
        print("="*50)

    except Exception as e:
        print(f"\n❌ 에러가 발생했습니다: {e}")
        print(f"에러 타입: {type(e).__name__}")
        import traceback
        print(f"상세 에러: {traceback.format_exc()}")
        print("Google Cloud 인증 정보(.env 파일 등)가 올바르게 설정되었는지 확인해주세요.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
