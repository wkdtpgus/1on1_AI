#!/usr/bin/env python3
"""
STT와 LLM 분석 통합 테스트
"""

import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.transcription import STTProcessor
from src.models.recording import AudioRecorder
from src.models.stt_llm_analysis import MeetingAnalyzer
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class STTLLMIntegrationTest:
    """STT와 LLM 분석 통합 테스트 클래스"""
    
    def __init__(self):
        self.stt_processor = None
        self.audio_recorder = None
        self.meeting_analyzer = None
        self.data_dir = project_root / "data"
        
    def initialize_components(self):
        """모든 컴포넌트 초기화"""
        print("🚀 컴포넌트 초기화 중...")
        
        # API 키 확인
        assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not assemblyai_key:
            print("❌ ASSEMBLYAI_API_KEY가 설정되지 않았습니다.")
            return False
            
        if not openai_key:
            print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
            return False
        
        try:
            # 컴포넌트 초기화
            self.stt_processor = STTProcessor(api_key=assemblyai_key)
            self.audio_recorder = AudioRecorder()
            self.meeting_analyzer = MeetingAnalyzer(api_key=openai_key)
            
            print("✅ 모든 컴포넌트가 성공적으로 초기화되었습니다.")
            return True
            
        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            return False
    
    def test_with_existing_audio(self, audio_file: str):
        """기존 오디오 파일로 테스트"""
        print(f"\n📁 오디오 파일 테스트: {audio_file}")
        
        # 1. STT 전사
        print("\n1️⃣ STT 전사 시작...")
        stt_result = self.stt_processor.transcribe_audio(audio_file)
        
        if stt_result["status"] != "success":
            print(f"❌ STT 실패: {stt_result.get('message')}")
            return
        
        print("✅ STT 전사 완료")
        print(f"📝 전체 텍스트: {stt_result['full_text'][:100]}...")
        
        # 2. LLM 분석
        print("\n2️⃣ LLM 분석 시작...")
        
        # 화자 정보 포함 분석
        if stt_result.get("utterances"):
            analysis_result = self.meeting_analyzer.analyze_with_speakers(stt_result)
            print("👥 화자 정보를 포함한 분석 수행")
        else:
            analysis_result = self.meeting_analyzer.analyze_stt_result(stt_result)
            print("📄 전체 텍스트 분석 수행")
        
        print("\n✅ LLM 분석 완료")
        self.display_analysis_result(analysis_result)
        
        # 3. 결과 저장
        self.save_integrated_result(analysis_result)
        
    def test_with_recording(self):
        """새로운 녹음으로 테스트"""
        print("\n🎤 녹음 테스트 시작")
        
        # 녹음 시작
        input("Enter를 눌러 녹음을 시작하세요...")
        if self.audio_recorder.start_recording():
            print("🔴 녹음 중... (Enter를 눌러 중지)")
            input()
            
            # 녹음 중지
            audio_file = self.audio_recorder.stop_recording()
            if audio_file:
                print(f"✅ 녹음 완료: {audio_file}")
                self.test_with_existing_audio(audio_file)
            else:
                print("❌ 녹음 저장 실패")
        else:
            print("❌ 녹음 시작 실패")
    
    def display_analysis_result(self, result: dict):
        """분석 결과 표시"""
        print("\n" + "="*60)
        print("📊 분석 결과")
        print("="*60)
        
        analysis = result.get("analysis", {})
        
        # 제목
        print(f"\n📌 제목: {analysis.get('title', 'N/A')}")
        
        # 요약
        print("\n📝 핵심 포인트:")
        for i, point in enumerate(analysis.get('summary', []), 1):
            print(f"  {i}. {point}")
        
        # 화자 정보
        if result.get("utterances"):
            print(f"\n👥 화자 수: {len(set(u['speaker'] for u in result['utterances']))}")
            print(f"💬 총 발언 수: {len(result['utterances'])}")
        
        print("="*60)
    
    def save_integrated_result(self, result: dict):
        """통합 결과 저장"""
        output_dir = self.data_dir / "integrated_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 타임스탬프로 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"integrated_result_{timestamp}.json"
        filepath = output_dir / filename
        
        # JSON으로 저장
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 통합 결과 저장: {filepath}")
    
    def run_interactive_test(self):
        """대화형 테스트 실행"""
        if not self.initialize_components():
            return
        
        while True:
            print("\n" + "="*60)
            print("STT + LLM 통합 테스트")
            print("="*60)
            print("1. 새로운 녹음으로 테스트")
            print("2. 기존 오디오 파일로 테스트")
            print("3. 최근 STT 결과 재분석")
            print("q. 종료")
            
            choice = input("\n선택하세요: ").strip()
            
            if choice == "1":
                self.test_with_recording()
            
            elif choice == "2":
                # 오디오 파일 목록 표시
                audio_dir = self.data_dir / "raw_audio"
                if audio_dir.exists():
                    audio_files = list(audio_dir.glob("*.wav"))
                    if audio_files:
                        print("\n📁 사용 가능한 오디오 파일:")
                        for i, f in enumerate(audio_files[-5:], 1):
                            print(f"  {i}. {f.name}")
                        
                        idx = input("\n파일 번호를 선택하세요: ").strip()
                        try:
                            file_idx = int(idx) - 1
                            if 0 <= file_idx < len(audio_files[-5:]):
                                self.test_with_existing_audio(str(audio_files[-5:][file_idx]))
                        except ValueError:
                            print("❌ 잘못된 입력입니다.")
                    else:
                        print("❌ 오디오 파일이 없습니다.")
                else:
                    print("❌ 오디오 디렉토리가 없습니다.")
            
            elif choice == "3":
                # 최근 STT 결과 재분석
                stt_dir = self.data_dir / "stt_transcripts"
                if stt_dir.exists():
                    json_files = list(stt_dir.glob("transcription_*.json"))
                    if json_files:
                        latest_file = max(json_files, key=os.path.getctime)
                        
                        with open(latest_file, "r", encoding="utf-8") as f:
                            stt_result = json.load(f)
                        
                        print(f"\n📁 최근 STT 결과 로드: {latest_file.name}")
                        
                        # LLM 분석
                        print("2️⃣ LLM 재분석 시작...")
                        if stt_result.get("utterances"):
                            analysis_result = self.meeting_analyzer.analyze_with_speakers(stt_result)
                        else:
                            analysis_result = self.meeting_analyzer.analyze_stt_result(stt_result)
                        
                        self.display_analysis_result(analysis_result)
                        self.save_integrated_result(analysis_result)
                    else:
                        print("❌ STT 결과 파일이 없습니다.")
                else:
                    print("❌ STT 결과 디렉토리가 없습니다.")
            
            elif choice.lower() == "q":
                print("👋 테스트를 종료합니다.")
                break
            
            else:
                print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    test = STTLLMIntegrationTest()
    test.run_interactive_test()