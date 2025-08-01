#!/usr/bin/env python3
"""
STT 모듈 대화형 테스트 스크립트
키보드 입력으로 녹음 제어
"""

import os
import sys
import threading
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent  # tests 폴더에서 상위 디렉토리로
sys.path.insert(0, str(project_root))

# 필요한 패키지 확인
try:
    import sounddevice
    import soundfile
    import assemblyai
    import numpy
    from dotenv import load_dotenv
    print("✅ 모든 필수 패키지가 설치되어 있습니다.")
except ImportError as e:
    print(f"❌ 필수 패키지가 누락되었습니다: {e}")
    print("다음 명령어로 설치해주세요:")
    print("pip install sounddevice soundfile assemblyai numpy scipy python-dotenv")
    sys.exit(1)

from src.services.stt_processor import STTProcessor


class InteractiveSTTTest:
    """대화형 STT 테스트 클래스"""
    
    def __init__(self):
        self.stt = None
        self.is_recording = False
        self.audio_files = []
        self.audio_dir = project_root / "data" / "raw_audio"
        
    def initialize_stt(self):
        """STT 프로세서 초기화"""
        # API 키 확인
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            print("❌ ASSEMBLYAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("   .env 파일에 ASSEMBLYAI_API_KEY를 설정해주세요.")
            return False
        
        try:
            self.stt = STTProcessor(api_key=api_key)
            print("✅ STT 프로세서 초기화 성공")
            
            # 기존 오디오 파일 로드
            self.load_existing_audio_files()
            
            return True
        except Exception as e:
            print(f"❌ STT 프로세서 초기화 실패: {e}")
            return False
    
    def start_recording(self):
        """녹음 시작"""
        if self.is_recording:
            print("⚠️ 이미 녹음 중입니다.")
            return
        
        try:
            result = self.stt.start_recording()
            if result["status"] == "recording":
                self.is_recording = True
                print("🎤 녹음이 시작되었습니다. 말씀해 주세요...")
                print("   (중지하려면 's' 키를 눌러주세요)")
            else:
                print(f"❌ 녹음 시작 실패: {result['message']}")
        except Exception as e:
            print(f"❌ 녹음 시작 오류: {e}")
    
    def stop_recording(self):
        """녹음 중지"""
        if not self.is_recording:
            print("⚠️ 현재 녹음 중이 아닙니다.")
            return
        
        try:
            result = self.stt.stop_recording()
            self.is_recording = False
            
            if result["status"] == "stopped":
                audio_file = result["audio_file"]
                self.audio_files.append(audio_file)
                print(f"✅ 녹음이 중지되었습니다.")
                print(f"📁 저장된 파일: {audio_file}")
                
                # 파일 크기 확인
                if os.path.exists(audio_file):
                    file_size = os.path.getsize(audio_file) / 1024  # KB
                    print(f"📏 파일 크기: {file_size:.1f} KB")
                
                return audio_file
            else:
                print(f"❌ 녹음 중지 실패: {result['message']}")
                return None
        except Exception as e:
            print(f"❌ 녹음 중지 오류: {e}")
            self.is_recording = False
            return None
    
    def transcribe_latest(self):
        """최근 녹음된 파일 전사"""
        # 파일 목록 다시 로드
        self.load_existing_audio_files()
        
        if not self.audio_files:
            print("⚠️ 전사할 오디오 파일이 없습니다. 먼저 녹음을 해주세요.")
            return
        
        latest_file = self.audio_files[-1]
        print(f"🔄 전사 시작: {latest_file}")
        print("   (AssemblyAI 서버에서 처리 중... 잠시만 기다려주세요)")
        
        try:
            result = self.stt.transcribe_audio(latest_file)
            self.display_transcription_result(result)
        except Exception as e:
            print(f"❌ 전사 오류: {e}")
    
    def transcribe_all(self):
        """모든 녹음된 파일 전사"""
        # 파일 목록 다시 로드
        self.load_existing_audio_files()
        
        if not self.audio_files:
            print("⚠️ 전사할 오디오 파일이 없습니다.")
            return
        
        print(f"🔄 총 {len(self.audio_files)}개 파일 전사 시작")
        
        for i, audio_file in enumerate(self.audio_files, 1):
            print(f"\n📁 파일 {i}/{len(self.audio_files)}: {audio_file}")
            try:
                result = self.stt.transcribe_audio(audio_file)
                print(f"✅ 파일 {i} 전사 완료")
                if result["status"] == "success":
                    print(f"📝 텍스트: {result['full_text'][:100]}{'...' if len(result['full_text']) > 100 else ''}")
            except Exception as e:
                print(f"❌ 파일 {i} 전사 실패: {e}")
    
    def display_transcription_result(self, result):
        """전사 결과 표시"""
        print("\n" + "="*60)
        print("📋 전사 결과")
        print("="*60)
        
        if result["status"] == "success":
            print("✅ 전사 성공!")
            print(f"📝 텍스트: {result.get('full_text', 'N/A')}")
            
            # 화자 분리 결과
            if result.get('utterances'):
                print(f"\n👥 화자 분리 결과 ({len(result['utterances'])}개 발언):")
                for i, utterance in enumerate(result['utterances'][:5]):  # 처음 5개만 표시
                    print(f"  {i+1}. 참석자 {utterance['speaker']}번 ({utterance['start']:.1f}s-{utterance['end']:.1f}s)")
                    text_preview = utterance['text'][:80] + "..." if len(utterance['text']) > 80 else utterance['text']
                    print(f"     \"{text_preview}\"")
                
                if len(result['utterances']) > 5:
                    print(f"     ... 및 {len(result['utterances']) - 5}개 더")
            
            # 저장된 파일 정보
            outputs_dir = project_root / "data" / "stt_transcripts"
            if outputs_dir.exists():
                json_files = list(outputs_dir.glob("transcription_*.json"))
                txt_files = list(outputs_dir.glob("transcription_*.txt"))
                if json_files or txt_files:
                    print(f"\n📁 저장된 파일:")
                    for file in sorted(json_files + txt_files, key=os.path.getctime, reverse=True)[:2]:
                        print(f"   - {file}")
        else:
            print(f"❌ 전사 실패: {result.get('message', 'Unknown error')}")
    
    def load_existing_audio_files(self):
        """기존 오디오 파일들을 로드"""
        if self.audio_dir.exists():
            # .wav 파일들을 날짜순으로 정렬하여 로드
            wav_files = sorted(self.audio_dir.glob("recording_*.wav"), key=os.path.getctime)
            self.audio_files = [str(f) for f in wav_files]
            
            if self.audio_files:
                print(f"📁 기존 오디오 파일 {len(self.audio_files)}개를 불러왔습니다.")
            else:
                print("📁 기존 오디오 파일이 없습니다.")
    
    def list_recordings(self):
        """녹음된 파일 목록 표시"""
        # 파일 목록 다시 로드
        self.load_existing_audio_files()
        
        if not self.audio_files:
            print("📁 녹음된 파일이 없습니다.")
            return
        
        print(f"\n📁 녹음된 파일 목록 ({len(self.audio_files)}개):")
        for i, audio_file in enumerate(self.audio_files, 1):
            if os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file) / 1024  # KB
                # 파일명만 표시 (전체 경로 대신)
                file_name = os.path.basename(audio_file)
                print(f"  {i}. {file_name} ({file_size:.1f} KB)")
            else:
                print(f"  {i}. {os.path.basename(audio_file)} (파일 없음)")
    
    def show_help(self):
        """도움말 표시"""
        print("\n" + "="*60)
        print("🔧 사용 가능한 명령어")
        print("="*60)
        print("r, record  : 녹음 시작")
        print("s, stop    : 녹음 중지")
        print("t, trans   : 최근 파일 전사")
        print("a, all     : 모든 파일 전사")
        print("l, list    : 녹음 파일 목록")
        print("h, help    : 도움말")
        print("q, quit    : 종료")
        print("="*60)
    
    def run(self):
        """메인 실행 루프"""
        print("🚀 STT 대화형 테스트 시작")
        print("="*60)
        
        # STT 초기화
        if not self.initialize_stt():
            return
        
        # 도움말 표시
        self.show_help()
        
        while True:
            try:
                # 현재 상태 표시
                status = "🎤 녹음 중" if self.is_recording else "⏹️ 대기 중"
                command = input(f"\n[{status}] 명령어를 입력하세요 (h: 도움말): ").strip().lower()
                
                if command in ['r', 'record']:
                    self.start_recording()
                
                elif command in ['s', 'stop']:
                    audio_file = self.stop_recording()
                    if audio_file:
                        # 녹음 중지 후 전사 여부 묻기
                        trans_input = input("🤔 바로 전사하시겠습니까? (y/n): ").strip().lower()
                        if trans_input in ['y', 'yes', '']:
                            self.transcribe_latest()
                
                elif command in ['t', 'trans', 'transcribe']:
                    self.transcribe_latest()
                
                elif command in ['a', 'all']:
                    self.transcribe_all()
                
                elif command in ['l', 'list']:
                    self.list_recordings()
                
                elif command in ['h', 'help']:
                    self.show_help()
                
                elif command in ['q', 'quit', 'exit']:
                    if self.is_recording:
                        print("⚠️ 녹음 중입니다. 먼저 중지하고 종료합니다.")
                        self.stop_recording()
                    print("👋 테스트를 종료합니다.")
                    break
                
                elif command == '':
                    continue
                
                else:
                    print(f"❓ 알 수 없는 명령어: '{command}'. 'h'를 입력하여 도움말을 확인하세요.")
            
            except KeyboardInterrupt:
                print("\n\n⚠️ Ctrl+C 감지됨.")
                if self.is_recording:
                    print("🛑 녹음을 중지합니다...")
                    self.stop_recording()
                print("👋 테스트를 종료합니다.")
                break
            
            except Exception as e:
                print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    test = InteractiveSTTTest()
    test.run()