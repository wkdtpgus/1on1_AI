import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.llm_analysis import OpenAIMeetingAnalyzer, GeminiMeetingAnalyzer
from src.models.audio_processing import AudioProcessor

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

def _extract_transcript_text(content: str) -> str:
    """전사 파일에서 텍스트 추출"""
    full_transcript = _extract_full_text(content)
    speaker_separated = _extract_speaker_text(content)
    
    # 화자별 발언이 있으면 우선 사용, 없으면 전체 텍스트 사용
    return speaker_separated.strip() if speaker_separated.strip() else full_transcript.strip()

def _extract_full_text(content: str) -> str:
    """전체 텍스트 섹션 추출"""
    lines = content.split('\n')
    full_transcript = ""
    in_full_text = False
    
    for line in lines:
        if "## 전체 텍스트" in line:
            in_full_text = True
            continue
        elif "## 화자별 발언" in line:
            break
        elif in_full_text and line.strip() and not line.startswith("#"):
            full_transcript += line + " "
    
    return full_transcript

def _extract_speaker_text(content: str) -> str:
    """화자별 발언 섹션 추출"""
    lines = content.split('\n')
    speaker_separated = ""
    in_speaker_section = False
    
    for line in lines:
        if "## 화자별 발언" in line:
            in_speaker_section = True
            continue
        elif in_speaker_section and line.strip():
            speaker_separated += line + "\\n"
    
    return speaker_separated

def _get_debug_info(content: str) -> dict:
    """디버깅 정보 생성"""
    full_transcript = _extract_full_text(content)
    speaker_separated = _extract_speaker_text(content)
    
    return {
        "full_transcript_length": len(full_transcript.strip()),
        "speaker_separated_length": len(speaker_separated.strip()), 
        "raw_content_length": len(content)
    }


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
        }
    }
    
    print("📋 테스트할 데이터를 선택하세요:")
    for key, config in test_configs.items():
        print(f"{key}. {config['name']}")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice in test_configs:
        return test_configs[choice]
    else:
        print("❌ 잘못된 선택입니다. 기본값으로 test_1on1.txt를 사용합니다.")
        return test_configs["1"]

def main():
    """메인 테스트 함수"""
    print("🚀 통합 LLM 분석 테스트 시작 (JSON 출력)")
    print("선택하세요:")
    print("1. OpenAI GPT 분석 테스트")
    print("2. Gemini 분석 테스트")
    print("3. 오디오 처리 및 전사 테스트")
    print("4. 통합 분석 파이프라인 테스트")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        _run_openai_test()
    elif choice == "2":
        _run_gemini_test()
    elif choice == "3":
        _run_audio_processing_test()
    elif choice == "4":
        _run_integrated_pipeline_test()
    else:
        print("❌ 잘못된 선택입니다. 1-4를 선택해주세요.")

def _run_openai_test():
    """OpenAI GPT 분석 테스트 실행 (JSON 전용)"""
    # 테스트 데이터 선택
    test_config = get_test_data_and_questions()
    transcript_file = test_config["file"]
    questions = test_config["questions"]
    
    print(f"\n📊 OpenAI GPT 분석 테스트 (JSON)")
    print(f"📄 선택된 데이터: {test_config['name']}")
    print(f"📄 전사 파일 로드 중: {transcript_file}")
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료")
    print(f"   - 전체 텍스트 길이: {len(stt_data['full_text'])}자")
    print(f"   - 사용할 질문 개수: {len(questions)}개")
    
    # OpenAI 분석기 초기화
    print("\n🔧 OpenAI GPT 모델 초기화 중...")
    try:
        analyzer = OpenAIMeetingAnalyzer()
        print("✅ OpenAI 분석기 초기화 완료")
    except Exception as e:
        print(f"❌ OpenAI 분석기 초기화 실패: {e}")
        return
    
    # STT 결과 분석 (JSON)
    print(f"\n🔄 OpenAI GPT로 분석 중 (JSON 형식)...")
    try:
        # STT 데이터에서 전사 텍스트 추출
        transcript_text = stt_data.get("transcript", "")
        if not transcript_text:
            print("❌ 전사 내용이 없습니다.")
            return
        
        result_text = analyzer.analyze_comprehensive(transcript_text, questions=questions)
        
        print_section("OpenAI GPT 분석 결과 (JSON)", result_text[:500] + "..." if len(result_text) > 500 else result_text)
        save_analysis_result(result_text, "openai")
        print(f"\n✅ OpenAI GPT 분석 테스트 완료!")
            
    except Exception as e:
        print(f"❌ OpenAI 분석 실패: {e}")

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
    
    # AudioProcessor 초기화
    try:
        processor = AudioProcessor()
        print("\n✅ AudioProcessor 초기화 완료")
    except Exception as e:
        print(f"❌ AudioProcessor 초기화 실패: {e}")
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
        audio_file = input("\nWAV 파일 경로를 입력하세요 (Enter: 기본 샘플 파일): ").strip()
        
        if not audio_file:
            audio_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/recording_20250731_175027.wav"
        
        if not os.path.exists(audio_file):
            print(f"❌ 오디오 파일이 존재하지 않습니다: {audio_file}")
            return
        
        print(f"📄 오디오 파일: {audio_file}")
        
        # 화자 정보 입력 받기
        print("\n화자 정보를 입력하시겠습니까? (y/n): ", end="")
        if input().strip().lower() == 'y':
            participants_info = _get_participants_info()
        else:
            participants_info = None
        
        # 전사 수행
        print("\n🔄 오디오 파일 전사 중 (화자 분리)...")
        transcription_result = processor.transcribe_existing_file(audio_file, participants_info)
    else:
        print("❌ 잘못된 선택입니다.")
        return
    
    # 전사 결과 확인
    if transcription_result.get("status") != "success":
        print(f"❌ 전사 실패: {transcription_result.get('message', '알 수 없는 오류')}")
        return
    
    transcript_text = transcription_result.get("transcript", "")
    print(f"\n✅ 전사 완료 (길이: {len(transcript_text)}자)")
    print_section("전사 결과 (화자 분리)", transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text)
    
    # Gemini로 분석
    print("\n🤖 Gemini로 회의 분석을 수행하시겠습니까? (y/n): ", end="")
    if input().strip().lower() == 'y':
        _analyze_with_gemini(transcript_text)
    
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

def _analyze_with_gemini(transcript_text):
    """Gemini로 전사 결과 분석"""
    print("\n🤖 Gemini 분석을 시작합니다...")
    
    # 질문 선택
    print("\n분석에 사용할 질문 세트를 선택하세요:")
    print("1. 기본 1-on-1 질문")
    print("2. 종합 미팅 질문")
    print("3. 커리어 개발 질문")
    print("4. 성과 개선 질문")
    print("5. 사용자 정의 질문")
    
    choice = input("선택 (1-5): ").strip()
    
    test_configs = get_test_data_and_questions()
    
    if choice == "1":
        questions = test_configs["1"]["questions"]
    elif choice == "2":
        questions = test_configs["2"]["questions"]
    elif choice == "3":
        questions = test_configs["3"]["questions"]
    elif choice == "4":
        questions = test_configs["4"]["questions"]
    elif choice == "5":
        print("\n질문을 입력하세요 (빈 줄 입력시 종료):")
        questions = []
        while True:
            q = input(f"질문 {len(questions)+1}: ").strip()
            if not q:
                break
            questions.append(q)
        if not questions:
            print("❌ 질문이 입력되지 않았습니다.")
            return
    else:
        print("❌ 잘못된 선택입니다. 기본 질문을 사용합니다.")
        questions = test_configs["1"]["questions"]
    
    print(f"\n선택된 질문 개수: {len(questions)}개")
    
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
        result_text = analyzer.analyze_comprehensive(transcript_text, questions=questions)
        
        print_section("Gemini 분석 결과 (JSON)", result_text[:500] + "..." if len(result_text) > 500 else result_text)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("data", exist_ok=True)
        
        # 전사 결과 저장
        transcript_file = os.path.join("data", f"transcript_{timestamp}.txt")
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"\n💾 전사 결과 저장: {transcript_file}")
        
        # 분석 결과 저장
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    # 통합 분석 결과 파일 저장 (JSON)
    result_filename = f"comprehensive_analysis_{timestamp}.json"
    result_filepath = os.path.join("data", result_filename)
    
    with open(result_filepath, "w", encoding="utf-8") as f:
        f.write(comprehensive_result)
    
    print(f"💾 통합 분석 결과 저장 (JSON): {result_filepath}")


if __name__ == "__main__":
    main()