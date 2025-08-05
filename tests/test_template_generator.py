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
        problem="새로운 기술 스택에 대한 학습 곡선과 기존 레거시 코드 유지보수 업무 사이의 균형점을 찾는 데 어려움을 겪고 있음",
        dialogue_type='신규',

        # 템플릿 커스텀 옵션
        use_previous_data=False,
        previous_summary=None,
        num_questions='표준', # 간단, 표준, 심화
        question_composition=['오픈형', '성과/목표', '성장/커리어'],
        tone_and_manner=5, # 0(정중) ~ 5(캐주얼)
        creativity=0.7, # 0.2 ~ 1.0
    )
    # ---------------------------------------------- #

    try:
        # 템플릿 생성 함수를 호출합니다.
        result = await generate_template(sample_input)
        
        print("\n✨ 생성된 1on1 템플릿 결과 ✨")
        print("="*30)
        pprint.pprint(result)
        print("="*30)

    except Exception as e:
        print(f"\n❌ 에러가 발생했습니다: {e}")
        print("Google Cloud 인증 정보(.env 파일 등)가 올바르게 설정되었는지 확인해주세요.")

if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행합니다.
    asyncio.run(main())
