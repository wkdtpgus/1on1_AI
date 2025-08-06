"""
통합 LLM 분석 테스트 스크립트
- OpenAI GPT 및 Gemini 독립 테스트
- 오디오 처리 및 전사 테스트
- 통합 분석 테스트
"""

import os
import sys
import json
from datetime import datetime
from typing import List
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.llm_analysis import OpenAIMeetingAnalyzer, GeminiMeetingAnalyzer
from src.models.audio_processing import AudioProcessor
from src.prompts.stt_llm_prompts import MEETING_ANALYST_SYSTEM_PROMPT, COMPREHENSIVE_ANALYSIS_USER_PROMPT

def load_sample_transcript(file_path: str) -> dict:
    """실제 전사 파일에서 STT 데이터 로드"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 파일 형식에 따른 텍스트 추출
        if file_path.endswith("test_1on1.txt"):
            selected_text = content.strip()
        elif "Gemini가 작성한 회의록.txt" in file_path:
            # Gemini 회의록 파일은 전체 내용을 그대로 사용
            selected_text = content.strip() 
        else:
            selected_text = _extract_transcript_text(content)
        
        return {
            "status": "success",
            "transcript": selected_text,  # analyze_stt_result가 기대하는 키 이름
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
            speaker_separated += line + "\n"
    
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
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)
    print(content)


def save_analysis_result(result: str, model_type: str):
    """분석 결과를 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    if model_type == "openai":
        filename = f"openai_gpt_result_{timestamp}.md"
        title = "OpenAI GPT 회의 분석 결과"
    elif model_type == "gemini":
        filename = f"vertexai_gemini_result_{timestamp}.md"
        title = "Google Vertex AI Gemini 회의 분석 결과"
    else:
        filename = f"analysis_result_{timestamp}.md"
        title = "회의 분석 결과"
    
    filepath = os.path.join("data", filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"생성 시간: {timestamp}\n\n")
        f.write("---\n\n")
        f.write(result)
    
    print(f"💾 {title} 저장: {filepath}")




def main():
    """메인 테스트 함수"""
    print("🚀 통합 LLM 분석 테스트 시작")
    print("선택하세요:")
    print("1. OpenAI GPT 분석 테스트")
    print("2. Gemini 분석 테스트 (기본)")
    print("3. 오디오 처리 및 전사 테스트")
    print("4. 통합 분석 파이프라인 테스트")
    
    choice = input("\n선택 (1, 2, 3, 또는 4): ").strip()
    
    if choice == "1":
        _run_openai_test()
    elif choice == "2":
        _run_gemini_test()
    elif choice == "3":
        _run_audio_processing_test()
    elif choice == "4":
        _run_integrated_pipeline_test()
    else:
        print("❌ 잘못된 선택입니다. 1, 2, 3, 또는 4를 선택해주세요.")

def _run_openai_test():
    """OpenAI GPT 분석 테스트 실행"""
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_1on1.txt"
    
    print(f"\n📊 OpenAI GPT 분석 테스트")
    print(f"📄 전사 파일 로드 중: {transcript_file}")
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료")
    print(f"   - 전체 텍스트 길이: {len(stt_data['full_text'])}자")
    
    # OpenAI 분석기 초기화
    print("\n🔧 OpenAI GPT 모델 초기화 중...")
    try:
        analyzer = OpenAIMeetingAnalyzer()
        print("✅ OpenAI 분석기 초기화 완료")
    except Exception as e:
        print(f"❌ OpenAI 분석기 초기화 실패: {e}")
        return
    
    # STT 결과 분석
    print("\n🔄 OpenAI GPT로 분석 중...")
    try:
        analysis_result = analyzer.analyze_stt_result(stt_data)
        
        if "analysis" in analysis_result:
            result_text = analysis_result["analysis"]["comprehensive_analysis"]
            print_section("OpenAI GPT 분석 결과", result_text)
            save_analysis_result(result_text, "openai")
            print("\n✅ OpenAI GPT 분석 테스트 완료!")
        else:
            print("❌ 분석 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ OpenAI 분석 실패: {e}")

def _run_gemini_test():
    """Gemini 분석 테스트 실행 (기본)"""
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_1on1.txt"
    
    print(f"\n📊 Gemini 분석 테스트 (기본 모델)")
    print(f"📄 전사 파일 로드 중: {transcript_file}")
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료")
    print(f"   - 전체 텍스트 길이: {len(stt_data['full_text'])}자")
    
    # Gemini 분석기 초기화
    print("\n🔧 Gemini 모델 초기화 중...")
    try:
        analyzer = GeminiMeetingAnalyzer()
        print("✅ Gemini 분석기 초기화 완료")
    except Exception as e:
        print(f"❌ Gemini 분석기 초기화 실패: {e}")
        return
    
    # STT 결과 분석
    print("\n🔄 Gemini로 분석 중...")
    try:
        analysis_result = analyzer.analyze_stt_result(stt_data)
        
        if "analysis" in analysis_result:
            result_text = analysis_result["analysis"]["comprehensive_analysis"]
            print_section("Gemini 분석 결과", result_text)
            save_analysis_result(result_text, "gemini")
            print("\n✅ Gemini 분석 테스트 완료!")
        else:
            print("❌ 분석 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ Gemini 분석 실패: {e}")

def _run_audio_processing_test():
    """오디오 처리 및 전사 테스트"""
    print("\n🎵 오디오 처리 및 전사 테스트")
    
    # 기존 오디오 파일 테스트
    audio_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/recording_20250731_175027.wav"
    
    if not os.path.exists(audio_file):
        print(f"❌ 오디오 파일이 존재하지 않습니다: {audio_file}")
        return
    
    print(f"📄 오디오 파일: {audio_file}")
    
    # AudioProcessor 초기화
    try:
        processor = AudioProcessor()
        print("✅ AudioProcessor 초기화 완료")
    except Exception as e:
        print(f"❌ AudioProcessor 초기화 실패: {e}")
        return
    
    # 기존 파일 전사
    print("\n🔄 오디오 파일 전사 중...")
    try:
        transcription_result = processor.transcribe_existing_file(audio_file)
        
        if transcription_result.get("status") == "success":
            transcript_text = transcription_result.get("transcript", "")
            print(f"✅ 전사 완료 (길이: {len(transcript_text)}자)")
            print_section("전사 결과", transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text)
            print("\n✅ 오디오 처리 테스트 완료!")
        else:
            print(f"❌ 전사 실패: {transcription_result.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"❌ 오디오 처리 실패: {e}")

def _run_integrated_pipeline_test():
    """통합 분석 파이프라인 테스트 - 질문 리스트 기반 분석"""
    print("\n🔄 통합 분석 파이프라인 테스트 (질문 기반)")
    
    # 샘플 전사 데이터 로드
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_1on1.txt"
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료 (길이: {len(stt_data['full_text'])}자)")
    
    # 고정된 질문 리스트 (여기서 직접 수정)
    questions = [
        "이분기에 달성한 주요 성과는 무엇인가요?",
        "프로젝트 진행 중 어떤 어려움이 있었나요?",
        "3분기에 계획된 새로운 프로젝트는 무엇인가요?",
        "개인적인 성장 목표는 무엇인가요?",
        "어떤 지원이나 리소스가 필요한가요?"
    ]
    

    # Gemini 분석기로 통합 분석
    try:
        analyzer = GeminiMeetingAnalyzer()
        print("\n✅ Gemini 분석기 초기화 완료")
        
        analysis_result = analyzer.analyze_stt_result(stt_data, questions=questions)
        
        if "analysis" in analysis_result:
            result_text = analysis_result["analysis"]["comprehensive_analysis"]
            print_section("통합 분석 결과", result_text)            
            save_comprehensive_result(result_text, len(stt_data['full_text']))
            print("✅ 통합 분석 파이프라인 테스트 완료!")
        else:
            print("❌ 분석 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ 통합 분석 실패: {e}")


def save_comprehensive_result(comprehensive_result: str, transcript_length: int):
    """통합 분석 결과를 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    # 통합 분석 결과 파일 저장
    result_filename = f"comprehensive_analysis_{timestamp}.md"
    result_filepath = os.path.join("data", result_filename)
    
    with open(result_filepath, "w", encoding="utf-8") as f:
        f.write("# 1on1 종합 분석 결과\n\n")
        f.write(f"생성 시간: {timestamp}\n")
        f.write(f"전사 내용 길이: {transcript_length}자\n\n")
        f.write("---\n\n")
        f.write(comprehensive_result)
        f.write(f"\n\n---\n\n")
        f.write("## 분석 정보\n")
        f.write(f"- 분석 시간: {timestamp}\n")
        f.write(f"- 사용 프롬프트: MEETING_ANALYST_SYSTEM_PROMPT + COMPREHENSIVE_ANALYSIS_USER_PROMPT\n")
        f.write(f"- 포함 기능: 회의 요약 + 매니저 피드백 + Q&A 답변\n")
    
    print(f"💾 통합 분석 결과 저장: {result_filepath}")


# 이전 함수는 통합 테스트로 대체됨


if __name__ == "__main__":
    main()