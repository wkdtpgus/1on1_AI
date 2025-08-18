// API Configuration
// 환경에 따라 API URL 자동 설정
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? `http://localhost:8000`  // 로컬 개발 환경 - 8000 포트로 고정
    : window.VITE_API_URL || window.location.origin; // 현재 도메인 사용

// Config cache
let APP_CONFIG = null;

// API Functions
class MeetingAPI {
    
    // 설정 가져오기
    static async getConfig() {
        if (APP_CONFIG) return APP_CONFIG;
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/config`);
            if (!response.ok) {
                throw new Error(`Config fetch failed: ${response.status}`);
            }
            APP_CONFIG = await response.json();
            return APP_CONFIG;
        } catch (error) {
            console.error('Failed to load config:', error);
            throw error;
        }
    }
    // 오디오를 Supabase에 업로드하고 분석하는 함수
    static async analyzeAudio(audioBlob, meetingType = '1on1', questions = null, qaData = null, participantsInfo = null) {
        // 1. Supabase에 오디오 파일 업로드
        const file_id = await this.uploadToSupabase(audioBlob);
        
        // 2. 분석 API 호출
        const formData = new FormData();
        formData.append('file_id', file_id);
        
        // Q&A 데이터가 있는 경우 추가
        if (qaData && qaData.length > 0) {
            formData.append('qa_data', JSON.stringify(qaData));
            console.log('🔍 API로 전송하는 Q&A 데이터:', qaData);
        }
        
        // 참석자 정보가 있는 경우 추가
        if (participantsInfo && (participantsInfo.leader || participantsInfo.member || participantsInfo.participants)) {
            formData.append('participants_info', JSON.stringify(participantsInfo));
            console.log('👥 API로 전송하는 참석자 정보:', participantsInfo);
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/analyze`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // 백엔드에서 이미 포맷된 형식으로 반환하므로 그대로 사용
            if (data.status === 'success') {
                // 기획회의 구조인 경우
                if (data.meeting_type === 'planning' && (data.strategic_insights || data.next_steps)) {
                    return {
                        meeting_type: data.meeting_type,
                        quick_review: data.quick_review || {},
                        detailed_discussion: data.detailed_discussion || '',
                        strategic_insights: data.strategic_insights || [],
                        innovation_ideas: data.innovation_ideas || [],
                        risks_challenges: data.risks_challenges || [],
                        next_steps: data.next_steps || [],
                        transcript: data.transcript || '스크립트를 불러올 수 없습니다.',
                        title: data.title || '기획회의 분석 결과'
                    };
                }
                // 새로운 JSON 구조가 있는 경우 그대로 반환 (1on1 등)
                else if (data.quick_review || data.detailed_discussion) {
                    return {
                        meeting_type: data.meeting_type || '1on1',
                        quick_review: data.quick_review || {},
                        detailed_discussion: data.detailed_discussion || '',
                        feedback: data.feedback || [],
                        positive_aspects: data.positive_aspects || [],
                        qa_summary: data.qa_summary || [],
                        transcript: data.transcript || '스크립트를 불러올 수 없습니다.',
                        title: data.title || '1on1 미팅 분석 결과'
                    };
                }
                // 기존 구조 지원 (하위 호환성)
                return {
                    meeting_type: data.meeting_type || '1on1',
                    summary: data.summary || '요약 정보가 없습니다.',
                    decisions: data.decisions || [],
                    actionItems: data.actionItems || [],
                    feedback: data.feedback || { positive: [], improvement: [] },
                    qa: data.qa || [],
                    transcript: data.transcript || '스크립트를 불러올 수 없습니다.'
                };
            } else {
                throw new Error(data.message || '분석에 실패했습니다.');
            }
            
        } catch (error) {
            console.error('Error analyzing audio:', error);
            throw error;
        }
    }
    
    // 서버 응답을 프론트엔드 형식으로 변환
    static formatAnalysisResults(data) {
        return {
            summary: data.summary || '요약 정보가 없습니다.',
            decisions: data.key_decisions || [],
            actionItems: data.action_items || [],
            feedback: {
                positive: data.leader_feedback?.positive_points || [],
                improvement: data.leader_feedback?.improvement_points || []
            },
            qa: this.formatQAResults(data.qa_analysis || {}),
            transcript: data.transcript || '스크립트를 불러올 수 없습니다.'
        };
    }
    
    // Q&A 결과 포맷팅
    static formatQAResults(qaData) {
        if (!qaData.questions || !qaData.answers) {
            return [];
        }
        
        return qaData.questions.map((question, index) => ({
            question: question,
            answer: qaData.answers[index] || '답변이 없습니다.'
        }));
    }
    
    // STT 상태 확인 (폴링용)
    static async checkAnalysisStatus(taskId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/status/${taskId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error checking status:', error);
            throw error;
        }
    }
    
    // 이전 분석 결과 가져오기
    static async getAnalysisHistory() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/history`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching history:', error);
            throw error;
        }
    }
    
    // 분석 결과 내보내기
    static async exportResults(analysisId, format = 'pdf') {
        try {
            const response = await fetch(`${API_BASE_URL}/api/export/${analysisId}?format=${format}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // 파일 다운로드 처리
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `meeting_analysis_${analysisId}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error('Error exporting results:', error);
            throw error;
        }
    }
    
    // Supabase에 오디오 파일 업로드
    static async uploadToSupabase(audioBlob) {
        try {
            // 설정 가져오기
            const config = await this.getConfig();
            
            // UUID + timestamp로 파일 ID 생성
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const uuid = Math.random().toString(36).substring(2, 15);
            const file_id = `recording_${uuid}_${timestamp}.wav`;
            
            // Supabase Storage API를 직접 호출
            const response = await fetch(`${config.supabase_url}/storage/v1/object/${config.bucket_name}/recordings/${file_id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${config.supabase_key}`,
                    'Content-Type': 'audio/wav'
                },
                body: audioBlob
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Supabase 업로드 실패: ${response.status} - ${errorText}`);
            }
            
            console.log(`✅ Supabase 업로드 완료: ${file_id}`);
            return file_id;
            
        } catch (error) {
            console.error('Supabase 업로드 오류:', error);
            throw error;
        }
    }
}

// Progress tracking with real API
async function analyzeWithProgress(audioBlob, updateProgress, meetingType = '1on1', qaData = null, participantsInfo = null) {
    try {
        // 초기 업로드
        updateProgress(10, 'Supabase에 파일 업로드 중...');
        
        // 분석 요청 시작
        updateProgress(30, 'STT 변환 시작...');
        
        // 실제 API 호출
        const results = await MeetingAPI.analyzeAudio(audioBlob, meetingType, null, qaData, participantsInfo);
        
        // 진행률 시뮬레이션 (실제로는 백엔드에서 WebSocket으로 진행률 전송)
        const progressSteps = [
            { progress: 40, text: 'STT 변환 완료...' },
            { progress: 60, text: 'AI 분석 중...' },
            { progress: 80, text: '결과 생성 중...' },
            { progress: 100, text: '분석 완료!' }
        ];
        
        for (const step of progressSteps) {
            updateProgress(step.progress, step.text);
            await new Promise(resolve => setTimeout(resolve, 800));
        }
        
        return results;
        
    } catch (error) {
        console.error('Analysis failed:', error);
        updateProgress(0, `분석 중 오류: ${error.message}`);
        throw error;
    }
}

// Export the API class and helper functions
window.MeetingAPI = MeetingAPI;
window.analyzeWithProgress = analyzeWithProgress;