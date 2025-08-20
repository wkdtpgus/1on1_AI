// Audio Recording Variables
let mediaRecorder;
let audioChunks = [];
let recordingTimer;
let recordingSeconds = 0;
let audioBlob = null;
let selectedMeetingType = '1on1';
let qaCounter = 0;
let qaPairs = [];
let currentAnalysisResults = null; // 현재 분석 결과 저장용

// DOM Elements
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const recordBtn = document.getElementById('recordBtn');
const micIcon = document.getElementById('micIcon');
const recordingTime = document.getElementById('recordingTime');
const timeDisplay = document.getElementById('timeDisplay');
const analyzeBtn = document.getElementById('analyzeBtn');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

// Copy Buttons
const copySummaryBtn = document.getElementById('copySummaryBtn');
const copyMarkdownBtn = document.getElementById('copyMarkdownBtn');
const copyTranscriptBtn = document.getElementById('copyTranscriptBtn');

// Participants Elements
const leaderName = document.getElementById('leaderName');
const memberName = document.getElementById('memberName');

// Q&A Elements
const addQABtn = document.getElementById('addQABtn');
const loadTestQABtn = document.getElementById('loadTestQABtn');
const qaContainer = document.getElementById('qaContainer');

// Tab Elements
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Meeting Type Selection
const meetingTypeButtons = document.querySelectorAll('.meeting-type-btn');

meetingTypeButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Update active state
        meetingTypeButtons.forEach(btn => btn.classList.remove('active-type'));
        button.classList.add('active-type');
        
        // Store selected type
        selectedMeetingType = button.getAttribute('data-type');
        
        // Update UI based on meeting type
        updateUIForMeetingType(selectedMeetingType);
    });
});

// Initialize Q&A section on page load
document.addEventListener('DOMContentLoaded', () => {
    // Q&A 섹션은 비워둔 상태로 시작 - 사용자가 테스트 데이터를 로드하거나 직접 추가
    console.log('Q&A 섹션 초기화 완료');
    
    // 초기 회의 타입에 따른 UI 설정 (기본값: 1on1)
    updateUIForMeetingType(selectedMeetingType);
    
    // 주간회의 빠른 참석자 추가 버튼 이벤트 리스너
    const addWeeklyMembersBtn = document.getElementById('addWeeklyMembersBtn');
    if (addWeeklyMembersBtn) {
        addWeeklyMembersBtn.addEventListener('click', () => {
            addWeeklyMembers();
        });
    }
    
    // 기획회의 빠른 참석자 추가 버튼 이벤트 리스너
    const addPlanningMembersBtn = document.getElementById('addPlanningMembersBtn');
    if (addPlanningMembersBtn) {
        addPlanningMembersBtn.addEventListener('click', () => {
            addPlanningMembers();
        });
    }
});

// Q&A Management Functions
addQABtn.addEventListener('click', () => {
    addQAPair();
});

// 김준희 테스트 Q&A 데이터 (하드코딩)
const kimJunheeTestData = [
    {
        question: "벌써 두 달 반이 다 되어가네요. 처음 오셨을 때보다 회사 분위기나 동료들과는 좀 더 편해지셨나요?",
        answer: "제가 점점 편해지고 있다는게 조금씩 느껴지고 있어요"
    },
    {
        question: "우리 회사에 남아서 더 하게된 이유는 무엇인가요?",
        answer: "인턴 기간 동안 일하는 게 너무 재밌었고 또 제가 많이 성장할 수 있을 거라고 생각했어요. 2개월 전의 저랑 지금의 저랑 확실히 성장하고 조금 더 나아지고 있다라는 걸 느꼈어요"
    },
    {
        question: "요즘 개인적으로 가장 흥미롭게 몰입하고 있는 업무나 프로젝트가 있으시다면 어떤 건가요?",
        answer: "제가 정리하는 것을 좋아해서 요즘 요약하는 것에 대해서 프롬프트 엔지니어링을 하는 것에 가장 몰입하고 있는 것 같아요. 제가 봤을 때도 이 정도면 괜찮은데 싶을 정도로 하고 싶은데 아직 만족하는 결과물은 아닌 것 같아요"
    },
    {
        question: "최근 2주간 진행했던 업무 중에서 특히 기억에 남거나, '이건 정말 잘했다!'고 생각하는 성과가 있다면 어떤 것인지 구체적으로 이야기해주실 수 있을까요?",
        answer: "아직까지 기억에 남는 성과는 없는 것 같아요. 이번에 1on1이 끝나고 테스트해보고 실제 결과를 빨리 보고 싶어요"
    },
    {
        question: "수습을 기점으로 정규직 전환을 앞두고 계신데, 앞으로 회사에서 어떤 역할을 하고 싶고, 어떤 부분에서 기여하고 싶다는 계획을 가지고 계신가요?",
        answer: "AI 개발자로서도 더 기여하고 싶고 또 지현님이 인턴 기간에 말씀해 주셨듯이 점점 풀스택 개발자로 성장하고 싶어요"
    },
    {
        question: "현재 맡고 계신 업무가 준희님의 기술 스택이나 강점과 잘 맞는다고 느끼시는지 궁금합니다. 혹시 잘 맞는다고 느끼는 부분과 개선이 필요하다고 생각하는 부분이 있으신가요?",
        answer: "하루하루 새로운 기술들 새로운 기법들이 많이 나오는데 이런 부분들이 새로운 것을 배우는 걸 좋아하는 제게는 정말 잘 맞는 것 같아요"
    },
    {
        question: "AI 개발자로서 앞으로 어떤 기술 역량을 중점적으로 개발하고 싶으신가요? 그리고 이를 위해 어떤 계획을 가지고 계신지 궁금합니다.",
        answer: "아직까지는 현재 업무에서 다루고 있는 llm이나 프롬프트 엔지니어링에 관심이 있는 것 같아요. 최근에 비슷한 일을 하는 친구들이랑 이야기를 해보면서 oss 오픈소스 모델을 가지고 이것저것 해보고 싶다는 생각도 들었어요"
    },
    {
        question: "지난번에 이야기 나눴던 'Cursor MCP 서버 사용 및 리뷰'는 잘 진행되고 있는지 궁금합니다. 혹시 사용하시면서 특별히 느끼신 점이나 어려움은 없으셨나요?",
        answer: "리뷰는 못했지만 피그마, 슈퍼베이스 정도 써봤던 것 같아요 최근에는 클로드 코드 템플릿 사이트? 같은 곳에서 에이전트랑 mcp를 쉽게 사용할 수 있는게 있어서 ai 엔지니어, 프롬프트 엔지니어, 코드 리뷰어 에이전트를 조합해서 사용해보고 있어요"
    },
    {
        question: "준희님의 성장을 위해 회사에서 어떤 지원을 해주면 가장 도움이 될 것이라고 생각하시나요?",
        answer: "저는 여러 프로젝트를 해보는게.. 도움이 될 것 같아요. 기획적인 측면에서도 생각하려고 노력하는게 여러 방면으로 시야를 넓혀주는 것 같아요"
    },
    {
        question: "현재 업무량은 적절하다고 느끼시는지 궁금합니다. 혹시 더 도전하고 싶은 업무가 있으시거나, 반대로 부담이 된다고 느끼는 부분이 있으신가요?",
        answer: "업무량은 적절한 것 같아요 부담감 또한 조금씩은 있어야 한다고 생각하는데 적절하다고 생각합니다.."
    },
    {
        question: "업무 몰입도 측면에서, 지난 한 달을 돌아봤을 때 스스로 어느 정도 점수를 줄 수 있을까요? (1점: 매우 낮음 ~ 5점: 매우 높음)",
        answer: "4점 인 것 같아요 1on1에 대해서 잘 와닿지가 않아서 최대한 이해하려고 자료 조사를 많이 했는데 도움도 많이 된 것 같고 칭찬도 해주셔서 4점 주겠습니다"
    },
    {
        question: "AI 개발자로서 핵심 스킬셋을 개발하는 데 있어 다음 중 어떤 방식이 가장 효과적이라고 생각하시나요? (a) 사내 스터디 참여, (b) 외부 교육 수강, (c) 개인 프로젝트 진행, (d) 논문 및 자료 학습",
        answer: "이번 인턴 하면서 느낀건데 확실히 프로젝트에 직접 참여하는게 정말 도움이 많이 되었던 것 같아요"
    },
    {
        question: "앞으로 준희님이 가장 성장하고 싶은 영역은 다음 중 어디인가요? (a) 특정 AI 모델 개발 역량, (b) 데이터 처리 및 분석 능력, (c) 협업 및 커뮤니케이션 스킬, (d) 문제 해결 능력",
        answer: "요즘은 (a)인데 데이터 분석을 했었어서 그 다음을 고르라면 (b)인 것 같아요 근데 요즘 느끼는거는 데이터 분석이라는게 업무를 하면서 자연스럽게 하게되는 것 같기도 해요"
    },
    {
        question: "만약 지금 당장 새로운 것을 시도할 수 있는 기회가 주어진다면, 어떤 종류의 AI 프로젝트나 기술에 도전해보고 싶으신가요?",
        answer: ""
    },
    {
        question: "마지막으로, 오늘 나눈 이야기 외에 준희님이 저에게 이야기하고 싶었던 다른 점은 없으실까요?",
        answer: ""
    }
];

// Load Test Q&A Data (하드코딩 버전)
loadTestQABtn.addEventListener('click', () => {
    try {
        loadTestQABtn.disabled = true;
        loadTestQABtn.innerHTML = '<i class="ri-loader-4-line mr-2 animate-spin"></i>로딩 중...';
        
        // 기존 Q&A 데이터 초기화
        clearQAData();
        
        // 테스트 데이터로 Q&A 추가
        kimJunheeTestData.forEach((qa, index) => {
            setTimeout(() => {
                addQAPair(qa.question, qa.answer);
            }, index * 100); // 각각 100ms 간격으로 추가
        });
        
        // 성공 알림
        setTimeout(() => {
            showNotification(`✅ 김준희 테스트 데이터 ${kimJunheeTestData.length}개 항목이 로드되었습니다!`, 'success');
        }, kimJunheeTestData.length * 100 + 200);
        
    } catch (error) {
        console.error('Test Q&A data load error:', error);
        showNotification(`❌ 테스트 데이터 로드 실패: ${error.message}`, 'error');
    } finally {
        setTimeout(() => {
            loadTestQABtn.disabled = false;
            loadTestQABtn.innerHTML = '<i class="ri-test-tube-line mr-2"></i>김준희 테스트 데이터';
        }, kimJunheeTestData.length * 100 + 500);
    }
});

function addQAPair(question = '', answer = '') {
    qaCounter++;
    const qaId = `qa_${qaCounter}`;
    
    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item py-2 border-b border-gray-100 last:border-b-0';
    qaItem.id = qaId;
    
    qaItem.innerHTML = `
        <div class="flex justify-end mb-2">
            <button onclick="removeQAPair('${qaId}')" class="text-gray-400 hover:text-red-500 transition-colors p-1">
                <i class="ri-close-line text-sm"></i>
            </button>
        </div>
        
        <!-- 질문 영역 -->
        <div class="flex items-start space-x-3 mb-1">
            <div class="mt-1">
                <span class="text-sm font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">Q</span>
            </div>
            <div class="flex-1">
                <textarea 
                    id="${qaId}_question" 
                    placeholder="질문을 입력하세요..."
                    class="w-full bg-transparent border-none focus:outline-none resize-none text-base text-gray-900 placeholder-gray-400 leading-relaxed mt-1"
                    rows="2"
                    onchange="updateQAData()">${question}</textarea>
            </div>
        </div>
        
        <!-- 답변 영역 -->
        <div class="flex items-start space-x-3">
            <div class="mt-1">
                <span class="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded">A</span>
            </div>
            <div class="flex-1">
                <textarea 
                    id="${qaId}_answer" 
                    placeholder="답변을 입력하세요..."
                    class="w-full bg-transparent border-none focus:outline-none resize-none text-base text-gray-700 placeholder-gray-400 leading-relaxed mt-1"
                    rows="3"
                    onchange="updateQAData()">${answer}</textarea>
            </div>
        </div>
    `;
    
    qaContainer.appendChild(qaItem);
    updateQAData();
    
    // 새로 추가된 Q&A로 부드럽게 스크롤
    setTimeout(() => {
        qaItem.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        // 첫 번째 입력 필드(질문)에 포커스
        document.getElementById(`${qaId}_question`).focus();
    }, 100);
}

function removeQAPair(qaId) {
    const qaItem = document.getElementById(qaId);
    if (qaItem) {
        qaItem.remove();
        updateQAData();
    }
}

function updateQAData() {
    qaPairs = [];
    const qaItems = document.querySelectorAll('.qa-item');
    
    qaItems.forEach(item => {
        const questionTextarea = item.querySelector('textarea[id$="_question"]');
        const answerTextarea = item.querySelector('textarea[id$="_answer"]');
        
        if (questionTextarea && answerTextarea) {
            const question = questionTextarea.value.trim();
            const answer = answerTextarea.value.trim();
            
            if (question || answer) {
                qaPairs.push({
                    question: question,
                    answer: answer
                });
            }
        }
    });
    
    console.log('🔍 Q&A 데이터 업데이트:', qaPairs);
}

function clearQAData() {
    qaContainer.innerHTML = '';
    qaPairs = [];
    qaCounter = 0;
}

// Transcript 포맷팅 함수
function formatTranscript(transcript) {
    console.log('📋 formatTranscript 입력:', typeof transcript, transcript);
    
    // transcript가 화자별 발화 배열인 경우
    if (Array.isArray(transcript)) {
        return transcript.map(utterance => {
            const speaker = utterance.speaker || 'Unknown';
            const text = utterance.text || '';
            return `${speaker}: ${text}`;
        }).join('\n\n');
    }
    
    // transcript 객체에 utterances 배열이 있는 경우 (새로운 구조)
    if (transcript && transcript.utterances && Array.isArray(transcript.utterances)) {
        return transcript.utterances.map(utterance => {
            const speaker = utterance.speaker || 'Unknown';
            const text = utterance.text || '';
            return `${speaker}: ${text}`;
        }).join('\n\n');
    }
    
    // transcript가 문자열이거나 다른 형태인 경우
    if (typeof transcript === 'string') {
        return transcript;
    }
    
    // transcript 객체에 text 필드가 있는 경우 (이전 형식)
    if (transcript && transcript.text) {
        return transcript.text;
    }
    
    console.log('❌ formatTranscript: 알 수 없는 형식', transcript);
    return '스크립트를 불러올 수 없습니다.';
}

// 알림 표시 함수
function showNotification(message, type = 'info') {
    // 알림 요소 생성
    const notification = document.createElement('div');
    const baseClasses = 'fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg flex items-center z-50 font-medium';
    
    let colorClasses;
    switch(type) {
        case 'success':
            colorClasses = 'bg-green-600 text-white';
            break;
        case 'error':
            colorClasses = 'bg-red-600 text-white';
            break;
        case 'warning':
            colorClasses = 'bg-yellow-600 text-white';
            break;
        default:
            colorClasses = 'bg-blue-600 text-white';
    }
    
    notification.className = `${baseClasses} ${colorClasses}`;
    notification.innerHTML = `<span>${message}</span>`;
    
    // body에 추가
    document.body.appendChild(notification);
    
    // 자동으로 사라지게 하기
    setTimeout(() => {
        notification.style.transition = 'opacity 0.5s, transform 0.5s';
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 500);
    }, 3000);
}

// File Upload Handler
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = file.name;
        fileInfo.classList.remove('hidden');
        analyzeBtn.disabled = false;
        audioBlob = file;
    }
});

// Recording Functions
recordBtn.addEventListener('click', async () => {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        await startRecording();
    } else {
        stopRecording();
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.addEventListener('dataavailable', event => {
            audioChunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', () => {
            audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            analyzeBtn.disabled = false;
        });
        
        mediaRecorder.start();
        
        // Update UI
        recordBtn.innerHTML = '<i class="ri-stop-circle-line mr-2"></i>녹음 중지';
        recordBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
        recordBtn.classList.add('bg-gray-600', 'hover:bg-gray-700');
        micIcon.classList.remove('ri-mic-line');
        micIcon.classList.add('ri-mic-fill', 'text-red-600', 'animate-pulse');
        recordingTime.classList.remove('hidden');
        
        // Start timer
        recordingSeconds = 0;
        recordingTimer = setInterval(() => {
            recordingSeconds++;
            const minutes = Math.floor(recordingSeconds / 60);
            const seconds = recordingSeconds % 60;
            timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
        
    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert('마이크 접근 권한이 필요합니다.');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        // Update UI
        recordBtn.innerHTML = '<i class="ri-record-circle-line mr-2"></i>녹음 시작';
        recordBtn.classList.remove('bg-gray-600', 'hover:bg-gray-700');
        recordBtn.classList.add('bg-red-600', 'hover:bg-red-700');
        micIcon.classList.remove('ri-mic-fill', 'text-red-600', 'animate-pulse');
        micIcon.classList.add('ri-mic-line');
        
        // Stop timer
        clearInterval(recordingTimer);
        
        // 녹음 파일 자동 저장
        setTimeout(() => {
            if (audioBlob) {
                saveRecordingFile(audioBlob);
            }
        }, 500); // mediaRecorder stop 이벤트 처리 후 저장
    }
}

// 녹음 파일 저장 함수
function saveRecordingFile(blob) {
    // 현재 날짜와 시간으로 파일명 생성
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    // 미팅 타입을 파일명에 포함
    const meetingTypeKorean = {
        '1on1': '1on1미팅',
        'general': '일반회의',
        'weekly': '주간회의',
        'planning': '기획회의'
    };
    
    const meetingName = meetingTypeKorean[selectedMeetingType] || '회의';
    const fileName = `${meetingName}_녹음_${year}${month}${day}_${hours}${minutes}${seconds}.wav`;
    
    // Blob을 다운로드 링크로 변환
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    
    // 메모리 정리
    setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 100);
    
    // 사용자에게 알림
    console.log(`✅ 녹음 파일이 저장되었습니다: ${fileName}`);
    
    // 간단한 알림 메시지 표시 (선택사항)
    showSaveNotification(fileName);
}

// 저장 알림 표시 함수
function showSaveNotification(fileName) {
    // 알림 요소 생성
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center z-50';
    notification.innerHTML = `
        <i class="ri-download-2-line mr-2"></i>
        <span>녹음 파일이 저장되었습니다: ${fileName}</span>
    `;
    
    // body에 추가
    document.body.appendChild(notification);
    
    // 3초 후 자동으로 사라지게 하기
    setTimeout(() => {
        notification.style.transition = 'opacity 0.5s';
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}

// Analysis Function
analyzeBtn.addEventListener('click', async () => {
    if (!audioBlob) {
        alert('분석할 오디오 파일이 없습니다.');
        return;
    }
    
    // Show progress section
    progressSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    
    try {
        // Use real API if available, otherwise use mock data
        if (window.MeetingAPI && window.analyzeWithProgress) {
            // Real API call with progress tracking
            // 참석자 정보 수집 (회의 타입에 따라 다르게 처리)
            let participantsInfo = null;
            
            if (selectedMeetingType === '1on1') {
                // 1on1: 리더/멤버 구분
                const leaderEl = document.getElementById('leaderName');
                const memberEl = document.getElementById('memberName');
                if (leaderEl && memberEl) {
                    participantsInfo = {
                        leader: leaderEl.value.trim(),
                        member: memberEl.value.trim()
                    };
                }
            } else {
                // 다른 회의: 일반 참가자 목록
                const participantInputs = document.querySelectorAll('.participant-input input');
                const participants = [];
                
                participantInputs.forEach(input => {
                    const name = input.value.trim();
                    if (name) {
                        participants.push(name);
                    }
                });
                
                if (participants.length > 0) {
                    participantsInfo = {
                        participants: participants
                    };
                }
            }
            
            const results = await analyzeWithProgress(
                audioBlob, 
                (progress, text) => {
                    progressBar.style.width = `${progress}%`;
                    progressText.textContent = text;
                },
                selectedMeetingType,  // 선택된 미팅 타입 전달
                qaPairs,  // Q&A 데이터 전달
                participantsInfo  // 참석자 정보 전달
            );
            showResults(results);
        } else {
            // Fallback to simulation for demo
            await simulateAnalysis();
            showResults(getMockResults());
        }
    } catch (error) {
        console.error('Analysis error:', error);
        alert(`분석 중 오류가 발생했습니다: ${error.message}`);
        progressSection.classList.add('hidden');
    }
});

// Simulate Analysis Progress
async function simulateAnalysis() {
    const steps = [
        { progress: 20, text: 'STT 변환 중...' },
        { progress: 40, text: '대화 내용 분석 중...' },
        { progress: 60, text: '핵심 내용 추출 중...' },
        { progress: 80, text: '피드백 생성 중...' },
        { progress: 100, text: '분석 완료!' }
    ];
    
    for (const step of steps) {
        progressBar.style.width = `${step.progress}%`;
        progressText.textContent = step.text;
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

// Show Results
function showResults(results) {
    console.log('🔍 showResults 호출됨:', results);
    console.log('🔍 results.meeting_type:', results.meeting_type);
    console.log('🔍 results.leader_action_items 존재:', !!results.leader_action_items);
    console.log('🔍 results.member_action_items 존재:', !!results.member_action_items);
    console.log('🔍 results.ai_summary 존재:', !!results.ai_summary);
    
    // 분석 결과를 전역 변수에 저장 (복사 기능용)
    currentAnalysisResults = results;
    
    progressSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    
    // 결과 표시 전에 UI를 미팅 타입에 맞게 업데이트
    if (results.meeting_type) {
        updateUIForMeetingType(results.meeting_type);
    }
    
    // 미팅 타입별 결과 표시
    if (results.meeting_type === 'planning' && (results.strategic_insights || results.next_steps)) {
        console.log('✅ displayPlanningResults 호출');
        // 기획회의 결과 구조로 표시
        displayPlanningResults(results);
    } else if (results.meeting_type === 'weekly') {
        console.log('✅ displayWeeklyResults 호출');
        // 주간회의 결과 구조로 표시
        displayWeeklyResults(results);
    } else if (results.meeting_type === 'general') {
        console.log('✅ displayGeneralResults 호출');
        // 일반회의 결과 구조로 표시
        displayGeneralResults(results);
    } else if (results.leader_action_items || results.member_action_items || results.ai_summary) {
        console.log('✅ displayActualResults 호출');
        // 실제 분석 결과 구조로 표시
        displayActualResults(results);
    } else {
        console.log('✅ displayMockResults 호출');
        // Mock 결과 구조로 표시
        displayMockResults(results);
    }
}

// 실제 분석 결과 표시
function displayActualResults(results) {
    console.log('🔍 displayActualResults 시작:', results);
    
    // Quick Review 섹션 업데이트
    // 액션 아이템 표시 (리더와 멤버 구분)
    const actionsElement = document.getElementById('quickReviewActions');
    if (actionsElement) {
        let actionsHTML = '';
        
        if (results.leader_action_items && results.leader_action_items.length > 0) {
            actionsHTML += '<h4 style="color: #dc2626; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;"><span>👨‍💼</span>리더 액션 아이템</h4>';
            actionsHTML += '<ul style="margin-bottom: 16px; padding-left: 20px;">' + results.leader_action_items.map(item => `<li style="color: #dc2626; margin-bottom: 4px;">${item}</li>`).join('') + '</ul>';
        }
        
        if (results.member_action_items && results.member_action_items.length > 0) {
            actionsHTML += '<h4 style="color: #0284c7; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;"><span>👤</span>멤버 액션 아이템</h4>';
            actionsHTML += '<ul style="margin-bottom: 16px; padding-left: 20px;">' + results.member_action_items.map(item => `<li style="color: #0284c7; margin-bottom: 4px;">${item}</li>`).join('') + '</ul>';
        }
        
        actionsElement.innerHTML = actionsHTML || '액션 아이템이 없습니다.';
    }
    
    // 세부 상세 요약 업데이트
    if (results.ai_summary) {
        const detailedElement = document.getElementById('detailedDiscussion');
        if (detailedElement) {
            // 마크다운을 HTML로 변환하여 적용
            detailedElement.innerHTML = convertMarkdownToHtml(results.ai_summary);
        } else {
            console.log('❌ detailedDiscussion 요소를 찾을 수 없습니다');
        }
    } else {
        console.log('❌ No ai_summary data found');
    }
    
    // 피드백 탭 업데이트
    if (results.leader_feedback && Array.isArray(results.leader_feedback)) {
        const feedbackHtml = results.leader_feedback.map(item => `
            <div class="bg-red-50 border-l-4 border-red-500 rounded-lg p-6">
                <h5 class="font-semibold text-red-900 mb-3">${item.title.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</h5>
                <div class="space-y-3">
                    <div>
                        <span class="font-medium text-red-800">상황:</span>
                        <p class="text-gray-700 mt-1">${item.situation.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                    <div>
                        <span class="font-medium text-red-800">제안:</span>
                        <p class="text-gray-700 mt-1">${item.suggestion.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                    <div>
                        <span class="font-medium text-red-800">중요성:</span>
                        <p class="text-gray-700 mt-1">${item.importance.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                    <div>
                        <span class="font-medium text-red-800">실행 방안:</span>
                        <p class="text-gray-700 mt-1">${item.implementation.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                </div>
            </div>
        `).join('');
        const feedbackElement = document.getElementById('feedbackItems');
        if (feedbackElement) {
            feedbackElement.innerHTML = feedbackHtml;
        } else {
        }
    } else {
    }
    
    // 긍정적 측면 업데이트
    if (results.positive_aspects && Array.isArray(results.positive_aspects)) {
        const positiveHtml = results.positive_aspects.map(aspect => 
            `<li class="text-gray-700 flex items-start"><i class="ri-check-line text-green-600 mr-2 mt-1"></i>${aspect.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</li>`
        ).join('');
        const positiveElement = document.getElementById('positiveAspects');
        if (positiveElement) {
            positiveElement.innerHTML = positiveHtml;
        } else {
        }
    } else {
    }
    
    // Q&A 탭 업데이트
    if (results.qa_summary && Array.isArray(results.qa_summary)) {
        console.log(`🔍 Q&A 데이터 개수: ${results.qa_summary.length}`);
        console.log('🔍 Q&A 전체 데이터:', results.qa_summary);
        
        // 마지막 항목 특별 체크
        if (results.qa_summary.length > 0) {
            const lastItem = results.qa_summary[results.qa_summary.length - 1];
            console.log('🔍 마지막 Q&A 항목:', lastItem);
        }
        
        const qaHtml = results.qa_summary.map((item) => {
            const questionText = qaPairs[item.question_index - 1]?.question || `질문 ${item.question_index}`;
            return `
                <div class="border-l-4 border-indigo-500 pl-6 py-4">
                    <p class="font-semibold text-gray-900 mb-2">Q${item.question_index}: ${questionText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    <p class="text-gray-700">A: ${(item.answer || '답변이 없습니다').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                </div>
            `;
        }).join('');
        const qaElement = document.getElementById('qaContent');
        if (qaElement) {
            qaElement.innerHTML = qaHtml;
            console.log('✅ Q&A 내용 업데이트 완료');
        } else {
            console.log('❌ qaContent 요소를 찾을 수 없습니다');
        }
    } else {
        console.log('❌ Q&A 데이터가 없거나 배열이 아닙니다', results.qa_summary);
    }
    
    // 전체 스크립트 업데이트
    const transcriptElement = document.getElementById('transcriptContent');
    if (transcriptElement) {
        const transcriptText = formatTranscript(results.transcript);
        transcriptElement.innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${transcriptText || '스크립트를 불러올 수 없습니다.'}</p>`;
    } else {
    }
    
    // 처리 완료 후 첫 번째 탭(요약)으로 자동 전환
    const summaryTabBtn = document.querySelector('[data-tab="summary"]');
    if (summaryTabBtn) {
        summaryTabBtn.click();
    }
}

// Mock 결과 표시 (기존 방식)
function displayMockResults(results) {
    // Quick Review를 기본 요약으로 표시
    document.getElementById('quickReviewTakeaways').textContent = results.summary || '';
    
    if (results.decisions && Array.isArray(results.decisions)) {
        const decisionsText = results.decisions.map(d => `• ${d}`).join('\n');
        document.getElementById('quickReviewDecisions').innerHTML = formatTextWithBreaks(decisionsText);
    }
    
    if (results.actionItems && Array.isArray(results.actionItems)) {
        const actionsText = results.actionItems.map(a => `• ${a}`).join('\n');
        document.getElementById('quickReviewActions').innerHTML = formatTextWithBreaks(actionsText);
    }
    
    // 세부 요약은 동일한 내용으로
    document.getElementById('detailedDiscussion').textContent = results.summary || '';
    
    // 피드백 탭 (기존 구조)
    if (results.leader_feedback) {
        const positiveHtml = (results.leader_feedback.positive || []).map(p => 
            `<li class="text-gray-700 flex items-start"><i class="ri-check-line text-green-600 mr-2 mt-1"></i>${p}</li>`
        ).join('');
        document.getElementById('positiveAspects').innerHTML = positiveHtml;
        
        // 개선점을 간단한 형태로 표시
        const improvementHtml = (results.leader_feedback.improvement || []).map(item => `
            <div class="bg-red-50 border-l-4 border-red-500 rounded-lg p-6">
                <p class="text-gray-700">${item}</p>
            </div>
        `).join('');
        document.getElementById('feedbackItems').innerHTML = improvementHtml;
    }
    
    // Q&A 탭
    const qaHtml = (results.qa || []).map(item => `
        <div class="border-l-4 border-indigo-500 pl-6 py-4">
            <p class="font-semibold text-gray-900 mb-2">Q: ${item.question}</p>
            <p class="text-gray-700">A: ${item.answer}</p>
        </div>
    `).join('');
    document.getElementById('qaContent').innerHTML = qaHtml;
    
    // 전체 스크립트
    const transcriptText = formatTranscript(results.transcript);
    document.getElementById('transcriptContent').innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${transcriptText}</p>`;
}

// 텍스트에 줄바꿈 포맷팅 적용
function formatTextWithBreaks(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>').replace(/•/g, '•').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
}

// 마크다운을 HTML로 변환하는 함수
function convertMarkdownToHtml(text) {
    if (!text) return '';
    
    // 줄 단위로 처리
    const lines = text.split('\n');
    let html = [];
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        
        // 빈 줄 처리
        if (line.trim() === '') {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            html.push('<div class="mb-3"></div>');
            continue;
        }
        
        // 헤딩 처리 (들여쓰기 포함)
        if (line.match(/^  ### /)) {
            // 2칸 들여쓰기된 서브섹션
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            const content = line.replace(/^  ### /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<h3 class="text-lg font-semibold text-gray-900 mt-6 mb-3 ml-4">${content}</h3>`);
        } else if (line.match(/^### /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            const content = line.replace(/^### /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<h3 class="text-lg font-semibold text-gray-900 mt-6 mb-3">${content}</h3>`);
        } else if (line.match(/^## /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            const content = line.replace(/^## /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<h2 class="text-xl font-bold text-gray-900 mt-8 mb-4">${content}</h2>`);
        } else if (line.match(/^# /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            const content = line.replace(/^# /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<h1 class="text-2xl font-bold text-gray-900 mt-8 mb-4">${content}</h1>`);
        }
        // 하이픈으로 시작하는 섹션 제목 처리 (예: - 개발팀, - AI 에이전트)
        else if (line.match(/^- [가-힣A-Za-z\s]+:/)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            const content = line.replace(/^- /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<h4 class="text-md font-semibold text-gray-800 mt-4 mb-2">• ${content}</h4>`);
        }
        // 4칸 들여쓰기된 a, b, c, d 항목 처리 (일반회의용)
        else if (line.match(/^\s{4}\*\*[a-z]\.\*\* /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            // 들여쓰기를 제거하기 전에 볼드 처리를 먼저 하고, 마진은 CSS 클래스로 적용
            const content = line.replace(/^\s{4}/, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<p class="text-gray-700 mb-2 ml-8">${content}</p>`);
        }
        // 4칸 들여쓰기된 불릿 포인트 처리 (주간회의, 기획회의용)
        else if (line.match(/^\s{4}[•] /)) {
            if (!inList) {
                html.push('<ul class="list-none space-y-1 mb-4 ml-8">');
                inList = true;
            }
            const content = line.replace(/^\s{4}[•] /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<li class="text-gray-700">• ${content}</li>`);
        }
        // 불릿 포인트 처리 (섹션 제목이 아닌 일반 항목들)
        else if (line.match(/^[•] /) || line.match(/^- /)) {
            if (!inList) {
                html.push('<ul class="list-none space-y-1 mb-4">');
                inList = true;
            }
            const content = line.replace(/^[•-] /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<li class="text-gray-700 ml-4">• ${content}</li>`);
        }
        // 4칸 들여쓰기된 특수 형식 텍스트 처리 (주간회의, 기획회의용 - key: value [timestamp] 형태)
        else if (line.match(/^\s{4}[가-힣A-Za-z\s]+: .* \[.*\]$/)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            const content = line.trim().replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<p class="text-gray-700 mb-2 ml-8 font-medium">${content}</p>`);
        }
        // 일반 텍스트 처리 (들여쓰기 포함)
        else {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            // 들여쓰기 감지 및 적절한 마진 적용
            const indentLevel = line.match(/^(\s*)/)[1].length;
            let marginClass = '';
            
            if (indentLevel >= 4) {
                marginClass = 'ml-8'; // 4칸 이상 들여쓰기
            } else if (indentLevel >= 2) {
                marginClass = 'ml-4'; // 2칸 들여쓰기
            }
            
            // 굵은 글씨 처리
            const content = line.trim().replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<p class="text-gray-700 mb-3 ${marginClass}">${content}</p>`);
        }
    }
    
    // 마지막에 열린 리스트 닫기
    if (inList) {
        html.push('</ul>');
    }
    
    return html.join('');
}

// 기획회의 분석 결과 표시
function displayPlanningResults(results) {
    console.log('🔍 displayPlanningResults 시작:', results);
    
    // Quick Review 섹션 숨기기 (기획회의는 세부 요약만 표시)
    const quickReviewSection = document.querySelector('.bg-blue-50.border-l-4.border-blue-500');
    if (quickReviewSection) {
        quickReviewSection.style.display = 'none';
    }
    
    // 세부 상세 요약 업데이트
    if (results.ai_summary) {
        const detailedElement = document.getElementById('detailedDiscussion');
        if (detailedElement) {
            detailedElement.innerHTML = convertMarkdownToHtml(results.ai_summary);
        }
    }
    
    // 피드백 탭을 전략적 인사이트로 변경
    if (results.strategic_insights && Array.isArray(results.strategic_insights)) {
        const insightsHtml = results.strategic_insights.map(item => `
            <div class="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-6">
                <h5 class="font-semibold text-blue-900 mb-3">${item.category}</h5>
                <div class="space-y-3">
                    <div>
                        <span class="font-medium text-blue-800">인사이트:</span>
                        <p class="text-gray-700 mt-1">${item.insight.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                    <div>
                        <span class="font-medium text-blue-800">근거:</span>
                        <p class="text-gray-700 mt-1">${item.rationale.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                    <div>
                        <span class="font-medium text-blue-800">예상 영향:</span>
                        <p class="text-gray-700 mt-1">${item.impact.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                </div>
            </div>
        `).join('');
        const feedbackElement = document.getElementById('feedbackItems');
        if (feedbackElement) {
            feedbackElement.innerHTML = insightsHtml;
        }
    }
    
    // 긍정적 측면을 혁신 아이디어로 변경
    if (results.innovation_ideas && Array.isArray(results.innovation_ideas)) {
        const innovationHtml = results.innovation_ideas.map(idea => 
            `<li class="text-gray-700 flex items-start"><i class="ri-lightbulb-line text-yellow-600 mr-2 mt-1"></i>${idea.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</li>`
        ).join('');
        const positiveElement = document.getElementById('positiveAspects');
        if (positiveElement) {
            positiveElement.innerHTML = innovationHtml;
        }
    }
    
    // Q&A 탭을 다음 단계 액션으로 변경
    if (results.next_steps && Array.isArray(results.next_steps)) {
        const nextStepsHtml = results.next_steps.map(item => `
            <div class="border-l-4 border-green-500 pl-6 py-4">
                <p class="font-semibold text-gray-900 mb-2">액션: ${item.item.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                <div class="text-sm space-y-1">
                    <p class="text-gray-700">담당자: ${(item.owner || '미정').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    <p class="text-gray-700">마감일: ${(item.deadline || '미정').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    <p class="text-gray-700">우선순위: <span class="px-2 py-1 rounded text-xs ${
                        item.priority === 'High' ? 'bg-red-100 text-red-800' :
                        item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                    }">${item.priority || 'Medium'}</span></p>
                </div>
            </div>
        `).join('');
        const qaElement = document.getElementById('qaContent');
        if (qaElement) {
            qaElement.innerHTML = nextStepsHtml;
        }
    }
    
    // 전체 스크립트 업데이트
    const transcriptElement = document.getElementById('transcriptContent');
    if (transcriptElement) {
        const transcriptText = formatTranscript(results.transcript);
        transcriptElement.innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${transcriptText || '스크립트를 불러올 수 없습니다.'}</p>`;
    }
    
    // 처리 완료 후 첫 번째 탭(요약)으로 자동 전환
    const summaryTabBtn = document.querySelector('[data-tab="summary"]');
    if (summaryTabBtn) {
        summaryTabBtn.click();
    }
}

// 주간회의 결과 표시
function displayWeeklyResults(results) {
    console.log('🔍 displayWeeklyResults 시작:', results);
    console.log('🔍 results.ai_summary:', results.ai_summary);
    
    // Quick Review 섹션 숨기기 (주간회의는 세부 요약만 표시)
    const quickReviewSection = document.querySelector('.bg-blue-50.border-l-4.border-blue-500');
    if (quickReviewSection) {
        quickReviewSection.style.display = 'none';
    }
    
    // Detailed Discussion
    if (results.ai_summary) {
        const detailedElement = document.getElementById('detailedDiscussion');
        if (detailedElement) {
            detailedElement.innerHTML = convertMarkdownToHtml(results.ai_summary);
        }
    }
    
    // Progress Updates (주간회의 전용)
    if (results.progress_updates && results.progress_updates.length > 0) {
        const progressContainer = document.getElementById('feedbackContent');
        if (progressContainer) {
            let progressHtml = '<div class="space-y-4">';
            progressHtml += '<h4 class="font-semibold text-gray-800 mb-3">📈 진행 상황 업데이트</h4>';
            
            results.progress_updates.forEach((update, index) => {
                progressHtml += `
                    <div class="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
                        <h5 class="font-medium text-blue-900">${update.area.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</h5>
                        <p class="text-sm text-blue-800 mt-1"><strong>상태:</strong> ${update.status.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-blue-700 mt-1"><strong>담당:</strong> ${update.owner.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-blue-700 mt-1"><strong>이번 주 성과:</strong> ${update.achievements.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-blue-700 mt-1"><strong>다음 단계:</strong> ${update.next_steps.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                `;
            });
            
            progressHtml += '</div>';
            progressContainer.innerHTML = progressHtml;
        }
    }
    
    // Blockers & Challenges
    if (results.blockers_challenges && results.blockers_challenges.length > 0) {
        const blockersContainer = document.getElementById('qaContent');
        if (blockersContainer) {
            let blockersHtml = '<div class="space-y-4">';
            blockersHtml += '<h4 class="font-semibold text-gray-800 mb-3">🚫 블로커 및 도전과제</h4>';
            
            results.blockers_challenges.forEach((blocker, index) => {
                blockersHtml += `
                    <div class="bg-red-50 p-4 rounded-lg border-l-4 border-red-400">
                        <h5 class="font-medium text-red-900">${blocker.blocker.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</h5>
                        <p class="text-sm text-red-800 mt-1"><strong>영향:</strong> ${blocker.impact.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-red-700 mt-1"><strong>담당:</strong> ${blocker.owner.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-red-700 mt-1"><strong>해결 방안:</strong> ${blocker.proposed_solution.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-red-700 mt-1"><strong>필요 지원:</strong> ${blocker.support_needed.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                `;
            });
            
            blockersHtml += '</div>';
            blockersContainer.innerHTML = blockersHtml;
        }
    }
    
    // 전체 스크립트
    const transcriptText = formatTranscript(results.transcript);
    document.getElementById('transcriptContent').innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${transcriptText}</p>`;
    
    // 처리 완료 후 첫 번째 탭(요약)으로 자동 전환
    const summaryTabBtn = document.querySelector('[data-tab="summary"]');
    if (summaryTabBtn) {
        summaryTabBtn.click();
    }
}

// 일반회의 결과 표시
function displayGeneralResults(results) {
    console.log('🔍 displayGeneralResults 시작:', results);
    
    // Quick Review 섹션 숨기기 (일반회의는 세부 요약만 표시)
    const quickReviewSection = document.querySelector('.bg-blue-50.border-l-4.border-blue-500');
    if (quickReviewSection) {
        quickReviewSection.style.display = 'none';
    }
    
    // Detailed Discussion
    if (results.ai_summary) {
        const detailedElement = document.getElementById('detailedDiscussion');
        if (detailedElement) {
            detailedElement.innerHTML = convertMarkdownToHtml(results.ai_summary);
        }
    }
    
    // Discussion Topics (일반회의 전용)
    if (results.discussion_topics && results.discussion_topics.length > 0) {
        const topicsContainer = document.getElementById('feedbackContent');
        if (topicsContainer) {
            let topicsHtml = '<div class="space-y-4">';
            topicsHtml += '<h4 class="font-semibold text-gray-800 mb-3">💬 논의 주제</h4>';
            
            results.discussion_topics.forEach((topic, index) => {
                topicsHtml += `
                    <div class="bg-green-50 p-4 rounded-lg border-l-4 border-green-400">
                        <h5 class="font-medium text-green-900">${topic.topic.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</h5>
                        <p class="text-sm text-green-800 mt-1"><strong>요약:</strong> ${topic.summary.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-green-700 mt-1"><strong>참여자:</strong> ${topic.participants.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                        <p class="text-sm text-green-700 mt-1"><strong>결정사항:</strong> ${topic.decisions.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')}</p>
                    </div>
                `;
            });
            
            topicsHtml += '</div>';
            topicsContainer.innerHTML = topicsHtml;
        }
    }
    
    // Action Items
    if ((results.leader_action_items && results.leader_action_items.length > 0) || 
        (results.member_action_items && results.member_action_items.length > 0)) {
        const actionsContainer = document.getElementById('qaContent');
        if (actionsContainer) {
            let actionsHtml = '<div class="space-y-4">';
            actionsHtml += '<h4 class="font-semibold text-gray-800 mb-3">✅ 액션 아이템</h4>';
            
            const allActionItems = [
                ...(results.leader_action_items || []).map(item => ({type: '리더', text: item})),
                ...(results.member_action_items || []).map(item => ({type: '멤버', text: item}))
            ];
            allActionItems.forEach((item, index) => {
                actionsHtml += `
                    <div class="bg-gray-50 p-4 rounded-lg border-l-4 border-gray-400">
                        <h5 class="font-medium text-gray-900">[${item.type}] ${item.text}</h5>
                    </div>
                `;
            });
            
            actionsHtml += '</div>';
            actionsContainer.innerHTML = actionsHtml;
        }
    }
    
    // 전체 스크립트
    const transcriptText = formatTranscript(results.transcript);
    document.getElementById('transcriptContent').innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${transcriptText}</p>`;
    
    // 처리 완료 후 첫 번째 탭(요약)으로 자동 전환
    const summaryTabBtn = document.querySelector('[data-tab="summary"]');
    if (summaryTabBtn) {
        summaryTabBtn.click();
    }
}

// Update participants UI based on meeting type
function updateParticipantsUI(isOneOnOne) {
    const participantsSection = document.getElementById('participantsSection');
    if (!participantsSection) return;
    
    const title = participantsSection.querySelector('h3');
    const description = participantsSection.querySelector('p');
    
    // 기존 참가자 데이터 초기화
    const leaderInput = document.getElementById('leaderName');
    const memberInput = document.getElementById('memberName');
    if (leaderInput) leaderInput.value = '';
    if (memberInput) memberInput.value = '';
    
    // 기존 컨테이너 제거 (완전 초기화)
    const existingContainers = participantsSection.querySelectorAll('.grid, .space-y-4');
    existingContainers.forEach(el => {
        if (!el.id || (!el.id.includes('weeklyMeetingQuickAdd') && !el.id.includes('planningMeetingQuickAdd'))) {
            el.remove();
        }
    });
    
    // 새 컨테이너 생성
    const container = document.createElement('div');
    
    // 빠른 추가 섹션 전에 삽입
    const quickAddSection = participantsSection.querySelector('#weeklyMeetingQuickAdd') || participantsSection.querySelector('#planningMeetingQuickAdd');
    if (quickAddSection) {
        participantsSection.insertBefore(container, quickAddSection);
    } else {
        participantsSection.appendChild(container);
    }
    
    if (isOneOnOne) {
        // 1on1: 리더/멤버 구분
        title.innerHTML = '<i class="ri-team-line mr-2 text-indigo-500"></i>회의 참석자 정보 (선택사항)';
        description.textContent = '참석자 정보를 입력하면 AI가 더 정확한 분석을 제공합니다.';
        
        container.className = 'grid md:grid-cols-2 gap-4';
        container.innerHTML = `
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    <i class="ri-user-line mr-1 text-indigo-500"></i>리더/매니저
                </label>
                <input 
                    type="text" 
                    id="leaderName"
                    placeholder="예: 김팀장"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent text-sm"
                >
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    <i class="ri-user-heart-line mr-1 text-indigo-500"></i>팀원/참가자
                </label>
                <input 
                    type="text" 
                    id="memberName"
                    placeholder="예: 이대리"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent text-sm"
                >
            </div>
        `;
    } else {
        // 다른 회의: 일반 참가자들
        title.innerHTML = '<i class="ri-team-line mr-2 text-indigo-500"></i>회의 참가자 (선택사항)';
        description.textContent = '회의 참가자들의 이름을 입력해주세요. 필요에 따라 추가할 수 있습니다.';
        
        container.className = 'space-y-4';
        container.innerHTML = `
            <div id="participantsContainer" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <div class="participant-input group relative">
                    <input 
                        type="text" 
                        placeholder="참가자 이름 (예: 김준희)"
                        class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent text-sm transition-colors"
                    >
                    <button type="button" onclick="removeParticipant(this)" class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100" title="참가자 제거">
                        <i class="ri-close-line text-sm"></i>
                    </button>
                </div>
            </div>
            <div class="flex justify-center">
                <button type="button" id="addParticipantBtn" class="px-4 py-2 border border-dashed border-gray-300 text-gray-600 rounded-lg hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors flex items-center justify-center">
                    <i class="ri-add-line mr-2"></i>참가자 추가
                </button>
            </div>
        `;
        
        // 참가자 추가 버튼 이벤트 리스너 추가
        setTimeout(() => {
            const addBtn = document.getElementById('addParticipantBtn');
            if (addBtn) {
                // 기존 이벤트 리스너 제거 후 새로 추가 (중복 방지)
                const newAddBtn = addBtn.cloneNode(true);
                addBtn.parentNode.replaceChild(newAddBtn, addBtn);
                newAddBtn.addEventListener('click', addParticipant);
            }
        }, 100);
    }
}

// 참가자 추가 함수
function addParticipant() {
    const container = document.getElementById('participantsContainer');
    if (!container) return;
    
    const participantDiv = document.createElement('div');
    participantDiv.className = 'participant-input group relative';
    participantDiv.innerHTML = `
        <input 
            type="text" 
            placeholder="참가자 이름 (예: 김준희)"
            class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent text-sm transition-colors"
        >
        <button type="button" onclick="removeParticipant(this)" class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100" title="참가자 제거">
            <i class="ri-close-line text-sm"></i>
        </button>
    `;
    
    container.appendChild(participantDiv);
}

// 참가자 제거 함수
function removeParticipant(button) {
    const container = document.getElementById('participantsContainer');
    if (!container) return;
    
    const participantDiv = button.closest('.participant-input');
    if (participantDiv && container.children.length > 1) {
        participantDiv.remove();
    }
}

// Update UI based on meeting type
function updateUIForMeetingType(type) {
    // 참석자 정보 섹션 업데이트
    const participantsSection = document.getElementById('participantsSection');
    const qaSection = document.getElementById('qaSection');
    
    if (participantsSection) {
        if (type === '1on1') {
            // 1on1: 리더/멤버 구분 형식
            participantsSection.style.display = 'block';
            updateParticipantsUI(true); // 리더/멤버 구분
        } else {
            // 다른 회의: 일반 참가자 목록 형식
            participantsSection.style.display = 'block';
            updateParticipantsUI(false); // 일반 참가자들
        }
    }
    
    // 주간회의 빠른 추가 버튼 표시/숨김
    const weeklyQuickAddBtn = document.getElementById('weeklyMeetingQuickAdd');
    if (weeklyQuickAddBtn) {
        if (type === 'weekly') {
            weeklyQuickAddBtn.style.display = 'block';
        } else {
            weeklyQuickAddBtn.style.display = 'none';
        }
    }
    
    // 기획회의 빠른 추가 버튼 표시/숨김
    const planningQuickAddBtn = document.getElementById('planningMeetingQuickAdd');
    if (planningQuickAddBtn) {
        if (type === 'planning') {
            planningQuickAddBtn.style.display = 'block';
        } else {
            planningQuickAddBtn.style.display = 'none';
        }
    }
    
    if (type === '1on1') {
        // 1on1일 때만 QA 섹션 표시
        if (qaSection) qaSection.style.display = 'block';
    } else {
        // 다른 회의 타입에서는 QA 섹션 숨김
        if (qaSection) qaSection.style.display = 'none';
    }
    
    // 탭 이름 업데이트
    const feedbackTab = document.querySelector('[data-tab="feedback"]');
    const qaTab = document.querySelector('[data-tab="qa"]');
    
    if (type === '1on1') {
        // 1on1용 탭 표시
        if (feedbackTab) {
            feedbackTab.innerHTML = '<i class="ri-feedback-line mr-2"></i>리더 피드백';
            feedbackTab.style.display = 'flex';
        }
        if (qaTab) {
            qaTab.innerHTML = '<i class="ri-question-answer-line mr-2"></i>Q&A 분석';
            qaTab.style.display = 'flex';
        }
    } else {
        // 주간회의, 일반회의, 기획회의는 피드백과 Q&A 탭 숨기기
        if (feedbackTab) {
            feedbackTab.style.display = 'none';
            // 피드백 탭이 활성화되어 있으면 요약 탭으로 전환
            if (feedbackTab.classList.contains('active-tab')) {
                tabButtons[0].click();
            }
        }
        if (qaTab) {
            qaTab.style.display = 'none';
            // Q&A 탭이 활성화되어 있으면 요약 탭으로 전환
            if (qaTab.classList.contains('active-tab')) {
                tabButtons[0].click();
            }
        }
    }
}

// Mock Results for Demo
function getMockResults() {
    // Return different mock data based on meeting type
    switch(selectedMeetingType) {
        case '1on1':
            return getMock1on1Results();
        case 'general':
            return getMockGeneralMeetingResults();
        case 'weekly':
            return getMockWeeklyMeetingResults();
        case 'planning':
            return getMockPlanningMeetingResults();
        default:
            return getMock1on1Results();
    }
}

// Mock Results for 1on1 Meeting
function getMock1on1Results() {
    return {
        summary: '이번 1on1 미팅에서는 프로젝트 진행 상황과 팀원의 성장 목표에 대해 논의했습니다. 현재 진행 중인 AI 프로젝트의 일정을 검토하고, 향후 3개월간의 개인 성장 계획을 수립했습니다.',
        decisions: [
            '다음 스프린트부터 새로운 기능 개발 착수',
            '주간 코드 리뷰 세션 도입',
            '팀 내 기술 공유 세미나 월 2회 진행'
        ],
        actionItems: [
            '프로젝트 로드맵 업데이트 (담당: 김준희, 기한: 8/15)',
            '코드 리뷰 가이드라인 작성 (담당: 이세현, 기한: 8/20)',
            '기술 세미나 주제 선정 (담당: 전체, 기한: 8/18)'
        ],
        leader_feedback: {
            positive: [
                '팀원의 의견을 적극적으로 경청하고 반영했습니다',
                '구체적인 액션 아이템과 기한을 명확히 설정했습니다',
                '긍정적인 분위기로 미팅을 진행했습니다'
            ],
            improvement: [
                '미팅 시간이 예정보다 길어졌습니다. 시간 관리에 신경 써주세요',
                '일부 논의 사항에서 구체적인 수치나 목표가 부족했습니다',
                '팀원의 발언 기회를 더 균등하게 배분하면 좋겠습니다'
            ]
        },
        qa: [
            {
                question: '현재 프로젝트 진행 상황은 어떤가요?',
                answer: '전체 일정의 60% 정도 완료되었으며, 주요 기능 개발은 예정대로 진행 중입니다. 다만 테스트 단계에서 약간의 지연이 있어 리소스 재배치를 검토 중입니다.'
            },
            {
                question: '팀원들의 성장을 위해 어떤 지원이 필요한가요?',
                answer: '기술 교육 프로그램 참여 기회와 멘토링 시스템이 필요합니다. 특히 AI/ML 분야의 전문 교육과 실무 프로젝트 경험을 쌓을 수 있는 기회를 원합니다.'
            },
            {
                question: '다음 분기 목표는 무엇인가요?',
                answer: '프로젝트 성공적 완료와 함께 팀 역량 강화에 집중할 예정입니다. 구체적으로는 코드 품질 개선, 자동화 도입, 그리고 지식 공유 문화 정착을 목표로 합니다.'
            }
        ],
        transcript: `[00:00] 리더: 안녕하세요, 오늘 1on1 미팅을 시작하겠습니다. 최근 프로젝트 진행 상황은 어떤가요?

[00:15] 팀원: 네, 현재 전체 일정의 60% 정도 완료했습니다. 주요 기능 개발은 예정대로 진행되고 있는데, 테스트 단계에서 약간의 지연이 있습니다.

[00:35] 리더: 테스트 지연의 원인은 무엇인가요?

[00:42] 팀원: 예상보다 버그가 많이 발견되어서 수정에 시간이 걸리고 있습니다. 특히 통합 테스트에서 문제가 많이 나타나고 있어요.

[01:00] 리더: 그렇군요. 리소스 재배치가 필요할 것 같은데, 어떻게 생각하시나요?

[01:12] 팀원: 동의합니다. 개발 인력 일부를 테스트 지원으로 전환하면 도움이 될 것 같습니다.

[이하 생략...]`
    };
}

// Mock Results for General Meeting
function getMockGeneralMeetingResults() {
    return {
        summary: '프로젝트 현황 점검 및 팀 협업 방안을 논의했습니다. 각 팀별 진행 상황을 공유하고, 발생한 이슈들에 대한 해결 방안을 모색했습니다. 다음 단계 액션 플랜을 수립했습니다.',
        decisions: [
            'API 개발 일정을 1주일 앞당기기로 결정',
            'QA 팀과 개발팀 간 일일 스탠드업 미팅 도입',
            '디자인 리뷰 프로세스 개선안 채택',
            '리소스 재배치: 프론트엔드 개발 인력 보강'
        ],
        actionItems: [
            'API 명세서 업데이트 (담당: 백엔드팀, 기한: 8/14)',
            '테스트 시나리오 작성 (담당: QA팀, 기한: 8/16)',
            'UI 컴포넌트 라이브러리 구축 (담당: 프론트엔드팀, 기한: 8/20)',
            '성능 모니터링 대시보드 구축 (담당: DevOps팀, 기한: 8/25)'
        ],
        leader_feedback: null, // General meetings don't have leader feedback
        qa: [
            {
                question: '현재 가장 큰 기술적 도전 과제는 무엇인가요?',
                answer: '대용량 데이터 처리 시 발생하는 성능 이슈와 실시간 동기화 문제가 주요 과제입니다. 캐싱 전략과 비동기 처리 방식을 개선하여 해결할 예정입니다.'
            },
            {
                question: '프로젝트 일정에 리스크는 없나요?',
                answer: '백엔드 API 개발이 약간 지연되고 있지만, 인력 재배치를 통해 일정 내 완료 가능할 것으로 예상됩니다.'
            }
        ],
        transcript: `[00:00] 진행자: 오늘 회의를 시작하겠습니다. 먼저 각 팀별 진행 상황을 공유해주세요.

[00:30] 개발팀: 현재 API 개발 70% 완료했습니다. 인증 모듈과 데이터 처리 부분이 완성되었고...

[이하 생략...]`
    };
}

// Mock Results for Weekly Meeting
function getMockWeeklyMeetingResults() {
    return {
        summary: '이번 주 프로젝트 진행 현황과 다음 주 계획을 검토했습니다. 전체적으로 일정대로 진행되고 있으며, 몇 가지 이슈사항에 대한 대응 방안을 논의했습니다.',
        decisions: [
            '금주 목표 달성률: 85%',
            '차주 우선순위: 버그 수정 > 신규 기능 개발',
            '고객 피드백 반영 사항 우선 처리',
            '팀 빌딩 이벤트 날짜 확정 (8/30)'
        ],
        actionItems: [
            '주간 보고서 작성 및 공유 (담당: PM, 기한: 매주 금요일)',
            '버그 트래킹 시스템 업데이트 (담당: QA팀, 기한: 8/13)',
            '고객 미팅 준비 자료 작성 (담당: 영업팀, 기한: 8/15)',
            '차주 스프린트 계획 수립 (담당: 전체, 기한: 8/16)'
        ],
        leader_feedback: null,
        qa: [
            {
                question: '이번 주 주요 성과는 무엇인가요?',
                answer: '로그인 시스템 개선 완료, 데이터베이스 최적화로 응답 속도 30% 향상, 고객사 요구사항 3건 반영 완료했습니다.'
            },
            {
                question: '다음 주 중점 추진 사항은?',
                answer: '크리티컬 버그 3건 수정, 사용자 대시보드 UI 개선, 성능 테스트 진행 예정입니다.'
            },
            {
                question: '팀원들의 건의사항이 있나요?',
                answer: '원격 근무 가이드라인 명확화와 협업 도구 추가 도입에 대한 요청이 있었습니다.'
            }
        ],
        transcript: `[00:00] PM: 주간 회의를 시작하겠습니다. 이번 주 진행 상황부터 공유하겠습니다.

[00:15] PM: 전체 진행률은 85%로 목표 대비 양호한 편입니다...

[이하 생략...]`
    };
}

// Mock Results for Planning Meeting
function getMockPlanningMeetingResults() {
    return {
        summary: '신규 프로젝트 "AI 기반 고객 서비스 자동화 시스템" 기획을 위한 브레인스토밍과 초기 전략 수립을 진행했습니다. 시장 분석, 기술 스택 선정, 로드맵 초안을 작성했습니다.',
        decisions: [
            '프로젝트 코드명: "SmartCS" 확정',
            '개발 방법론: Agile/Scrum 채택',
            '기술 스택: React + FastAPI + PostgreSQL + Redis',
            'MVP 출시 목표: 2024년 Q1',
            '초기 예산: 5억원 책정'
        ],
        actionItems: [
            '시장 조사 보고서 작성 (담당: 기획팀, 기한: 8/20)',
            '기술 POC 개발 (담당: R&D팀, 기한: 8/30)',
            '투자 제안서 초안 작성 (담당: 경영기획팀, 기한: 8/25)',
            '경쟁사 분석 자료 준비 (담당: 마케팅팀, 기한: 8/18)',
            '인력 채용 계획 수립 (담당: HR팀, 기한: 8/22)'
        ],
        leader_feedback: null,
        qa: [
            {
                question: '이 프로젝트의 핵심 차별화 포인트는?',
                answer: '한국어 자연어 처리에 특화된 AI 모델과 업종별 커스터마이징이 가능한 유연한 아키텍처가 핵심 경쟁력입니다.'
            },
            {
                question: '예상되는 주요 리스크는?',
                answer: '기술적으로는 AI 모델의 정확도, 비즈니스적으로는 시장 진입 시기와 경쟁사 대응이 주요 리스크입니다.'
            },
            {
                question: 'ROI는 언제쯤 달성 가능한가요?',
                answer: '초기 투자 회수는 출시 후 18개월, 손익분기점은 24개월로 예상하고 있습니다.'
            }
        ],
        transcript: `[00:00] 기획팀장: 오늘은 신규 프로젝트 기획 회의를 진행하겠습니다.

[00:10] CTO: 먼저 기술적 타당성부터 검토해보겠습니다...

[이하 생략...]`
    };
}

// Tab Navigation
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const targetTab = button.getAttribute('data-tab');
        
        // Update active tab button
        tabButtons.forEach(btn => btn.classList.remove('active-tab'));
        button.classList.add('active-tab');
        
        // Show corresponding content
        tabContents.forEach(content => {
            if (content.id === `${targetTab}Tab`) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        });
    });
});

// New Analysis Button
newAnalysisBtn.addEventListener('click', () => {
    // Reset everything
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    audioBlob = null;
    analyzeBtn.disabled = true;
    recordingTime.classList.add('hidden');
    timeDisplay.textContent = '00:00';
    recordingSeconds = 0;
    
    // Clear Q&A data
    clearQAData();
    
    // Hide results, show upload section
    resultsSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    
    // Reset to first tab
    tabButtons[0].click();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// 복사 기능 이벤트 리스너들
copySummaryBtn.addEventListener('click', async () => {
    if (!currentAnalysisResults) {
        alert('복사할 분석 결과가 없습니다.');
        return;
    }
    
    try {
        let summaryText = `# ${currentAnalysisResults.title || '미팅 분석 결과'}\n\n`;
        
        // 액션 아이템과 상세 요약 추출
        if (currentAnalysisResults.leader_action_items || currentAnalysisResults.member_action_items) {
            summaryText += `## 액션 아이템\n`;
            if (currentAnalysisResults.leader_action_items && currentAnalysisResults.leader_action_items.length > 0) {
                summaryText += `### 리더\n${currentAnalysisResults.leader_action_items.map(item => `- ${item}`).join('\n')}\n\n`;
            }
            if (currentAnalysisResults.member_action_items && currentAnalysisResults.member_action_items.length > 0) {
                summaryText += `### 멤버\n${currentAnalysisResults.member_action_items.map(item => `- ${item}`).join('\n')}\n\n`;
            }
        }
        summaryText += `## 상세 요약\n${currentAnalysisResults.ai_summary || '상세 내용이 없습니다.'}`;
        
        await navigator.clipboard.writeText(summaryText);
        showCopySuccess(copySummaryBtn, '요약이 복사되었습니다!');
    } catch (err) {
        console.error('복사 실패:', err);
        alert('복사에 실패했습니다. 다시 시도해주세요.');
    }
});

copyMarkdownBtn.addEventListener('click', async () => {
    if (!currentAnalysisResults) {
        alert('복사할 분석 결과가 없습니다.');
        return;
    }
    
    try {
        let markdownText = `# ${currentAnalysisResults.title || '미팅 분석 결과'}\n\n`;
        
        // 전체 상세 내용을 마크다운 형태로 복사
        if (currentAnalysisResults.ai_summary) {
            markdownText += currentAnalysisResults.ai_summary;
        } else {
            markdownText += '상세 내용이 없습니다.';
        }
        
        await navigator.clipboard.writeText(markdownText);
        showCopySuccess(copyMarkdownBtn, '마크다운이 복사되었습니다!');
    } catch (err) {
        console.error('복사 실패:', err);
        alert('복사에 실패했습니다. 다시 시도해주세요.');
    }
});

copyTranscriptBtn.addEventListener('click', async () => {
    if (!currentAnalysisResults || !currentAnalysisResults.transcript) {
        alert('복사할 전사 내용이 없습니다.');
        return;
    }
    
    try {
        const transcriptText = `# 회의 전사 내용\n\n${currentAnalysisResults.transcript}`;
        await navigator.clipboard.writeText(transcriptText);
        showCopySuccess(copyTranscriptBtn, '전사 내용이 복사되었습니다!');
    } catch (err) {
        console.error('복사 실패:', err);
        alert('복사에 실패했습니다. 다시 시도해주세요.');
    }
});

// 복사 성공 피드백 표시 함수
function showCopySuccess(button, message) {
    const originalText = button.innerHTML;
    button.innerHTML = `<i class="ri-check-line mr-2"></i>${message}`;
    button.classList.add('bg-green-500', 'text-white');
    button.classList.remove('bg-green-100', 'text-green-700', 'bg-blue-100', 'text-blue-700', 'bg-gray-100', 'text-gray-700');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('bg-green-500', 'text-white');
        
        // 원래 색상으로 복원
        if (button.id === 'copySummaryBtn') {
            button.classList.add('bg-green-100', 'text-green-700');
        } else if (button.id === 'copyMarkdownBtn') {
            button.classList.add('bg-blue-100', 'text-blue-700');
        } else if (button.id === 'copyTranscriptBtn') {
            button.classList.add('bg-gray-100', 'text-gray-700');
        }
    }, 2000);
}

// 주간회의 참석자 빠른 추가 함수
function addWeeklyMembers() {
    const weeklyMembers = [
        "김동영", "지유진", "김지현", "박요한", "이민희", 
        "최재준", "김경민", "양현빈", "장세현", "김준희"
    ];
    
    console.log('🚀 주간회의 참석자 추가 시작:', weeklyMembers);
    
    // 현재 회의 타입이 주간회의가 아니면 먼저 UI를 업데이트
    if (selectedMeetingType !== 'weekly') {
        console.log('⚠️ 회의 타입을 주간회의로 전환합니다.');
        selectedMeetingType = 'weekly';
        // 버튼 상태 업데이트
        document.querySelectorAll('.meeting-type-btn').forEach(btn => {
            btn.classList.remove('active-type');
            if (btn.getAttribute('data-type') === 'weekly') {
                btn.classList.add('active-type');
            }
        });
        // UI 업데이트
        updateUIForMeetingType('weekly');
        // 짧은 대기 후 다시 시도
        setTimeout(() => addWeeklyMembers(), 200);
        return;
    }
    
    // 참가자 컨테이너 찾기
    const participantContainer = document.getElementById('participantsContainer');
    if (!participantContainer) {
        console.error('❌ 참가자 컨테이너를 찾을 수 없습니다');
        return;
    }
    
    // 기존 참가자들 모두 제거
    const existingParticipants = participantContainer.querySelectorAll('.participant-input');
    console.log('🗑️ 기존 참가자 항목 제거:', existingParticipants.length);
    existingParticipants.forEach(item => item.remove());
    
    // 각 참가자를 순차적으로 추가하는 비동기 함수
    async function addMembersSequentially() {
        for (let i = 0; i < weeklyMembers.length; i++) {
            const member = weeklyMembers[i];
            console.log(`➕ 참가자 추가 중 (${i + 1}/${weeklyMembers.length}):`, member);
            
            // 새 참가자 입력 필드 생성
            const participantDiv = document.createElement('div');
            participantDiv.className = 'participant-input group relative';
            participantDiv.innerHTML = `
                <input 
                    type="text" 
                    placeholder="참가자 이름 (예: 김준희)"
                    value="${member}"
                    class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent text-sm transition-colors"
                >
                <button type="button" onclick="removeParticipant(this)" class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100" title="참가자 제거">
                    <i class="ri-close-line text-sm"></i>
                </button>
            `;
            
            // 컨테이너에 추가
            participantContainer.appendChild(participantDiv);
            
            console.log(`✅ ${member} 입력 완료`);
            
            // 다음 참가자 추가 전에 50ms 대기 (더 안정적)
            await new Promise(resolve => setTimeout(resolve, 50));
        }
    }
    
    // 순차 추가 실행
    addMembersSequentially().then(() => {
        console.log('✅ 주간회의 참석자 전체 추가 완료');
        
        // 버튼 상태 변경
        const btn = document.getElementById('addWeeklyMembersBtn');
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="ri-check-line mr-1"></i>완료';
            btn.style.backgroundColor = '#10b981';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.backgroundColor = '#6366f1';
            }, 2000);
        }
    });
}

// 기획회의 참석자 빠른 추가 함수
function addPlanningMembers() {
    const planningMembers = [
        "김동영", "지유진", "김지현", "이민희", "양현빈", "장세현", "김준희"
    ];
    
    console.log('🚀 기획회의 참석자 추가 시작:', planningMembers);
    
    // 현재 회의 타입이 기획회의가 아니면 먼저 UI를 업데이트
    if (selectedMeetingType !== 'planning') {
        console.log('⚠️ 회의 타입을 기획회의로 전환합니다.');
        selectedMeetingType = 'planning';
        // 버튼 상태 업데이트
        document.querySelectorAll('.meeting-type-btn').forEach(btn => {
            btn.classList.remove('active-type');
            if (btn.getAttribute('data-type') === 'planning') {
                btn.classList.add('active-type');
            }
        });
        // UI 업데이트
        updateUIForMeetingType('planning');
        // 짧은 대기 후 다시 시도
        setTimeout(() => addPlanningMembers(), 200);
        return;
    }
    
    // 참가자 컨테이너 찾기
    const participantContainer = document.getElementById('participantsContainer');
    if (!participantContainer) {
        console.error('❌ 참가자 컨테이너를 찾을 수 없습니다');
        return;
    }
    
    // 기존 참가자들 모두 제거
    const existingParticipants = participantContainer.querySelectorAll('.participant-input');
    console.log('🗑️ 기존 참가자 항목 제거:', existingParticipants.length);
    existingParticipants.forEach(item => item.remove());
    
    // 각 참가자를 순차적으로 추가하는 비동기 함수
    async function addMembersSequentially() {
        for (let i = 0; i < planningMembers.length; i++) {
            const member = planningMembers[i];
            console.log(`➕ 참가자 추가 중 (${i + 1}/${planningMembers.length}):`, member);
            
            // 새 참가자 입력 필드 생성
            const participantDiv = document.createElement('div');
            participantDiv.className = 'participant-input group relative';
            participantDiv.innerHTML = `
                <input 
                    type="text" 
                    placeholder="참가자 이름 (예: 김준희)"
                    value="${member}"
                    class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent text-sm transition-colors"
                >
                <button type="button" onclick="removeParticipant(this)" class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100" title="참가자 제거">
                    <i class="ri-close-line text-sm"></i>
                </button>
            `;
            
            // 컨테이너에 추가
            participantContainer.appendChild(participantDiv);
            
            console.log(`✅ ${member} 입력 완료`);
            
            // 다음 참가자 추가 전에 50ms 대기 (더 안정적)
            await new Promise(resolve => setTimeout(resolve, 50));
        }
    }
    
    // 순차 추가 실행
    addMembersSequentially().then(() => {
        console.log('✅ 기획회의 참석자 전체 추가 완료');
        
        // 버튼 상태 변경
        const btn = document.getElementById('addPlanningMembersBtn');
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="ri-check-line mr-1"></i>완료';
            btn.style.backgroundColor = '#10b981';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.backgroundColor = '#9333ea'; // purple-600
            }, 2000);
        }
    });
}