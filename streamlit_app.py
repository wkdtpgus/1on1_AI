import streamlit as st
import requests
import json
import re
from src.services.template_generator.generate_email import generate_email
from src.utils.template_schemas import TemplateGeneratorInput, MOCK_USER_DATA, Purpose, QuestionComposition, ToneAndManner, Language
from src.services.template_generator.generate_template import generate_template
import asyncio

st.set_page_config(layout="wide")

# --- Page Title and Introduction ---
st.title("🤝 1on1 미팅 템플릿 생성 AI")
st.markdown("""
_나와 팀원의 성공적인 성장을 돕는 1on1 미팅, 어떻게 시작해야 할지 막막하셨나요?_
AI가 맞춤형 질문 템플릿을 생성하여 성공적인 1on1 미팅을 지원합니다. 
""")
st.markdown("---")

# --- MOCK DATA ---
USER_ID_TO_TEST = "user_001"
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)
if not user_data:
    st.error(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")
    st.stop()

def create_previous_summary_from_mock_db(use_previous_data: bool = True):
    if not use_previous_data or not user_data.get("one_on_one_history"):
        return ""
    latest_meeting = user_data["one_on_one_history"][-1]
    summary_sections = []
    for category, items in latest_meeting["summary"].items():
        done_items = items.get("Done", [])
        todo_items = items.get("ToDo", [])
        section = (
            f"  - {category}:\n"
            f"    Done: {', '.join(done_items) if done_items else 'None'}\n"
            f"    ToDo: {', '.join(todo_items) if todo_items else 'None'}"
        )
        summary_sections.append(section)
    return (
        f"<Previous Conversation Summary>\n"
        f"- Date: {latest_meeting['date']}\n"
        f"- Summary Categories:\n"
        f"{chr(10).join(summary_sections)}"
    )

# --- Session State Initialization ---
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []

# --- Main Form ---
with st.form("1on1_template_form"):
    st.subheader("STEP 1: 1on1 기본 정보 입력")
    
    c1, c2 = st.columns(2)
    with c1:
        target_info = st.text_input("👤 1on1 대상", value=user_data.get('name', ''), help="1on1 미팅을 진행할 팀원의 이름 또는 정보를 입력하세요.")
    with c2:
        purpose_options = [p.value for p in Purpose]
        purpose = st.multiselect("🎯 1on1 목적 (1개 이상 선택)", options=purpose_options, default=[Purpose.GROWTH.value, Purpose.WORK.value])

    detailed_context = st.text_area("📝 상세 맥락 및 주요 논의사항", height=150, placeholder="예시) 최근 팀원의 번아웃이 우려되어 원인 파악 및 해결 방안을 논의하고 싶습니다.", value="프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.")
    
    st.markdown("---")
    st.subheader("STEP 2: 질문 생성 옵션 선택")
    
    c3, c4 = st.columns(2)
    with c3:
        num_questions = st.select_slider("⚖️ 질문 개수", options=["Small", "Standard", "Large"], value="Standard")
        question_composition_options = [qc.value for qc in QuestionComposition]
        question_composition = st.multiselect("🧩 질문 유형 조합", options=question_composition_options, default=[qc.value for qc in QuestionComposition])
    with c4:
        tone_and_manner_options = [t.value for t in ToneAndManner]
        tone_and_manner = st.radio("🗣️ 톤앤매너", options=tone_and_manner_options, index=0, horizontal=True)
        language_options = [l.value for l in Language]
        language = st.radio("🌐 언어", options=language_options, index=0, horizontal=True)

    use_previous_data = st.toggle("📚 이전 1on1 기록 활용", value=True)
    
    # --- Form Submission ---
    submitted = st.form_submit_button("🚀 1on1 맞춤 템플릿 생성하기", use_container_width=True)

if submitted:
    st.session_state.form_data = {
        "user_id": USER_ID_TO_TEST,
        "target_info": target_info,
        "purpose": ", ".join(purpose),
        "detailed_context": detailed_context,
        "use_previous_data": use_previous_data,
        "previous_summary": create_previous_summary_from_mock_db(use_previous_data),
        "num_questions": num_questions,
        "question_composition": ", ".join(question_composition),
        "tone_and_manner": tone_and_manner,
        "language": language
    }

    # --- Summary Generation ---
    if 'summary' not in st.session_state or not st.session_state.summary:
        with st.spinner("템플릿 요약을 생성 중입니다..."):
            input_data = TemplateGeneratorInput(**st.session_state.form_data)
            summary_result = asyncio.run(generate_email(input_data))
            st.session_state.summary = summary_result.get('template_summary', '요약 생성에 실패했습니다.')

# --- Display Results ---
if st.session_state.summary:
    with st.expander("✅ 생성된 1on1 템플릿 요약 보기", expanded=True):
        st.markdown(st.session_state.summary)

    # --- Template Generation ---
    st.subheader("STEP 3: 생성된 1on1 질문 목록")
    
    if not st.session_state.generated_questions:
        with st.spinner("AI가 맞춤형 질문을 생성하고 있습니다..."):
            api_url = "http://localhost:8000/generate"
            payload = st.session_state.form_data
            
            full_response_str = ""
            try:
                response = requests.post(api_url, json=payload, stream=True)
                response.raise_for_status()
                
                placeholder = st.empty()
                
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        json_data = line[len('data: '):]
                        try:
                            content_chunk = json.loads(json_data)
                            full_response_str += content_chunk
                            placeholder.markdown(full_response_str + "▌")
                        except json.JSONDecodeError:
                            st.warning(f"JSON 파싱 오류: {json_data}")
                
                placeholder.markdown(full_response_str)
                
                # --- Final Processing ---
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', full_response_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    parsed_response = json.loads(json_str)
                    st.session_state.generated_questions = parsed_response.get('generated_questions', [])
                else:
                    st.error("생성된 질문에서 JSON 형식을 찾을 수 없습니다.")

            except requests.exceptions.RequestException as e:
                st.error(f"API 요청 중 오류 발생: {e}")

    if st.session_state.generated_questions:
        for i, q in enumerate(st.session_state.generated_questions, 1):
            st.info(f"**Q{i}.** {q}")
            
        # --- Feedback Buttons ---
        st.markdown("---")
        st.markdown("**생성된 템플릿은 만족스러우신가요?**")
        c5, c6, c7 = st.columns(3)
        with c5:
            if st.button("👍 마음에 들어요", use_container_width=True):
                st.toast("피드백 감사합니다! 더 좋은 템플릿을 위해 노력하겠습니다. 😄")
        with c6:
            if st.button("👎 아쉬워요", use_container_width=True):
                st.toast("피드백 감사합니다! 개선에 참고하겠습니다. 🤔")
        with c7:
            if st.button("🔄 다시 생성하기", use_container_width=True):
                st.session_state.summary = ""
                st.session_state.generated_questions = []
                st.rerun()
