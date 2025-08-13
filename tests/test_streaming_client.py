import requests
import json
import os
from dotenv import load_dotenv
from langsmith import traceable
from src.utils.mock_db import MOCK_USER_DATA

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
payload = {
    "user_id": user_data["user_id"],
    "target_info": user_data['name'],
    "purpose": ["Growth", "Work"], # Enum에 맞는 값으로 설정
    "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여, 갈등상황 진단 및 해결책 논의하고자 함. 김수연씨의 매니징 능력 개선을 위함.",

    "use_previous_data": True,
    "num_questions": "Standard", # Enum에 맞는 값으로 설정
    "question_composition": ["Growth/Goal-oriented", "Reflection/Thought-provoking", "Action/Implementation-focused"], # Enum에 맞는 값으로 설정
    "tone_and_manner": "Casual",
    "language": "Korean"
}

headers = {
    'Content-Type': 'application/json'
}

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
                
                # 스트리밍 데이터를 모아서 저장할 변수
                full_response_str = ""
                generated_questions = []
                
                for line in response.iter_lines(decode_unicode=True):
                    # SSE 데이터는 "data: "로 시작합니다.
                    if line.startswith('data: '):
                        # "data: " 접두사를 제거하여 실제 JSON 데이터를 추출합니다.
                        json_data = line[len('data: '):]
                        try:
                            # 서버에서 오는 데이터 조각(chunk)을 파싱합니다.
                            content_chunk = json.loads(json_data)
                            # 줄바꿈 없이 이어서 출력하여 타이핑 효과를 냅니다.
                            print(content_chunk, end="", flush=True)
                            
                            # 전체 응답을 모으기
                            full_response_str += str(content_chunk)
                            
                        except json.JSONDecodeError:
                            # 파싱에 실패한 경우, 원본 데이터를 출력하여 디버깅을 돕습니다.
                            print(f"JSON 파싱 오류: {json_data}")
                
                # 스트리밍이 모두 끝난 후 한 줄을 띄워줍니다.
                print("\n-------------------------------------") # Add a newline for cleaner terminal output after the stream.
                
                # 스트리밍 완료 후 파일 저장 및 LangSmith 추적 개선
                try:
                    # 전체 응답에서 JSON 추출
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', full_response_str, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        full_response = json.loads(json_str)
                        generated_questions = full_response.get('generated_questions', [])
                        
                        if generated_questions:
                            # save_questions_to_json 함수 사용하여 파일 저장
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_path = f"data/generated_templates/questions_streamed_{timestamp}.json"
                            
                            # 디렉토리 생성
                            os.makedirs("data/generated_templates", exist_ok=True)
                            
                            # save_questions_to_json 함수 사용
                            from src.utils.utils import save_questions_to_json
                            save_questions_to_json(generated_questions, output_path)
                            
                            print(f"\n✅ 질문들이 '{output_path}'에 저장되었습니다.")
                            print(f"📊 총 {len(generated_questions)}개의 질문이 생성되었습니다.")
                            
                            # LangSmith에서 깔끔하게 추적되도록 완전한 JSON을 한 번 더 출력
                            print("\n--- LangSmith 추적용 완전한 JSON ---")
                            print(json.dumps(full_response, ensure_ascii=False, indent=2))
                            print("----------------------------------------")
                            
                        else:
                            print("\n⚠️ 생성된 질문이 없습니다.")
                    else:
                        print("\n⚠️ JSON 응답을 찾을 수 없습니다.")
                        
                except Exception as save_error:
                    print(f"\n❌ 파일 저장 중 오류 발생: {save_error}")
                
            else:
                print(f"에러 발생: {response.status_code}")
                print(f"응답 내용: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"요청 중 에러 발생: {e}")

@traceable(run_type="chain", name="test_streaming_client")
def main():
    """메인 함수 - LangSmith 추적을 위한 래퍼"""
    # 스트리밍 실행
    test_streaming()
    
    # 저장된 JSON 파일을 읽어서 LangSmith에 추적
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/generated_templates/questions_streamed_{timestamp}.json"
        
        # 파일이 존재하면 읽어서 추적
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print(f"\n🔍 LangSmith 추적용 저장된 데이터:")
            print(json.dumps(saved_data, ensure_ascii=False, indent=2))
            
            # 여기서 LangSmith에 깔끔하게 추적됨
            return saved_data
        else:
            print(f"\n⚠️ 저장된 파일을 찾을 수 없습니다: {output_path}")
            return None
            
    except Exception as e:
        print(f"\n❌ 파일 읽기 중 오류: {e}")
        return None

# 메인 실행
if __name__ == "__main__":
    main()
