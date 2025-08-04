"""
LLM 모델 비교 테스트 스크립트
OpenAI GPT vs Google Vertex AI Gemini 성능 및 결과 품질 비교
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

from langchain_google_vertexai import ChatVertexAI
from langchain.schema import HumanMessage
from src.models.multi_llm_analyzer import MultiLLMAnalyzer
from src.models.stt_llm_analysis import MeetingAnalyzer
from src.prompts.stt_llm_prompts import COMPREHENSIVE_MEETING_ANALYSIS_PROMPT
from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
    VERTEX_AI_MAX_TOKENS
)

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
            "full_text": selected_text,
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


def save_comparison_results(results: dict):
    """비교 결과를 개별 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    model_comparison = results.get("model_comparison", {})
    
    # OpenAI 결과 파일 저장
    if "openai_analysis" in model_comparison:
        openai_filename = f"openai_gpt_result_{timestamp}.md"
        openai_filepath = os.path.join("data", openai_filename)
        
        with open(openai_filepath, "w", encoding="utf-8") as f:
            f.write("# OpenAI GPT 회의 분석 결과\n\n")
            f.write(f"생성 시간: {timestamp}\n\n")
            f.write("---\n\n")
            f.write(model_comparison["openai_analysis"])
        
        print(f"💾 OpenAI GPT 결과 저장: {openai_filepath}")
    
    # Vertex AI 결과 파일 저장
    if "vertexai_analysis" in model_comparison:
        vertexai_filename = f"vertexai_gemini_result_{timestamp}.md"
        vertexai_filepath = os.path.join("data", vertexai_filename)
        
        with open(vertexai_filepath, "w", encoding="utf-8") as f:
            f.write("# Google Vertex AI Gemini 회의 분석 결과\n\n")
            f.write(f"생성 시간: {timestamp}\n\n")
            f.write("---\n\n")
            f.write(model_comparison["vertexai_analysis"])
        
        print(f"💾 Vertex AI Gemini 결과 저장: {vertexai_filepath}")




def main():
    """메인 테스트 함수"""
    print("🚀 LLM 테스트 시작")
    print("선택하세요:")
    print("1. LLM 모델 비교 테스트 (OpenAI vs Gemini)")
    print("2. 통합 1on1 분석 테스트 (요약+피드백+Q&A)")
    
    choice = input("\n선택 (1 또는 2): ").strip()
    
    if choice == "1":
        _run_llm_comparison_test()
    elif choice == "2":
        _run_comprehensive_analysis_test()
    else:
        print("❌ 잘못된 선택입니다. 1 또는 2를 선택해주세요.")

def _run_llm_comparison_test():
    """LLM 비교 테스트 실행"""
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/[리버스마운틴] 서비스 관련 미팅 - 2025_08_01 08_49 KST - Gemini가 작성한 회의록.txt"
    
    print(f"\n📊 테스트 대상: OpenAI GPT vs Google Vertex AI Gemini")
    print(f"📄 전사 파일 로드 중: {transcript_file}")
    
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    print(f"✅ 전사 데이터 로드 완료")
    print(f"   - 전체 텍스트 길이: {len(stt_data['full_text'])}자")
    
    # MultiLLMAnalyzer 초기화
    print("\n🔧 LLM 모델 초기화 중...")
    analyzer = MultiLLMAnalyzer()
    
    # STT 결과를 두 모델로 분석
    print("\n🔄 STT 결과 분석 중...")
    comparison_results = analyzer.analyze_stt_with_comparison(stt_data)
    
    # 결과 출력
    model_comparison = comparison_results.get("model_comparison", {})
    
    if "error" in model_comparison:
        print(f"❌ 오류: {model_comparison['error']}")
        return

    # 결과 저장
    save_comparison_results(comparison_results)
    print("\n✅ LLM 비교 테스트 완료!")

def _run_comprehensive_analysis_test():
    """통합 1on1 분석 테스트 실행"""
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/[리버스마운틴] 서비스 관련 미팅 - 2025_08_01 08_49 KST - Gemini가 작성한 회의록.txt"
    
    print("\n🎯 통합 1on1 분석 테스트 (요약+피드백+Q&A)")
    print(f"📄 전사 파일: {transcript_file}")
    
    # 전사 파일 로드
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    transcript = stt_data['full_text']
    print(f"✅ 전사 데이터 로드 완료 (길이: {len(transcript)}자)")
    
    # MeetingAnalyzer 초기화
    try:
        analyzer = MeetingAnalyzer()
        print("✅ MeetingAnalyzer 초기화 완료")
    except Exception as e:
        print(f"❌ 분석기 초기화 실패: {e}")
        return
    
    # 통합 분석 실행
    print("\n🔄 통합 1on1 분석 중...")
    try:
        comprehensive_result = analyzer.analyze_comprehensive(transcript)
        
        # 결과 출력
        print_section("1on1 종합 분석 결과", comprehensive_result)
        
        # 결과 저장
        save_comprehensive_result(comprehensive_result, len(transcript))
        
        print("\n✅ 통합 1on1 분석 테스트 완료!")
        
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
        f.write(f"- 사용 프롬프트: COMPREHENSIVE_MEETING_ANALYSIS_PROMPT\n")
        f.write(f"- 포함 기능: 회의 요약 + 매니저 피드백 + Q&A 답변\n")
    
    print(f"💾 통합 분석 결과 저장: {result_filepath}")
    


if __name__ == "__main__":
    main()