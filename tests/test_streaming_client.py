# 1. 표준 라이브러리
import json
import os
from datetime import datetime

# 2. 서드파티 라이브러리
import requests
from dotenv import load_dotenv
from langsmith import traceable

# 3. 내부 모듈
from src.utils.mock_db import MOCK_USER_DATA
from src.utils.utils import collect_streaming_response, process_streaming_response, save_questions_to_json

# .env 파일 로드
load_dotenv()

# FastAPI 서버의 v2 스트리밍 엔드포인트 URL
url = "http://127.0.0.1:8000/generate"

# 테스트할 사용자 ID
USER_ID_TO_TEST = "user_001"

# MOCK_USER_DATA에서 사용자 찾기
user_data = next((user for user in MOCK_USER_DATA if user["user_id"] == USER_ID_TO_TEST), None)

if not user_data:
    raise ValueError(f"Test user '{USER_ID_TO_TEST}' not found in mock_db.py")

# 요청에 포함할 데이터 (TemplateGeneratorInput 스키마에 맞춰서)
# mock_db에서 이전 미팅 기록을 가져와서 previous_summary 생성
def create_previous_summary_from_mock_db(user_data, use_previous_data: bool = True):
    """mock_db의 실제 데이터를 사용하여 이전 미팅 기록 생성"""
    if not use_previous_data or not user_data.get("one_on_one_history"):
        return ""
    
    # 가장 최근 미팅 기록 가져오기
    latest_meeting = user_data["one_on_one_history"][-1]
    
    # summary 데이터를 프롬프트 형식으로 변환
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



# use_previous_data 설정에 따라 이전 미팅 기록 동적 생성
use_previous_data = False  # 테스트 시 이 값을 변경하여 동작 확인 가능
if use_previous_data:
    previous_summary_data = create_previous_summary_from_mock_db(user_data, use_previous_data=True)
else:
    previous_summary_data = None

# 모든 데이터를 문자열로 전처리
purpose_str = "Growth, Work"  # 직접 문자열로 정의
question_composition_str = "Growth/Goal-oriented, Reflection/Thought-provoking, Action/Implementation-focused"  # 직접 문자열로 정의

payload = {
    "user_id": user_data["user_id"], #필수
    "target_info": user_data['name'], #필수
    "purpose": purpose_str,  # 필수, 문자열로 전처리 완료
    "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",
    "use_previous_data": use_previous_data,  # 프론트엔드에서 사용자 선택값
    "previous_summary": previous_summary_data,  # 조건에 따라 동적 설정
    "num_questions": "Standard", # Enum에 맞는 값으로 설정
    "question_composition": question_composition_str,  # 문자열로 전처리 완료
    "tone_and_manner": "Casual",
    "language": "Korean"
}

headers = {
    'Content-Type': 'application/json'
}

@traceable(run_type="chain", name="test_streaming_client")
def test_streaming():
    """스트리밍 API 테스트를 위한 함수"""
    try:
        # 스트리밍 요청 보내기
        with requests.post(url, data=json.dumps(payload), headers=headers, stream=True, timeout=300) as response: 
            # 응답 상태 코드 확인
            if response.status_code == 200:
                # 인코딩 설정
                # SSE (Server-Sent Events) 스트림을 실시간으로 처리
                print("--- 생성된 1on1 질문 목록 (스트리밍) ---")
                
                # utils.py의 함수를 사용하여 스트리밍 응답 수집
                full_response_str = collect_streaming_response(response)
                
                # 스트리밍이 모두 끝난 후 한 줄을 띄워줍니다.
                print("\n-------------------------------------")
                
                # 스트리밍 완료 후 JSON 추출 및 저장
                try:
                    # utils.py의 함수를 사용하여 JSON 추출
                    generated_questions = process_streaming_response(full_response_str)
                    
                    if generated_questions:
                        # 파일 저장 및 데이터 검증
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_path = f"data/generated_templates/questions_streamed_{timestamp}.json"
                        
                        # 디렉토리 생성과 저장
                        saved_data = save_questions_to_json(generated_questions, output_path)
                        assert saved_data is not None, "데이터 저장이 실패했습니다"
                        assert len(saved_data) > 0, "저장된 데이터가 비어있습니다"
                        
                    else:
                        print("\n⚠️ 생성된 질문이 없습니다.")
                        assert False, "생성된 질문이 없습니다"
                        
                except Exception as save_error:
                    print(f"\n❌ 파일 저장 중 오류 발생: {save_error}")
                    assert False, f"파일 저장 중 오류 발생: {save_error}"
                
            else:
                print(f"에러 발생: {response.status_code}")
                print(f"응답 내용: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"요청 중 에러 발생: {e}")

# 메인 실행
if __name__ == "__main__":
    test_streaming()
