"""
LLM 모델 비교 테스트 스크립트
OpenAI GPT vs Google Vertex AI Gemini 성능 및 결과 품질 비교
"""

import os
import json
from datetime import datetime
from typing import List
from langchain_google_vertexai import ChatVertexAI
from langchain.schema import HumanMessage
from src.models.multi_llm_analyzer import MultiLLMAnalyzer
from src.prompts.stt_llm_prompts import QA_EXTRACTION_PROMPT
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
        
        # 3가지 형태로 텍스트 추출
        lines = content.split('\n')
        
        # 1. 전체 전사 텍스트 (기존)
        full_transcript = ""
        in_full_text = False
        
        # 2. 화자별 발언만 (화자 정보 포함)
        speaker_separated = ""
        in_speaker_section = False
        
        # 3. 전체 파일 내용 (원본 그대로)
        raw_content = content
        
        for line in lines:
            # 전체 텍스트 섹션 파싱
            if "## 전체 텍스트" in line:
                in_full_text = True
                continue
            elif "## 화자별 발언" in line:
                in_full_text = False
                in_speaker_section = True
                continue
            elif in_full_text and line.strip() and not line.startswith("#"):
                full_transcript += line + " "
            
            # 화자별 발언 섹션 파싱
            elif in_speaker_section and line.strip():
                speaker_separated += line + "\n"
        
        # 파일 형식에 따른 텍스트 선택
        if file_path.endswith("test_1on1.txt"):
            # test_1on1.txt는 일반 대화 형식이므로 전체 내용 사용
            selected_text = raw_content.strip()
        else:
            # 기존 전사 파일 형식은 화자별 발언 사용
            selected_text = speaker_separated.strip() if speaker_separated.strip() else full_transcript.strip()
        
        return {
            "status": "success",
            "full_text": selected_text,
            "timestamp": "2025-07-28T16:44:07",
            # 디버깅용 정보
            "options": {
                "full_transcript_length": len(full_transcript.strip()),
                "speaker_separated_length": len(speaker_separated.strip()), 
                "raw_content_length": len(raw_content)
            }
        }
        
    except Exception as e:
        print(f"❌ 파일 로드 오류: {e}")
        return None


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


def test_qa_extraction(questions: List[str], transcript_file: str):
    """Q&A 추출 테스트 함수"""
    print("\n🔍 Q&A 추출 테스트 시작")
    print(f"📋 질문 수: {len(questions)}")
    
    # 전사 파일 로드
    stt_data = load_sample_transcript(transcript_file)
    if not stt_data:
        print("❌ 전사 파일을 로드할 수 없습니다.")
        return
    
    transcript = stt_data['full_text']
    print(f"📄 전사 내용 길이: {len(transcript)}자")
    
    # Vertex AI 초기화
    try:
        llm = ChatVertexAI(
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
            model_name=VERTEX_AI_MODEL,
            temperature=VERTEX_AI_TEMPERATURE,
            max_output_tokens=VERTEX_AI_MAX_TOKENS
        )
        print("✅ Vertex AI Gemini 모델 초기화 완료")
    except Exception as e:
        print(f"❌ LLM 초기화 오류: {e}")
        return
    
    # 질문 리스트를 텍스트로 변환
    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    # 프롬프트 생성
    prompt = QA_EXTRACTION_PROMPT.format(
        questions=questions_text,
        transcript=transcript
    )
    
    # Q&A 추출 실행
    print("\n🔄 Q&A 추출 중...")
    try:
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        qa_result = response.content
        
        # 결과 출력
        print_section("Q&A 추출 결과", qa_result)
        
        # 결과 저장
        save_qa_result(qa_result, questions, len(transcript))
        
        return qa_result
        
    except Exception as e:
        print(f"❌ Q&A 추출 오류: {e}")
        return None


def save_qa_result(qa_result: str, questions: List[str], transcript_length: int):
    """Q&A 결과를 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # data 디렉토리가 없으면 생성
    os.makedirs("data", exist_ok=True)
    
    # Q&A 결과 파일 저장
    qa_filename = f"qa_result_{timestamp}.md"
    qa_filepath = os.path.join("data", qa_filename)
    
    with open(qa_filepath, "w", encoding="utf-8") as f:
        f.write("# Q&A 질문별 답변 정리 결과\n\n")
        f.write(f"생성 시간: {timestamp}\n")
        f.write(f"총 질문 수: {len(questions)}\n")
        f.write(f"전사 내용 길이: {transcript_length}자\n\n")
        f.write("---\n\n")
        f.write("## 질문 목록\n")
        for i, q in enumerate(questions, 1):
            f.write(f"{i}. {q}\n")
        f.write("\n---\n\n")
        f.write("## Q&A 결과\n\n")
        f.write(qa_result)
        f.write(f"\n\n---\n\n")
        f.write("## 분석 정보\n")
        f.write(f"- 모델: {VERTEX_AI_MODEL}\n")
        f.write(f"- 생성 시간: {timestamp}\n")
    
    print(f"💾 Q&A 결과 저장: {qa_filepath}")


def main():
    """메인 테스트 함수"""
    print("🚀 LLM 테스트 시작")
    print("선택하세요:")
    print("1. LLM 모델 비교 테스트 (OpenAI vs Gemini)")
    print("2. Q&A 질문별 답변 추출 테스트")
    
    choice = input("\n선택 (1 또는 2): ").strip()
    
    # 실제 전사 파일 경로
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/test_1on1.txt"
    
    if choice == "1":
        # 기존 LLM 비교 테스트
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
        
    elif choice == "2":
        # Q&A 테스트
        print("\n📋 Q&A 질문별 답변 추출 테스트")
        
        # 1on1 미팅 질문들
        sample_questions = [
            "2분기 성과 검토와 3분기 계획은?",
            "어려웠던 점이나 아쉬웠던 부분은?",
            "극복한 방법",
            "구체적인 일정이나 마일스톤",
            "올해 어떤 목표를 세웠는가?",
            "최근 개인적인 목표와 관심사는?",
            "궁금한 점이나 건의사항"
        ]
        
        print("📝 테스트 질문 목록:")
        for i, q in enumerate(sample_questions, 1):
            print(f"   {i}. {q}")
        
        print("\n💡 질문을 수정하려면 코드에서 sample_questions 리스트를 편집하세요.")
        
        # Q&A 추출 실행
        qa_result = test_qa_extraction(sample_questions, transcript_file)
        
        if qa_result:
            print("\n✅ Q&A 추출 테스트 완료!")
        else:
            print("\n❌ Q&A 추출 테스트 실패!")
    
    else:
        print("❌ 잘못된 선택입니다. 1 또는 2를 선택해주세요.")
    


if __name__ == "__main__":
    main()