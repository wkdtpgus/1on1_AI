from typing import Optional, Dict


def prepare_speaker_stats(speaker_stats: Optional[Dict]) -> str:
    """화자 통계 텍스트 준비
    
    Args:
        speaker_stats: 화자별 통계 정보 딕셔너리
        
    Returns:
        포맷팅된 화자 통계 텍스트
    """
    if not speaker_stats:
        return ""
    
    stats_text = "\n화자별 발언 점유율:\n"
    for speaker_name, stats in speaker_stats.items():
        stats_text += f"- {speaker_name}: {stats['percentage']}% ({stats['formatted_time']})\n"
    return stats_text