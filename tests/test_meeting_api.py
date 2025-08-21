import json
import os
import requests

# API 엔드포인트 설정
BASE_URL = "http://localhost:8000"  # FastAPI 서버 주소
API_ENDPOINT = f"{BASE_URL}/api/analyze"

# 테스트 데이터
QA_PAIRS = [
    {
        "question": "벌써 두 달 반이 다 되어가네요. 처음 오셨을 때보다 회사 분위기나 동료들과는 좀 더 편해지셨나요?",
        "answer": "제가 점점 편해지고 있다는게 조금씩 느껴지고 있어요"
    },
    {
        "question": "우리 회사에 남아서 더 하게된 이유는 무엇인가요?",
        "answer": "인턴 기간 동안 일하는 게 너무 재밌었고 또 제가 많이 성장할 수 있을 거라고 생각했어요. 2개월 전의 저랑 지금의 저랑 확실히 성장하고 조금 더 나아지고 있다라는 걸 느꼈어요"
    },
    {
        "question": "요즘 개인적으로 가장 흥미롭게 몰입하고 있는 업무나 프로젝트가 있으시다면 어떤 건가요?",
        "answer": "제가 정리하는 것을 좋아해서 요즘 요약하는 것에 대해서 프롬프트 엔지니어링을 하는 것에 가장 몰입하고 있는 것 같아요. 제가 봤을 때도 이 정도면 괜찮은데 싶을 정도로 하고 싶은데 아직 만족하는 결과물은 아닌 것 같아요"
    },
    {
        "question": "최근 2주간 진행했던 업무 중에서 특히 기억에 남거나, '이건 정말 잘했다!'고 생각하는 성과가 있다면 어떤 것인지 구체적으로 이야기해주실 수 있을까요?",
        "answer": "아직까지 기억에 남는 성과는 없는 것 같아요. 이번에 1on1이 끝나고 테스트해보고 실제 결과를 빨리 보고 싶어요"
    },
    {
        "question": "수습을 기점으로 정규직 전환을 앞두고 계신데, 앞으로 회사에서 어떤 역할을 하고 싶고, 어떤 부분에서 기여하고 싶다는 계획을 가지고 계신가요?",
        "answer": "AI 개발자로서도 더 기여하고 싶고 또 지현님이 인턴 기간에 말씀해 주셨듯이 점점 풀스택 개발자로 성장하고 싶어요"
    },
    {
        "question": "현재 맡고 계신 업무가 준희님의 기술 스택이나 강점과 잘 맞는다고 느끼시는지 궁금합니다. 혹시 잘 맞는다고 느끼는 부분과 개선이 필요하다고 생각하는 부분이 있으신가요?",
        "answer": "하루하루 새로운 기술들 새로운 기법들이 많이 나오는데 이런 부분들이 새로운 것을 배우는 걸 좋아하는 제게는 정말 잘 맞는 것 같아요"
    },
    {
        "question": "AI 개발자로서 앞으로 어떤 기술 역량을 중점적으로 개발하고 싶으신가요? 그리고 이를 위해 어떤 계획을 가지고 계신지 궁금합니다.",
        "answer": "아직까지는 현재 업무에서 다루고 있는 llm이나 프롬프트 엔지니어링에 관심이 있는 것 같아요. 최근에 비슷한 일을 하는 친구들이랑 이야기를 해보면서 oss 오픈소스 모델을 가지고 이것저것 해보고 싶다는 생각도 들었어요"
    },
    {
        "question": "지난번에 이야기 나눴던 'Cursor MCP 서버 사용 및 리뷰'는 잘 진행되고 있는지 궁금합니다. 혹시 사용하시면서 특별히 느끼신 점이나 어려움은 없으셨나요?",
        "answer": "리뷰는 못했지만 피그마, 슈퍼베이스 정도 써봤던 것 같아요 최근에는 클로드 코드 템플릿 사이트? 같은 곳에서 에이전트랑 mcp를 쉽게 사용할 수 있는게 있어서 ai 엔지니어, 프롬프트 엔지니어, 코드 리뷰어 에이전트를 조합해서 사용해보고 있어요"
    },
    {
        "question": "준희님의 성장을 위해 회사에서 어떤 지원을 해주면 가장 도움이 될 것이라고 생각하시나요?",
        "answer": "저는 여러 프로젝트를 해보는게.. 도움이 될 것 같아요. 기획적인 측면에서도 생각하려고 노력하는게 여러 방면으로 시야를 넓혀주는 것 같아요"
    },
    {
        "question": "현재 업무량은 적절하다고 느끼시는지 궁금합니다. 혹시 더 도전하고 싶은 업무가 있으시거나, 반대로 부담이 된다고 느끼는 부분이 있으신가요?",
        "answer": "업무량은 적절한 것 같아요 부담감 또한 조금씩은 있어야 한다고 생각하는데 적절하다고 생각합니다.."
    },
    {
        "question": "업무 몰입도 측면에서, 지난 한 달을 돌아봤을 때 스스로 어느 정도 점수를 줄 수 있을까요? (1점: 매우 낮음 ~ 5점: 매우 높음)",
        "answer": "4점 인 것 같아요 1on1에 대해서 잘 와닿지가 않아서 최대한 이해하려고 자료 조사를 많이 했는데 도움도 많이 된 것 같고 칭찬도 해주셔서 4점 주겠습니다"
    },
    {
        "question": "AI 개발자로서 핵심 스킬셋을 개발하는 데 있어 다음 중 어떤 방식이 가장 효과적이라고 생각하시나요? (a) 사내 스터디 참여, (b) 외부 교육 수강, (c) 개인 프로젝트 진행, (d) 논문 및 자료 학습",
        "answer": "이번 인턴 하면서 느낀건데 확실히 프로젝트에 직접 참여하는게 정말 도움이 많이 되었던 것 같아요"
    },
    {
        "question": "앞으로 준희님이 가장 성장하고 싶은 영역은 다음 중 어디인가요? (a) 특정 AI 모델 개발 역량, (b) 데이터 처리 및 분석 능력, (c) 협업 및 커뮤니케이션 스킬, (d) 문제 해결 능력",
        "answer": "요즘은 (a)인데 데이터 분석을 했었어서 그 다음을 고르라면 (b)인 것 같아요 근데 요즘 느끼는거는 데이터 분석이라는게 업무를 하면서 자연스럽게 하게되는 것 같기도 해요"
    },
    {
        "question": "만약 지금 당장 새로운 것을 시도할 수 있는 기회가 주어진다면, 어떤 종류의 AI 프로젝트나 기술에 도전해보고 싶으신가요?",
        "answer": ""
    },
    {
        "question": "마지막으로, 오늘 나눈 이야기 외에 준희님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
        "answer": ""
    }
]

PARTICIPANTS_INFO = {
    "leader": "김지현",
    "member": "김준희"
}

MEETING_DATETIME = "2024-12-08T14:30:00"
FILE_ID = "joonhee_1on1.m4a"


def test_full_analysis():
    """전체 분석 테스트 (only_title=False)"""
    print("=== 전체 분석 테스트 ===")
    
    payload = {
        "file_id": FILE_ID,
        "qa_pairs": json.dumps(QA_PAIRS, ensure_ascii=False),
        "participants_info": json.dumps(PARTICIPANTS_INFO, ensure_ascii=False),
        "meeting_datetime": MEETING_DATETIME,
        "only_title": False
    }
    
    try:
        print(f"요청 URL: {API_ENDPOINT}")
        print(f"요청 데이터 크기: {len(json.dumps(payload))} 바이트")
        
        response = requests.post(API_ENDPOINT, data=payload, timeout=300)
        
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 전체 분석 성공!")
            print(f"제목: {result.get('title', 'N/A')}")
            print(f"분석 결과 키들: {list(result.keys())}")
            
            # 결과를 프로젝트 root/data 폴더에 저장
            project_root = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, "test_result_full.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📝 결과가 {file_path}에 저장되었습니다.")
            
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print(f"오류 내용: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


def test_title_only():
    """제목만 생성 테스트 (only_title=True)"""
    print("\n=== 제목만 생성 테스트 ===")
    
    payload = {
        "qa_pairs": json.dumps(QA_PAIRS, ensure_ascii=False),
        "participants_info": json.dumps(PARTICIPANTS_INFO, ensure_ascii=False),
        "meeting_datetime": MEETING_DATETIME,
        "only_title": True
    }
    
    try:
        print(f"요청 URL: {API_ENDPOINT}")
        print("file_id 없이 요청 (only_title=True)")
        
        response = requests.post(API_ENDPOINT, data=payload, timeout=60)
        
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 제목 생성 성공!")
            print(f"제목: {result.get('title', 'N/A')}")
            print(f"응답 키들: {list(result.keys())}")
            
            # 결과를 프로젝트 root/data 폴더에 저장
            project_root = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, "test_result_title_only.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📝 결과가 {file_path}에 저장되었습니다.")
            
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print(f"오류 내용: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


def test_server_connection():
    """서버 연결 테스트"""
    print("=== 서버 연결 테스트 ===")
    
    try:
        config_url = f"{BASE_URL}/api/config"
        response = requests.get(config_url, timeout=5)
        
        if response.status_code == 200:
            print("✅ 서버 연결 성공!")
            config = response.json()
            print(f"설정: {config}")
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("FastAPI 서버가 실행 중인지 확인해주세요: uvicorn src.web.stt_main:app --reload")


if __name__ == "__main__":
    # 1. 서버 연결 확인
    test_server_connection()
    
    # 2. 제목만 생성 테스트 (빠름)
    test_title_only()
    
    # 3. 전체 분석 테스트 (오래 걸림)
    user_input = input("\n전체 분석 테스트를 진행하시겠습니까? (y/N): ")
    if user_input.lower() in ['y', 'yes']:
        test_full_analysis()
    else:
        print("전체 분석 테스트를 건너뜁니다.")
    
    print("\n테스트 완료!")