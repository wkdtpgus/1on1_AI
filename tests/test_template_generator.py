import asyncio
import pprint

from src.template_generator.schemas import TemplateGeneratorInput
from src.template_generator.chains import generate_template

async def main():
    """
    템플릿 생성기 체인을 테스트하기 위한 메인 함수입니다.
    """
    print("1on1 템플릿 생성을 시작합니다...")
    
    # --- 테스트할 입력 데이터를 여기에서 수정하세요 --- #
    sample_input = TemplateGeneratorInput(
        # 기본 정보
        target_info="김민준, 시니어 백엔드 엔지니어, 최근 입사 3개월 차",
        purpose="온보딩 과정 중간 점검 및 팀 적응 현황 파악",
        problem="딱히 없어보이는데, 있는지 궁금함",
        dialogue_type='New',

        # 템플릿 커스텀 옵션
        use_previous_data=False,
        previous_summary=None,
        num_questions='Advanced', # Simple, Standard, Advanced
        question_composition=['Multiple choice'], #'Experience/Story-based', 'Growth/Goal-oriented', 'Reflection/Thought-provoking', 'Action/Implementation-focused', 'Relationship/Collaboration', 
        tone_and_manner='Formal', # Formal or Casual
        creativity=0.1, # 0.0 ~ 1.0
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
