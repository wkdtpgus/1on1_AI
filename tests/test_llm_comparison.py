import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.analysis import GeminiMeetingAnalyzer
from src.utils.formatter import STTProcessor
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub가 설치되지 않았습니다. WAV 외의 형식 변환에 제한이 있습니다.")
    print("📝 설치 명령: pip install pydub")

# Constants and Configuration
DATA_DIR = "data"
DEFAULT_TRANSCRIPT_DIR = "/Users/kimjoonhee/Documents/Orblit_1on1_AI"

# QA_PAIRS constant - moved to module level to eliminate duplication
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
        "question": "마지막으로, 오늘 나눈 이야기 외에 세현님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
        "answer": ""
    }
]

def load_sample_transcript(file_path: str) -> dict:
    """실제 전사 파일에서 STT 데이터 로드"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 파일 형식에 따른 텍스트 추출
        if (file_path.endswith("test_1on1.txt") or 
            file_path.endswith("test_50min_meeting.txt") or
            file_path.endswith("test_career_focus.txt") or
            file_path.endswith("test_performance_issue.txt")):
            # 테스트 파일들은 전체 내용을 그대로 사용
            selected_text = content.strip()
        elif "Gemini가 작성한 회의록.txt" in file_path:
            # Gemini 회의록 파일은 전체 내용을 그대로 사용
            selected_text = content.strip() 
        else:
            selected_text = _extract_transcript_text(content)
        
        return {
            "status": "success",
            "transcript": selected_text,  # 전사 텍스트
            "full_text": selected_text,   # 이전 버전 호환성을 위해 유지
            "timestamp": "2025-07-28T16:44:07",
            # 디버깅용 정보
            "options": _get_debug_info(content)
        }
        
    except Exception as e:
        print(f"❌ 파일 로드 오류: {e}")
        return None

# Legacy functions moved to TranscriptProcessor class


def print_section(title: str, content: str):
    """섹션 출력 함수"""
    print("\\n" + "="*80)
    print(f" {title}")
    print("="*80)
    print(content)


def save_analysis_result(result: str, model_type: str):
    """분석 결과를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    if model_type == "openai":
        filename = f"openai_gpt_result_{timestamp}.json"
        title = "OpenAI GPT 회의 분석 결과"
    elif model_type == "gemini":
        filename = f"vertexai_gemini_result_{timestamp}.json"
        title = "Google Vertex AI Gemini 회의 분석 결과"
    else:
        filename = f"analysis_result_{timestamp}.json"
        title = "회의 분석 결과"
    
    filepath = os.path.join("data", filename)
    
    # JSON 파싱 후 예쁘게 저장
    try:
        json_data = json.loads(result)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"💾 {title} 저장 (JSON): {filepath}")
    except json.JSONDecodeError as e:
        # 파싱 실패시 원본 그대로 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"💾 {title} 저장 (원본): {filepath}")
        print(f"⚠️ JSON 파싱 실패: {str(e)[:100]}")


def get_test_data_and_questions():
    """테스트 데이터 파일과 해당 질문 리스트 반환"""
    test_configs = {
        "1": {
            "name": "기본 1-on-1 미팅 (test_1on1.txt)",
            "file": "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_1on1.txt",
            "questions": [
                "이분기에 달성한 주요 성과는 무엇인가요?",
                "프로젝트 진행 중 어떤 어려움이 있었나요?",
                "3분기에 계획된 새로운 프로젝트는 무엇인가요?",
                "개인적인 성장 목표는 무엇인가요?",
                "어떤 지원이나 리소스가 필요한가요?"
            ]
        },
        "2": {
            "name": "50분 종합 미팅 (test_50min_meeting.txt)",
            "file": "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_50min_meeting.txt",
            "questions": [
                "이커머스 플랫폼 개선 프로젝트의 현재 진행 상황은 어떤가요?",
                "새로운 기술 학습(파이썬, 머신러닝)에서 어떤 어려움이 있었나요?",
                "데이터 분석에서 발견한 흥미로운 인사이트가 있나요?",
                "업무와 학습 시간의 균형을 어떻게 맞추고 계신가요?",
                "향후 3개월간의 개인 목표는 무엇인가요?",
                "커리어 패스에 대한 고민과 방향성은?",
                "현재 업무 분배에서 조정이 필요한 부분이 있나요?",
                "팀이나 회사에 대한 개선 제안사항이 있나요?"
            ]
        },
        "3": {
            "name": "커리어 개발 중심 미팅 (test_career_focus.txt)",
            "file": "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_career_focus.txt",
            "questions": [
                "입사 후 지금까지의 성장을 어떻게 평가하시나요?",
                "기술 전문성과 매니지먼트 중 어떤 방향으로 발전하고 싶나요?",
                "5년 후 목표하는 포지션은 무엇인가요?",
                "PMP나 클라우드 기술 학습은 어떻게 진행되고 있나요?",
                "리더십 역량 개발을 위한 계획이 있나요?",
                "현재 회사에서의 성장 가능성을 어떻게 보시나요?",
                "워라밸과 지속가능한 성장을 위한 고민은 무엇인가요?"
            ]
        },
        "4": {
            "name": "성과 개선 미팅 (test_performance_issue.txt)",
            "file": "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_performance_issue.txt",
            "questions": [
                "최근 업무 완료가 지연되는 주요 원인은 무엇이라고 생각하나요?",
                "코드 품질 향상을 위해 어떤 노력을 하고 계신가요?",
                "팀 회의나 협업에서 더 적극적으로 참여하려면 어떻게 해야 할까요?",
                "업무 스트레스나 동기부여에서 어려움이 있나요?",
                "기술적 역량 향상을 위한 학습 계획은?",
                "1년 후 어떤 개발자가 되고 싶나요?"
            ]
        },
        "5": {
            "name": "김준희 Q&A (질문+답변)",
            "file": "/Users/kimjoonhee/Documents/Orblit_1on1_AI/김준희.txt",
            "qa_pairs": [
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
                    "question": "만약 지금 당장 새로운 것을 시도할 수 있는 기회가 주어진다면,어떤 종류의 AI 프로젝트나 기술에 도전해보고 싶으신가요?",
                    "answer": ""
                },
                {
                    "question": "마지막으로, 오늘 나눈 이야기 외에 세현님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
                    "answer": ""
                }
            ]
        }
    }
    
    print("📋 테스트할 데이터를 선택하세요:")
    for key, config in test_configs.items():
        print(f"{key}. {config['name']}")
    
    choice = input("\n선택 (1-5): ").strip()
    
    if choice in test_configs:
        config = test_configs[choice]
        
        # qa_pairs가 있으면 질문만 추출, 없으면 기존 questions 사용
        if "qa_pairs" in config:
            questions = [qa["question"] for qa in config["qa_pairs"]]
            config["questions"] = questions
        
        return config
    else:
        print("❌ 잘못된 선택입니다. 기본값으로 test_1on1.txt를 사용합니다.")
        return test_configs["1"]

def main():
    """메인 테스트 함수"""
    print("🚀 통합 LLM 분석 테스트 시작 (JSON 출력)")
    print("선택하세요:")
    print("1. Gemini 분석 테스트")
    print("2. 오디오 처리 및 전사 테스트")
    print("3. 통합 분석 파이프라인 테스트")
    print("4. 미리 작성된 Q&A 분석 테스트")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        _run_gemini_test()
    elif choice == "2":
        _run_audio_processing_test()
    elif choice == "3":
        _run_integrated_pipeline_test()
    elif choice == "4":
        _run_qa_analysis_test()
    else:
        print("❌ 잘못된 선택입니다. 1-4를 선택해주세요.")


def _run_gemini_test():
    """Gemini 분석 테스트 실행 (JSON 전용)"""
    # 테스트 데이터 선택
    test_config = get_test_data_and_questions()
    transcript_file = test_config["file"]
    questions = test_config["questions"]
    
    print(f"\n📊 Gemini 분석 테스트 (JSON)")
    print(f"📄 선택된 데이터: {test_config['name']}")
    print(f"📄 전사 파일 로드 중: {transcript_file}")
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료")
    print(f"   - 전체 텍스트 길이: {len(stt_data['full_text'])}자")
    print(f"   - 사용할 질문 개수: {len(questions)}개")
    
    # Gemini 분석기 초기화
    print("\n🔧 Gemini 모델 초기화 중...")
    try:
        analyzer = GeminiMeetingAnalyzer()
        print("✅ Gemini 분석기 초기화 완료")
    except Exception as e:
        print(f"❌ Gemini 분석기 초기화 실패: {e}")
        return
    
    # STT 결과 분석 (JSON)
    print(f"\n🔄 Gemini로 분석 중 (JSON 형식)...")
    try:
        # STT 데이터에서 전사 텍스트 추출
        transcript_text = stt_data.get("transcript", "")
        if not transcript_text:
            print("❌ 전사 내용이 없습니다.")
            return
        
        result_text = analyzer.analyze_comprehensive(transcript_text, questions=questions)
        
        print_section("Gemini 분석 결과 (JSON)", result_text[:500] + "..." if len(result_text) > 500 else result_text)
        save_analysis_result(result_text, "gemini")
        print(f"\n✅ Gemini 분석 테스트 완료!")
            
    except Exception as e:
        print(f"❌ Gemini 분석 실패: {e}")

def _run_audio_processing_test():
    """오디오 처리 및 전사 테스트 - 전체 파이프라인"""
    print("\n🎵 오디오 처리 및 전사 테스트 (전체 파이프라인)")
    print("1. 녹음 시작")
    print("2. WAV 파일 저장")
    print("3. 화자 분리 전사")
    print("4. Gemini 분석")
    
    # STTProcessor 초기화
    try:
        processor = STTProcessor()
        print("\n✅ STTProcessor 초기화 완료")
    except Exception as e:
        print(f"❌ STTProcessor 초기화 실패: {e}")
        return
    
    # 녹음 옵션 선택
    print("\n녹음 옵션을 선택하세요:")
    print("1. 새로 녹음하기")
    print("2. 기존 WAV 파일 사용하기")
    
    choice = input("선택 (1-2): ").strip()
    
    if choice == "1":
        # 새로 녹음
        print("\n🎤 녹음을 시작합니다...")
        print("중지하려면 Enter 키를 누르세요.")
        
        # 녹음 시작
        if not processor.start_recording():
            print("❌ 녹음 시작 실패")
            return
        
        print("🔴 녹음 중...")
        
        # Enter 키 대기
        input()
        
        # 녹음 중지 및 전사
        print("\n⏹️ 녹음을 중지하고 전사를 시작합니다...")
        
        # 화자 정보 입력 받기
        print("\n화자 정보를 입력하시겠습니까? (y/n): ", end="")
        if input().strip().lower() == 'y':
            participants_info = _get_participants_info()
        else:
            participants_info = None
        
        # 녹음 중지 및 전사
        transcription_result = processor.stop_recording_and_transcribe(participants_info)
        
    elif choice == "2":
        # 기존 파일 사용
        audio_file = input("\n오디오 파일 경로를 입력하세요 (.wav, .mp3, .m4a 등 지원) (Enter: 기본 샘플 파일): ").strip()
        
        if not audio_file:
            audio_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/주간회의_테스트 복사본.wav"
        
        if not os.path.exists(audio_file):
            print(f"❌ 오디오 파일이 존재하지 않습니다: {audio_file}")
            return
        
        print(f"📄 오디오 파일: {audio_file}")
        
        # WAV가 아닌 경우 변환 필요
        if not audio_file.lower().endswith('.wav'):
            print(f"🔄 {os.path.splitext(audio_file)[1]} 파일을 WAV로 변환 중...")
            converted_file = _convert_to_wav(audio_file)
            if converted_file:
                audio_file = converted_file
                print(f"✅ WAV 변환 완료: {audio_file}")
            else:
                print("❌ WAV 변환 실패")
                return
        
        # 화자 정보 입력 받기
        print("\n화자 정보를 입력하시겠습니까? (y/n): ", end="")
        if input().strip().lower() == 'y':
            participants_info = _get_participants_info()
        else:
            participants_info = None
        
        # 전사 수행
        print("\n🔄 오디오 파일 전사 중 (화자 분리)...")
        transcription_result = processor.transcribe_audio(audio_file, participants_info)
    else:
        print("❌ 잘못된 선택입니다.")
        return
    
    # 전사 결과 확인 및 데이터 검증
    if transcription_result.get("status") != "success":
        print(f"❌ 전사 실패: {transcription_result.get('message', '알 수 없는 오류')}")
        return
    
    transcript_text = transcription_result.get("transcript", "")
    if not transcript_text or transcript_text.strip() == "":
        print("❌ 전사 내용이 비어있습니다.")
        return
        
    print(f"\n✅ 전사 완료 (길이: {len(transcript_text)}자)")
    
    # Gemini 최적화 형식 사용 여부 확인
    is_gemini_format = transcript_text.startswith("## 1:1 회의 전사 내용")
    print(f"🤖 Gemini 최적화 형식: {'YES' if is_gemini_format else 'NO'}")
    
    # 화자별 발언 시간 정보 표시 (있는 경우)
    if "speaker_times" in transcription_result:
        print("\n📊 화자별 발언 시간 분석 결과:")
        print("-" * 40)
        speaker_times = transcription_result["speaker_times"]
        total_duration = transcription_result.get("total_duration_seconds", 0)
        
        for speaker_name, time_info in speaker_times.items():
            print(f"{speaker_name}: {time_info['formatted_time']} ({time_info['percentage']}%)")
        
        if total_duration > 0:
            minutes = int(total_duration // 60)
            seconds = int(total_duration % 60)
            print(f"전체 발언 시간: {minutes}분 {seconds}초")
        print("-" * 40)
    
    print_section("전사 결과 (화자 분리)", transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text)
    
    # 전사 결과 텍스트 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data", exist_ok=True)
    
    # 전사 텍스트 저장 (화자별 발언 + 통계 포함)
    transcript_file = os.path.join("data", f"transcript_{timestamp}.txt")
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("회의 전사 결과\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        # 화자별 발언 통계 (있는 경우)
        if "speaker_times" in transcription_result:
            f.write("📊 화자별 발언 시간 분석:\n")
            f.write("-" * 40 + "\n")
            speaker_times = transcription_result["speaker_times"]
            total_duration = transcription_result.get("total_duration_seconds", 0)
            
            for speaker_name, time_info in speaker_times.items():
                f.write(f"{speaker_name}: {time_info['formatted_time']} ({time_info['percentage']}%)\n")
            
            if total_duration > 0:
                minutes = int(total_duration // 60)
                seconds = int(total_duration % 60)
                f.write(f"전체 발언 시간: {minutes}분 {seconds}초\n")
            f.write("-" * 40 + "\n\n")
        
        # 대화 내용 (LLM 분석용)
        f.write("📝 대화 내용:\n")
        f.write("-" * 40 + "\n")
        f.write(transcript_text)
        f.write("\n\n")
    
    # JSON 형태로도 저장 (프론트엔드 연동용 - 간소화된 형식)
    transcript_json_file = os.path.join("data", f"transcript_{timestamp}.json")
    # 필요한 필드만 포함한 간소화된 JSON 생성
    simplified_result = {
        "transcript": transcription_result.get("transcript", ""),
        "status": transcription_result.get("status", ""),
        "timestamp": transcription_result.get("timestamp", ""),
        "speaker_times": transcription_result.get("speaker_times", {}),
        "total_duration_seconds": transcription_result.get("total_duration_seconds", 0),
        "utterances": transcription_result.get("utterances", []),
    }
    
    with open(transcript_json_file, "w", encoding="utf-8") as f:
        json.dump(simplified_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 전사 결과 저장:")
    print(f"   - 텍스트 파일: {transcript_file}")
    print(f"   - JSON 파일: {transcript_json_file}")
    
    # Gemini로 분석
    print("\n🤖 Gemini로 회의 분석을 수행하시겠습니까? (y/n): ", end="")
    if input().strip().lower() == 'y':
        # 전사 내용 최종 검증
        if not transcript_text or len(transcript_text.strip()) < 10:
            print("❌ 전사 내용이 너무 짧아 분석을 수행할 수 없습니다.")
            print(f"전사 내용 미리보기: {repr(transcript_text[:100])}...")
            return
            
        # 화자 통계 정보 전달
        speaker_stats = transcription_result.get("speaker_times", None)
        print(f"📊 화자 통계 전달: {'YES' if speaker_stats else 'NO'}")
        _analyze_with_gemini(transcript_text, speaker_stats)
    else:
        print("🔄 LLM 분석을 건너뚝니다.")
    
    print("\n✅ 오디오 처리 파이프라인 테스트 완료!")

def _get_participants_info():
    """화자 정보 입력 받기"""
    participants_info = {}
    
    print("\n화자 수를 입력하세요 (2-5): ", end="")
    num_speakers = int(input().strip() or "2")
    num_speakers = max(2, min(5, num_speakers))
    
    for i in range(num_speakers):
        speaker_label = chr(65 + i)  # A, B, C...
        print(f"\n화자 {speaker_label} 정보:")
        name = input(f"  이름: ").strip() or f"참석자{i+1}"
        role = input(f"  역할: ").strip() or "참석자"
        
        participants_info[speaker_label] = {
            "name": name,
            "role": role
        }
    
    return participants_info

def _convert_to_wav(audio_file: str) -> str:
    """오디오 파일을 WAV 형식으로 변환"""
    if not PYDUB_AVAILABLE:
        print("❌ pydub가 설치되지 않아 변환할 수 없습니다.")
        print("📝 설치 명령: pip install pydub")
        return None
    
    try:
        # 파일 확장자 감지
        file_ext = os.path.splitext(audio_file)[1].lower()
        
        # 지원되는 형식 확인
        supported_formats = ['.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma']
        if file_ext not in supported_formats:
            print(f"❌ 지원되지 않는 파일 형식: {file_ext}")
            print(f"지원 형식: {', '.join(supported_formats)}")
            return None
        
        # 오디오 로드
        if file_ext == '.mp3':
            audio = AudioSegment.from_mp3(audio_file)
        elif file_ext == '.m4a':
            audio = AudioSegment.from_file(audio_file, format="m4a")
        elif file_ext == '.flac':
            audio = AudioSegment.from_file(audio_file, format="flac")
        else:
            # 기타 형식은 일반적인 방법 사용
            audio = AudioSegment.from_file(audio_file)
        
        # WAV 파일 이름 생성
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_filename = f"converted_{base_name}_{timestamp}.wav"
        
        # data 디렉토리 생성
        os.makedirs("data", exist_ok=True)
        wav_filepath = os.path.join("data", wav_filename)
        
        # WAV로 내보내기 (모노, 16kHz로 변환)
        audio = audio.set_channels(1)  # 모노로 변환
        audio = audio.set_frame_rate(16000)  # 16kHz로 변환 (AssemblyAI 최적화)
        audio.export(wav_filepath, format="wav")
        
        print(f"💾 변환된 WAV 파일 저장: {wav_filepath}")
        return wav_filepath
        
    except Exception as e:
        print(f"❌ 오디오 변환 실패: {e}")
        return None

def _create_qa_analysis_text(qa_pairs=None):
    """미리 작성된 질문-답변을 분석용 텍스트로 변환"""
    
    # qa_pairs가 제공되지 않으면 기본값 사용 (하위 호환성)
    if qa_pairs is None:
        qa_data = [
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
                "question": "마지막으로, 오늘 나눈 이야기 외에 세현님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
                "answer": ""
            }
        ]
    else:
        qa_data = qa_pairs
    
    # Q&A 형식으로 마크다운 텍스트 생성
    lines = []
    lines.append("## 1:1 회의 질문-답변 정리")
    lines.append("")
    lines.append("### 참석자 정보")
    lines.append("- **준희님**: AI 개발자 (인턴 → 정규직 전환 예정)")
    lines.append("- **세현님**: 매니저")
    lines.append("")
    lines.append("### 질문별 답변 내용")
    lines.append("")
    
    for i, qa in enumerate(qa_data, 1):
        lines.append(f"#### Q{i}. {qa['question']}")
        lines.append("")
        if qa['answer'].strip():
            lines.append(f"**준희님 답변:** {qa['answer']}")
        else:
            lines.append("**준희님 답변:** (답변 없음)")
        lines.append("")
    
    return "\n".join(lines)

def _analyze_with_gemini(transcript_text, speaker_stats=None):
    """Gemini로 전사 결과 분석"""
    print("\n🤖 Gemini 분석을 시작합니다...")
    
    # 분석 모드 선택
    print("\n분석 모드를 선택하세요:")
    print("1. 전사 내용 기반 분석 (일반)")
    print("2. 미리 작성된 Q&A 기반 분석")
    print("Enter. 질문 없이 일반 분석 진행")
    
    mode_choice = input("분석 모드 선택 (1-2, Enter): ").strip()
    
    if mode_choice == "2":
        # Q&A 기반 분석
        print("\n📝 미리 작성된 Q&A 내용을 기반으로 분석합니다...")
        qa_text = _create_qa_analysis_text()
        print(f"✅ Q&A 텍스트 생성 완료 (길이: {len(qa_text)}자)")
        
        # Q&A 내용으로 전사 텍스트 교체
        transcript_text = qa_text
        questions = None  # Q&A에는 별도 질문 없이 분석
        
    elif mode_choice == "1":
        # 전사 내용 기반 분석 - 질문 선택
        print("\n분석에 사용할 질문 세트를 선택하세요 (Enter: 질문 없이 진행):")
        print("1. 기본 1-on-1 질문")
        print("2. 종합 미팅 질문")
        print("3. 커리어 개발 질문")
        print("4. 성과 개선 질문")
        print("5. 김준희 Q&A 질문 (질문+답변)")
        print("6. 사용자 정의 질문")
        print("Enter. 질문 없이 일반 분석 진행")
        
        choice = input("선택 (1-6, Enter): ").strip()
    else:
        # 기본값: 질문 없이 진행
        choice = ""
        questions = None  # 기본값: 질문 없음
    
    # Q&A 모드가 아닌 경우에만 질문 처리
    if mode_choice != "2" and choice:  # 선택사항이 있는 경우에만 처리
        try:
            if choice == "1":
                questions = [
                    "이분기에 달성한 주요 성과는 무엇인가요?",
                    "프로젝트 진행 중 어떤 어려움이 있었나요?",
                    "3분기에 계획된 새로운 프로젝트는 무엇인가요?",
                    "개인적인 성장 목표는 무엇인가요?",
                    "어떤 지원이나 리소스가 필요한가요?"
                ]
            elif choice == "2":
                questions = [
                    "이커머스 플랫폼 개선 프로젝트의 현재 진행 상황은 어떻게 되나요?",
                    "새로운 기술 학습(파이썬, 머신러닝)에서 어떤 어려움이 있었나요?",
                    "데이터 분석에서 발견한 흥미로운 인사이트가 있나요?",
                    "업무와 학습 시간의 균형을 어떻게 맞추고 계신가요?",
                    "향후 3개월간의 개인 목표는 무엇인가요?",
                    "커리어 패스에 대한 고민과 방향성은?",
                    "현재 업무 분배에서 조정이 필요한 부분이 있나요?",
                    "팀이나 회사에 대한 개선 제안사항이 있나요?"
                ]
            elif choice == "3":
                questions = [
                    "입사 후 지금까지의 성장을 어떻게 평가하시나요?",
                    "기술 전문성과 매니지먼트 중 어떤 방향으로 발전하고 싶나요?",
                    "5년 후 목표하는 포지션은 무엇인가요?",
                    "PMP나 클라우드 기술 학습은 어떻게 진행되고 있나요?",
                    "리더십 역량 개발을 위한 계획이 있나요?",
                    "현재 회사에서의 성장 가능성을 어떻게 보시나요?",
                    "워라밸과 지속가능한 성장을 위한 고민은 무엇인가요?"
                ]
            elif choice == "4":
                questions = [
                    "최근 업무 완료가 지연되는 주요 원인은 무엇이라고 생각하나요?",
                    "코드 품질 향상을 위해 어떤 노력을 하고 계신가요?",
                    "팀 회의나 협업에서 더 적극적으로 참여하려면 어떻게 해야 할까요?",
                    "업무 스트레스나 동기부여에서 어려움이 있나요?",
                    "기술적 역량 향상을 위한 학습 계획은?",
                    "1년 후 어떤 개발자가 되고 싶나요?"
                ]
            elif choice == "5":
                # 김준희 Q&A - qa_pairs에서 질문과 답변을 Questions 필드에 전달
                qa_pairs = [
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
                        "question": "마지막으로, 오늘 나눈 이야기 외에 세현님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
                        "answer": ""
                    }
                ]
                # Q&A 형식을 Questions 필드로 변환 (질문: 답변 형태)
                questions = []
                for qa in qa_pairs:
                    if qa['answer'].strip():
                        questions.append(f"Q: {qa['question']}\nA: {qa['answer']}")
                    else:
                        questions.append(f"Q: {qa['question']}\nA: (답변 없음)")
                # questions 리스트가 생성되었으므로 transcript_text는 변경하지 않음
            elif choice == "6":
                print("\n질문을 입력하세요 (빈 줄 입력시 종료):")
                questions = []
                while True:
                    q = input(f"질문 {len(questions)+1}: ").strip()
                    if not q:
                        break
                    questions.append(q)
                if not questions:
                    questions = None  # 질문 없이 진행
            else:
                print("❌ 잘못된 선택입니다. 질문 없이 진행합니다.")
                questions = None
        except Exception as e:
            print(f"⚠️ 질문 로드 실패: {e}. 질문 없이 진행합니다.")
            questions = None
    
    if questions:
        print(f"\n📋 선택된 질문 개수: {len(questions)}개")
    else:
        print(f"\n📋 질문 없이 일반 분석을 진행합니다.")
    
    # Gemini 분석기 초기화
    try:
        analyzer = GeminiMeetingAnalyzer()
        print("✅ Gemini 분석기 초기화 완료")
    except Exception as e:
        print(f"❌ Gemini 분석기 초기화 실패: {e}")
        return
    
    # 분석 수행
    print("\n🔄 Gemini로 분석 중...")
    try:
        # questions가 None이어도 analyze_comprehensive는 처리할 수 있음
        result_text = analyzer.analyze_comprehensive(transcript_text, questions=questions, speaker_stats=speaker_stats)
        
        print_section("Gemini 분석 결과 (JSON)", result_text[:500] + "..." if len(result_text) > 500 else result_text)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("data", exist_ok=True)
        
        # 분석 결과 저장 (전사 결과는 이미 저장됨)
        save_analysis_result(result_text, "gemini")
        
    except Exception as e:
        print(f"❌ Gemini 분석 실패: {e}")

def _run_integrated_pipeline_test():
    """통합 분석 파이프라인 테스트 - 질문 리스트 기반 분석 (JSON 전용)"""
    print("\n🔄 통합 분석 파이프라인 테스트 (JSON 출력)")
    
    # 테스트 데이터 선택
    test_config = get_test_data_and_questions()
    transcript_file = test_config["file"]
    questions = test_config["questions"]
    
    print(f"📄 선택된 데이터: {test_config['name']}")
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료 (길이: {len(stt_data['full_text'])}자)")
    print(f"   - 사용할 질문 개수: {len(questions)}개")

    # Gemini 분석기로 통합 분석
    try:
        analyzer = GeminiMeetingAnalyzer()
        print("\n✅ Gemini 분석기 초기화 완료")
        
        # STT 데이터에서 전사 텍스트 추출
        transcript_text = stt_data.get("transcript", "")
        if not transcript_text:
            print("❌ 전사 내용이 없습니다.")
            return
        
        result_text = analyzer.analyze_comprehensive(transcript_text, questions=questions)
        
        print_section("통합 분석 결과 (JSON)", result_text[:500] + "..." if len(result_text) > 500 else result_text)            
        save_comprehensive_result(result_text, len(transcript_text))
        print("✅ 통합 분석 파이프라인 테스트 완료!")
            
    except Exception as e:
        print(f"❌ 통합 분석 실패: {e}")


def save_comprehensive_result(comprehensive_result: str, transcript_length: int):
    """통합 분석 결과를 JSON 파일로 저장"""
    result_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    # 통합 분석 결과 파일 저장 (JSON) - transcript_length는 추후 사용을 위해 유지
    result_filename = f"comprehensive_analysis_{result_timestamp}.json"
    result_filepath = os.path.join("data", result_filename)
    
    with open(result_filepath, "w", encoding="utf-8") as f:
        f.write(comprehensive_result)
    
    print(f"💾 통합 분석 결과 저장 (JSON): {result_filepath}")
    print(f"📄 전사 내용 길이: {transcript_length}자")


def _run_qa_analysis_test():
    """미리 작성된 Q&A 분석 테스트 (JSON 전용)"""
    print("\n📝 미리 작성된 Q&A 분석 테스트 (JSON)")
    
    # Q&A 데이터 정의 (옵션 5와 동일한 데이터)
    qa_pairs = [
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
            "question": "마지막으로, 오늘 나눈 이야기 외에 세현님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
            "answer": ""
        }
    ]
    
    # Q&A를 Questions 형식으로 변환
    print("🔄 Q&A 데이터를 Questions 형식으로 변환 중...")
    questions = []
    for qa in qa_pairs:
        if qa['answer'].strip():
            questions.append(f"Q: {qa['question']}\nA: {qa['answer']}")
        else:
            questions.append(f"Q: {qa['question']}\nA: (답변 없음)")
    
    print(f"✅ Q&A Questions 변환 완료 ({len(questions)}개 항목)")
    
    # Questions 미리보기
    print("\n📄 Questions 데이터 미리보기:")
    print("-" * 60)
    preview_questions = questions[:2]  # 처음 2개만 미리보기
    for i, q in enumerate(preview_questions, 1):
        print(f"{i}. {q[:100]}{'...' if len(q) > 100 else ''}")
    if len(questions) > 2:
        print(f"... 및 {len(questions)-2}개 추가 항목")
    print("-" * 60)
    
    # Questions 텍스트 저장 (디버깅용)
    import os
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data", exist_ok=True)
    
    qa_questions_file = os.path.join("data", f"qa_questions_{timestamp}.txt")
    with open(qa_questions_file, "w", encoding="utf-8") as f:
        for i, q in enumerate(questions, 1):
            f.write(f"=== Question {i} ===\n")
            f.write(q + "\n\n")
    print(f"💾 Q&A Questions 저장: {qa_questions_file}")
    
    # Gemini 분석기 초기화
    print("\n🔧 Gemini 모델 초기화 중...")
    try:
        analyzer = GeminiMeetingAnalyzer()
        print("✅ Gemini 분석기 초기화 완료")
    except Exception as e:
        print(f"❌ Gemini 분석기 초기화 실패: {e}")
        return
    
    # Q&A 분석 수행
    print(f"\n🔄 Gemini로 Q&A 분석 중...")
    try:
        # 실제 전사 파일 로드 (Gemini 포맷 추출)
        transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/김준희.txt"
        
        def extract_gemini_formatted_content(file_path: str) -> str:
            """Extract Gemini-friendly formatted content from 김준희.txt"""
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find the start of the conversation section
            conversation_start = content.find("## 1:1 회의 전사 내용")
            if conversation_start == -1:
                return content  # Return full content if formatting not found
            
            # Extract from conversation section onwards
            formatted_content = content[conversation_start:]
            return formatted_content.strip()
        
        try:
            transcript_content = extract_gemini_formatted_content(transcript_file)
            print(f"✅ 전사 파일 로드 완료 (Gemini 포맷): {len(transcript_content)}자")
        except FileNotFoundError:
            print(f"❌ 전사 파일을 찾을 수 없습니다: {transcript_file}")
            return
        except Exception as e:
            print(f"❌ 전사 파일 로드 실패: {e}")
            return
        
        # Transcript에는 Gemini 포맷 전사 내용, Questions에는 Q&A 데이터
        result_text = analyzer.analyze_comprehensive(transcript_content, questions=questions)
        
        print_section("Gemini Q&A 분석 결과 (JSON)", result_text[:500] + "..." if len(result_text) > 500 else result_text)
        
        # 결과 저장
        qa_result_file = f"qa_analysis_result_{timestamp}.json"
        qa_result_path = os.path.join("data", qa_result_file)
        
        # JSON 파싱 후 예쁘게 저장
        try:
            import json
            json_data = json.loads(result_text)
            with open(qa_result_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Q&A 분석 결과 저장 (JSON): {qa_result_path}")
        except json.JSONDecodeError as e:
            # 파싱 실패시 원본 그대로 저장
            with open(qa_result_path, "w", encoding="utf-8") as f:
                f.write(result_text)
            print(f"💾 Q&A 분석 결과 저장 (원본): {qa_result_path}")
            print(f"⚠️ JSON 파싱 실패: {str(e)[:100]}")
        
        print(f"\n✅ Q&A 분석 테스트 완료!")
            
    except Exception as e:
        print(f"❌ Q&A 분석 실패: {e}")


if __name__ == "__main__":
    main()