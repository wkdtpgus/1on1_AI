import assemblyai as aai
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Import config settings
from src.config.config import (
    ASSEMBLYAI_API_KEY,
    ASSEMBLYAI_SPEECH_MODEL,
    ASSEMBLYAI_LANGUAGE,
    ASSEMBLYAI_PUNCTUATE,
    ASSEMBLYAI_FORMAT_TEXT,
    ASSEMBLYAI_DISFLUENCIES,
    ASSEMBLYAI_SPEAKER_LABELS,
    ASSEMBLYAI_LANGUAGE_DETECTION,
    ASSEMBLYAI_WORD_BOOST,
    ASSEMBLYAI_BOOST_PARAM,
    ASSEMBLYAI_SPEAKERS_EXPECTED,
    OUTPUT_DIR
)


class STTProcessor:
    """AssemblyAI를 사용한 Speech-to-Text 처리 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        # API 키 설정
        self.api_key = api_key or ASSEMBLYAI_API_KEY or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("AssemblyAI API key is required")
        
        # AssemblyAI 설정
        aai.settings.api_key = self.api_key
    
    def transcribe_audio(self, audio_file: str) -> Dict[str, Any]:
        """AssemblyAI를 사용하여 오디오 파일을 텍스트로 변환"""
        
        if not os.path.exists(audio_file):
            return {
                "status": "error",
                "message": f"오디오 파일을 찾을 수 없습니다: {audio_file}",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # AssemblyAI 전사 설정 + 화자 분리 강화
            config = aai.TranscriptionConfig(
                speech_model=getattr(aai.SpeechModel, ASSEMBLYAI_SPEECH_MODEL, aai.SpeechModel.best),
                language_code=ASSEMBLYAI_LANGUAGE,
                punctuate=ASSEMBLYAI_PUNCTUATE,
                format_text=ASSEMBLYAI_FORMAT_TEXT,
                disfluencies=ASSEMBLYAI_DISFLUENCIES,
                speaker_labels=ASSEMBLYAI_SPEAKER_LABELS,
                language_detection=ASSEMBLYAI_LANGUAGE_DETECTION,
                # 화자 분리 강화 설정
                speakers_expected=ASSEMBLYAI_SPEAKERS_EXPECTED  # 예상 화자 수 지정
            )
            
            # 특정 단어 인식 강화 설정
            if ASSEMBLYAI_WORD_BOOST:
                config.word_boost = ASSEMBLYAI_WORD_BOOST
                config.boost_param = ASSEMBLYAI_BOOST_PARAM
            
            transcriber = aai.Transcriber(config=config)
            
            # 전사 시작
            transcript = transcriber.transcribe(audio_file)
            
            # 전사 상태 확인
            while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
                time.sleep(5)
            
            if transcript.status == aai.TranscriptStatus.error:
                return {
                    "status": "error",
                    "message": f"전사 실패: {transcript.error}",
                    "audio_file": audio_file,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 결과 구성 - 핵심 데이터만 반환
            result = {
                "status": "success",
                "full_text": transcript.text,
                "timestamp": datetime.now().isoformat()
            }
            
            # 화자 분리 결과 추가 (있는 경우)
            if hasattr(transcript, 'utterances') and transcript.utterances:
                result["utterances"] = []
                for utterance in transcript.utterances:
                    result["utterances"].append({
                        "speaker": utterance.speaker,
                        "text": utterance.text,
                        "start": utterance.start / 1000,  # ms to seconds
                        "end": utterance.end / 1000
                    })
                
                # 화자 ID를 숫자로 변경 (A, B → 1, 2)
                result["utterances"] = self._convert_speaker_ids_to_numbers(result["utterances"])
            
            # 결과 저장
            self._save_transcription_result(result)
            
            return result
            
        except Exception as e:
            print(f"❌ 전사 오류: {e}")
            return {
                "status": "error",
                "message": f"전사 처리 중 오류 발생: {str(e)}",
                "audio_file": audio_file,
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_transcription_result(self, result: Dict[str, Any]):
        """전사 결과를 파일로 저장"""
        try:
            import json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON 파일로 저장
            json_file = os.path.join(OUTPUT_DIR, f"transcription_{timestamp}.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON 결과 저장: {json_file}")
            
            # 텍스트 파일로도 저장
            txt_file = os.path.join(OUTPUT_DIR, f"transcription_{timestamp}.txt")
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(f"# 전사 결과\n")
                f.write(f"일시: {result['timestamp']}\n\n")
                f.write(f"## 전체 텍스트\n\n")
                f.write(result['full_text'] or "전사 내용 없음")
                f.write("\n\n")
                
                # 화자별 발언
                if result.get('utterances'):
                    f.write("## 화자별 발언\n\n")
                    for utterance in result['utterances']:
                        f.write(f"**참석자 {utterance['speaker']}번** ({utterance['start']:.1f}s-{utterance['end']:.1f}s)\n")
                        f.write(f"{utterance['text']}\n\n")
                
            
            print(f"💾 텍스트 결과 저장: {txt_file}")
            
        except Exception as e:
            print(f"❌ 결과 저장 오류: {e}")
    
    
    def _convert_speaker_ids_to_numbers(self, utterances: list) -> list:
        """화자 ID를 A, B, C에서 1, 2, 3으로 변경"""
        if not utterances:
            return utterances
        
        # 기존 화자 ID들을 수집하고 정렬
        unique_speakers = sorted(list(set(u["speaker"] for u in utterances)))
        
        # 화자 매핑 생성 (A → 1, B → 2, C → 3 등)
        speaker_mapping = {}
        for i, speaker in enumerate(unique_speakers):
            speaker_mapping[speaker] = str(i + 1)
        
        # 모든 발언의 화자 ID 변경
        converted_utterances = []
        for utterance in utterances:
            converted_utterance = utterance.copy()
            converted_utterance["speaker"] = speaker_mapping[utterance["speaker"]]
            converted_utterances.append(converted_utterance)
        
        return converted_utterances