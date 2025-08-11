import streamlit as st
import asyncio
from src.services.template_generator.generate_template import generate_template
from src.services.template_generator.generate_summary import generate_summary
from src.utils.template_schemas import TemplateGeneratorInput
from src.utils.mock_db import MOCK_USER_DATA
from src.utils.utils import get_user_data_by_name

st.set_page_config(layout="wide")

st.title("1-on-1 템플릿 생성기")

# --- MOCK DATA and OPTIONS ---
USER_NAMES = [user['name'] for user in MOCK_USER_DATA]

# --- MAPPING for OPTIONS (Korean Display Name -> English Value) ---
PURPOSE_MAP = {
    '성장': 'Growth',
    '만족도': 'Satisfaction',
    '관계': 'Relationships',
    '주니어 개발': 'Junior Development',
    '업무': 'Work'
}
NUM_QUESTIONS_MAP = {
    '간단하게': 'Simple',
    '보통': 'Standard',
    '상세하게': 'Advanced'
}
QUESTION_COMPOSITION_MAP = {
    '경험/이야기형': {
        'en': 'Experience/Story-based',
        'example': 'e.g. "최근에 가장 기억에 남는 프로젝트 경험은 무엇인가요?"'
    },
    '성찰/사고형': {
        'en': 'Reflection/Thought-provoking',
        'example': 'e.g. "현재 역할에서 가장 의미 있다고 느끼는 부분은 무엇인가요?"'
    },
    '행동/실행형': {
        'en': 'Action/Implementation-focused',
        'example': 'e.g. "앞으로 3개월간 어떤 구체적인 행동을 취하시겠나요?"'
    },
    '관계/협업형': {
        'en': 'Relationship/Collaboration',
        'example': 'e.g. "동료들과의 협업에서 가장 도움이 되는 부분은 무엇인가요?"'
    },
    '성장/목표 지향': {
        'en': 'Growth/Goal-oriented',
        'example': 'e.g. "1년 후에 어떤 팀장이 되고 싶으신가요?"'
    },
    '객관식': {
        'en': 'Multiple choice',
        'example': 'e.g. "현재 업무 만족도를 1-5로 평가해주세요."'
    }
}
TONE_AND_MANNER_OPTIONS = ['Formal', 'Casual']
LANGUAGE_OPTIONS = ['Korean', 'English']


# --- UI LAYOUT ---
col1, col2 = st.columns([0.4, 0.6])

with col1:
    st.header("입력 설정")
    with st.form(key='template_form'):
        # --- Basic Info ---
        st.subheader("사용자 기본정보")
        selected_user_name = st.selectbox("대상자 선택", USER_NAMES, key='user_name')
        target_info_details = st.text_input("추가 정보(팀, 역할)", placeholder="예: AI팀, 개발자", key='target_info_details')
        purpose_kr = st.multiselect("미팅 목적(다중 선택)", list(PURPOSE_MAP.keys()), key='purpose')
        detailed_context = st.text_area("상황 상세 설명 (문제상황 혹은 주요 이슈)", height=150, key='detailed_context')

        # --- Customization Options ---
        st.subheader("커스텀 옵션")
        use_previous_data = st.checkbox("지난 기록 활용하기", key='use_previous_data')
        num_questions_kr = st.selectbox("질문 수", list(NUM_QUESTIONS_MAP.keys()), index=1, key='num_questions')
        
        st.markdown("**질문 유형 (다중 선택)**")
        question_composition_selections = {}
        for name, data in QUESTION_COMPOSITION_MAP.items():
            # Markdown for visual separation: bold name, newline, and italic example
            label = f"**{name}**  \n_{data['example']}_"
            question_composition_selections[name] = st.checkbox(label, key=f"qc_{data['en']}")
        tone_and_manner = st.selectbox("톤과 방식", TONE_AND_MANNER_OPTIONS, key='tone_and_manner')
        language = st.selectbox("언어", LANGUAGE_OPTIONS, key='language')

        submit_button = st.form_submit_button(label='템플릿 생성하기')

with col2:
    st.header("생성된 템플릿")
    summary_placeholder = st.empty()
    questions_placeholder = st.empty()

# --- FORM SUBMISSION LOGIC ---
if submit_button:
    user_id = None
    previous_summary = None
    user_data = None

    if use_previous_data:
        user_name_to_find = selected_user_name
        if user_name_to_find:
            user_data = get_user_data_by_name(user_name_to_find)
        
        if user_data and user_data.get('one_on_one_history'):
            user_id = user_data['user_id']
            latest_history = user_data['one_on_one_history'][-1]
            previous_summary = f"Date: {latest_history['date']}\nSummary:\n{latest_history['summary']}"
        elif user_name_to_find:
            st.warning(f"'지난 기록 활용하기'가 선택되었지만, '{user_name_to_find}'님의 데이터를 찾을 수 없거나 기록이 없습니다. 기록 없이 생성합니다.")

    target_info = selected_user_name
    if target_info_details:
        target_info += f" ({target_info_details})"

    # Convert selected Korean options back to English values for the backend
    purpose_en = [PURPOSE_MAP[p] for p in purpose_kr]
    num_questions_en = NUM_QUESTIONS_MAP[num_questions_kr]
    question_composition_en = [QUESTION_COMPOSITION_MAP[name]['en'] for name, selected in question_composition_selections.items() if selected]

    input_data = TemplateGeneratorInput(
        user_id=user_id,
        target_info=target_info,
        purpose=purpose_en,
        detailed_context=detailed_context,
        use_previous_data=use_previous_data,
        previous_summary=previous_summary,
        num_questions=num_questions_en,
        question_composition=question_composition_en,
        tone_and_manner=tone_and_manner,
        language=language
    )

    with st.spinner('Generating your 1-on-1 template...'):
        try:
            # Run async functions concurrently
            async def generate_all():
                results = await asyncio.gather(
                    generate_summary(input_data),
                    generate_template(input_data)
                )
                return results

            summary_result, template_result = asyncio.run(generate_all())

            # Display results
            with summary_placeholder.container():
                st.subheader("템플릿 요약")
                st.info(summary_result.get('template_summary', 'No summary generated.'))
            
            with questions_placeholder.container():
                st.subheader("생성된 질문")
                for i, q in enumerate(template_result.get('generated_questions', [])):
                    if isinstance(q, dict):
                        question_text = q.get('question', 'N/A')
                        st.markdown(f"**{i+1}. {question_text}**")
                        if q.get('type') == 'multiple_choice' and 'options' in q:
                            for option in q['options']:
                                st.markdown(f"    - {option}")
                        st.write("")
                    else:
                        st.markdown(f"**{i+1}. {q}**")

        except Exception as e:
            st.error(f"An error occurred: {e}")
