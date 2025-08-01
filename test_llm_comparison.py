"""
LLM 모델 비교 테스트 스크립트
OpenAI GPT vs Google Vertex AI Gemini 성능 및 결과 품질 비교
"""

import os
import json
from datetime import datetime
from src.models.multi_llm_analyzer import MultiLLMAnalyzer

def load_sample_transcript(file_path: str) -> dict:
    """실제 전사 파일에서 STT 데이터 로드"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 전체 전사 내용 추출
        lines = content.split('\n')
        full_text = ""
        
        # 전체 전사 내용 찾기
        in_full_text = False
        
        for line in lines:
            if "## 전체 전사 내용" in line:
                in_full_text = True
                continue
            elif "## 화자별 발언" in line:
                in_full_text = False
                break
            elif in_full_text and line.strip() and not line.startswith("#"):
                full_text += line + " "
        
        return {
            "status": "success",
            "full_text": full_text.strip(),
            "timestamp": "2025-07-28T16:44:07"
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
    
def main():
    """메인 테스트 함수"""
    print("🚀 LLM 모델 비교 테스트 시작")
    print(f"📊 테스트 대상: OpenAI GPT vs Google Vertex AI Gemini")
    
    # 실제 전사 파일 로드
    transcript_file = "/Users/kimjoonhee/Documents/Orblit_1on1_AI/AssemblyAI_회의_전사_결과 복사본.txt"
    
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
    
    print("\n✅ 테스트 완료!")
    


if __name__ == "__main__":
    main()