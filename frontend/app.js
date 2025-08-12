// Audio Recording Variables
let mediaRecorder;
let audioChunks = [];
let recordingTimer;
let recordingSeconds = 0;
let audioBlob = null;
let selectedMeetingType = '1on1';

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
const testBtn = document.getElementById('testBtn');

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
            const results = await analyzeWithProgress(
                audioBlob, 
                (progress, text) => {
                    progressBar.style.width = `${progress}%`;
                    progressText.textContent = text;
                },
                selectedMeetingType  // 선택된 미팅 타입 전달
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
    console.log('🔍 results.quick_review 존재:', !!results.quick_review);
    console.log('🔍 results.detailed_discussion 존재:', !!results.detailed_discussion);
    
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
    } else if (results.quick_review || results.detailed_discussion) {
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
    if (results.quick_review) {
        const takeawaysElement = document.getElementById('quickReviewTakeaways');
        const decisionsElement = document.getElementById('quickReviewDecisions');
        const actionsElement = document.getElementById('quickReviewActions');
        const supportElement = document.getElementById('quickReviewSupport');
        
        if (takeawaysElement) takeawaysElement.textContent = results.quick_review.key_takeaways || '핵심 내용이 없습니다.';
        if (decisionsElement) decisionsElement.innerHTML = formatTextWithBreaks(results.quick_review.decisions_made || '결정사항이 없습니다.');
        if (actionsElement) actionsElement.innerHTML = formatTextWithBreaks(results.quick_review.action_items || '액션 아이템이 없습니다.');
        if (supportElement) supportElement.innerHTML = formatTextWithBreaks(results.quick_review.support_needs_blockers || '지원 요청사항이 없습니다.');
    } else {
        console.log('❌ No quick_review data found');
    }
    
    // 세부 상세 요약 업데이트
    if (results.detailed_discussion) {
        const detailedElement = document.getElementById('detailedDiscussion');
        if (detailedElement) {
            // 마크다운을 HTML로 변환하여 적용
            detailedElement.innerHTML = convertMarkdownToHtml(results.detailed_discussion);
        } else {
            console.log('❌ detailedDiscussion 요소를 찾을 수 없습니다');
        }
    } else {
        console.log('❌ No detailed_discussion data found');
    }
    
    // 피드백 탭 업데이트
    if (results.feedback && Array.isArray(results.feedback)) {
        const feedbackHtml = results.feedback.map(item => `
            <div class="bg-red-50 border-l-4 border-red-500 rounded-lg p-6">
                <h5 class="font-semibold text-red-900 mb-3">${item.title}</h5>
                <div class="space-y-3">
                    <div>
                        <span class="font-medium text-red-800">상황:</span>
                        <p class="text-gray-700 mt-1">${item.situation}</p>
                    </div>
                    <div>
                        <span class="font-medium text-red-800">제안:</span>
                        <p class="text-gray-700 mt-1">${item.suggestion}</p>
                    </div>
                    <div>
                        <span class="font-medium text-red-800">중요성:</span>
                        <p class="text-gray-700 mt-1">${item.importance}</p>
                    </div>
                    <div>
                        <span class="font-medium text-red-800">실행 방안:</span>
                        <p class="text-gray-700 mt-1">${item.implementation}</p>
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
            `<li class="text-gray-700 flex items-start"><i class="ri-check-line text-green-600 mr-2 mt-1"></i>${aspect}</li>`
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
        
        const qaHtml = results.qa_summary.map((item, index) => `
            <div class="border-l-4 border-indigo-500 pl-6 py-4">
                <p class="font-semibold text-gray-900 mb-2">Q${index + 1}: ${item.question || '질문이 없습니다'}</p>
                <p class="text-gray-700">A: ${item.answer || '답변이 없습니다'}</p>
            </div>
        `).join('');
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
        transcriptElement.innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${results.transcript || '스크립트를 불러올 수 없습니다.'}</p>`;
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
    if (results.feedback) {
        const positiveHtml = (results.feedback.positive || []).map(p => 
            `<li class="text-gray-700 flex items-start"><i class="ri-check-line text-green-600 mr-2 mt-1"></i>${p}</li>`
        ).join('');
        document.getElementById('positiveAspects').innerHTML = positiveHtml;
        
        // 개선점을 간단한 형태로 표시
        const improvementHtml = (results.feedback.improvement || []).map(item => `
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
    document.getElementById('transcriptContent').innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${results.transcript}</p>`;
}

// 텍스트에 줄바꿈 포맷팅 적용
function formatTextWithBreaks(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>').replace(/•/g, '•');
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
        
        // 헤딩 처리
        if (line.match(/^### /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            html.push(`<h3 class="text-lg font-semibold text-gray-900 mt-6 mb-3">${line.replace(/^### /, '')}</h3>`);
        } else if (line.match(/^## /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            html.push(`<h2 class="text-xl font-bold text-gray-900 mt-8 mb-4">${line.replace(/^## /, '')}</h2>`);
        } else if (line.match(/^# /)) {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            html.push(`<h1 class="text-2xl font-bold text-gray-900 mt-8 mb-4">${line.replace(/^# /, '')}</h1>`);
        }
        // 불릿 포인트 처리
        else if (line.match(/^[•-] /)) {
            if (!inList) {
                html.push('<ul class="list-none space-y-1 mb-4">');
                inList = true;
            }
            const content = line.replace(/^[•-] /, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<li class="text-gray-700 ml-4">• ${content}</li>`);
        }
        // 일반 텍스트 처리
        else {
            if (inList) {
                html.push('</ul>');
                inList = false;
            }
            // 굵은 글씨 처리
            const content = line.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html.push(`<p class="text-gray-700 mb-3">${content}</p>`);
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
    
    // Quick Review 섹션 업데이트 (기획회의용으로 변경)
    if (results.quick_review) {
        const takeawaysElement = document.getElementById('quickReviewTakeaways');
        const decisionsElement = document.getElementById('quickReviewDecisions');
        const actionsElement = document.getElementById('quickReviewActions');
        const supportElement = document.getElementById('quickReviewSupport');
        
        if (takeawaysElement) takeawaysElement.textContent = results.quick_review.key_planning_outcomes || '기획 결과가 없습니다.';
        if (decisionsElement) decisionsElement.innerHTML = formatTextWithBreaks(results.quick_review.major_decisions || '결정사항이 없습니다.');
        if (actionsElement) actionsElement.innerHTML = formatTextWithBreaks(results.quick_review.action_items || '액션 아이템이 없습니다.');
        if (supportElement) supportElement.innerHTML = formatTextWithBreaks(results.quick_review.resource_timeline || '리소스 및 타임라인 정보가 없습니다.');
    }
    
    // 세부 상세 요약 업데이트
    if (results.detailed_discussion) {
        const detailedElement = document.getElementById('detailedDiscussion');
        if (detailedElement) {
            detailedElement.innerHTML = convertMarkdownToHtml(results.detailed_discussion);
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
                        <p class="text-gray-700 mt-1">${item.insight}</p>
                    </div>
                    <div>
                        <span class="font-medium text-blue-800">근거:</span>
                        <p class="text-gray-700 mt-1">${item.rationale}</p>
                    </div>
                    <div>
                        <span class="font-medium text-blue-800">예상 영향:</span>
                        <p class="text-gray-700 mt-1">${item.impact}</p>
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
            `<li class="text-gray-700 flex items-start"><i class="ri-lightbulb-line text-yellow-600 mr-2 mt-1"></i>${idea}</li>`
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
                <p class="font-semibold text-gray-900 mb-2">액션: ${item.item}</p>
                <div class="text-sm space-y-1">
                    <p class="text-gray-700">담당자: ${item.owner || '미정'}</p>
                    <p class="text-gray-700">마감일: ${item.deadline || '미정'}</p>
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
        transcriptElement.innerHTML = `<p class="text-gray-700 whitespace-pre-wrap">${results.transcript || '스크립트를 불러올 수 없습니다.'}</p>`;
    }
    
    // 처리 완료 후 첫 번째 탭(요약)으로 자동 전환
    const summaryTabBtn = document.querySelector('[data-tab="summary"]');
    if (summaryTabBtn) {
        summaryTabBtn.click();
    }
}

// Update UI based on meeting type
function updateUIForMeetingType(type) {
    // 탭 이름 업데이트
    const feedbackTab = document.querySelector('[data-tab="feedback"]');
    const qaTab = document.querySelector('[data-tab="qa"]');
    
    if (type === 'planning') {
        // 기획회의용 탭 이름 변경
        if (feedbackTab) {
            feedbackTab.innerHTML = '<i class="ri-lightbulb-line mr-2"></i>전략 인사이트';
            feedbackTab.style.display = 'flex';
        }
        if (qaTab) {
            qaTab.innerHTML = '<i class="ri-task-line mr-2"></i>다음 단계';
        }
    } else if (type === '1on1') {
        // 1on1용 탭 이름 (원래대로)
        if (feedbackTab) {
            feedbackTab.innerHTML = '<i class="ri-feedback-line mr-2"></i>리더 피드백';
            feedbackTab.style.display = 'flex';
        }
        if (qaTab) {
            qaTab.innerHTML = '<i class="ri-question-answer-line mr-2"></i>Q&A 분석';
        }
    } else {
        // 다른 미팅 타입은 피드백 탭 숨기기
        if (feedbackTab) {
            feedbackTab.style.display = 'none';
            // 피드백 탭이 활성화되어 있으면 요약 탭으로 전환
            if (feedbackTab.classList.contains('active-tab')) {
                tabButtons[0].click();
            }
        }
        if (qaTab) {
            qaTab.innerHTML = '<i class="ri-question-answer-line mr-2"></i>Q&A 분석';
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
        feedback: {
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
        feedback: null, // General meetings don't have leader feedback
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
        feedback: null,
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
        feedback: null,
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
    
    // Hide results, show upload section
    resultsSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    
    // Reset to first tab
    tabButtons[0].click();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Test Button Event Handler
testBtn.addEventListener('click', async () => {
    try {
        progressSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        
        // Show loading
        progressBar.style.width = '20%';
        progressText.textContent = '샘플 데이터 로딩 중...';
        
        // Fetch test result
        const response = await fetch('http://localhost:8000/api/test-result');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Simulate progress
        progressBar.style.width = '100%';
        progressText.textContent = '완료!';
        
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (data.status === 'success') {
            showResults(data);
        } else {
            throw new Error(data.message || '샘플 데이터 로드 실패');
        }
        
    } catch (error) {
        console.error('Test result error:', error);
        alert(`샘플 결과 로드 중 오류: ${error.message}`);
        progressSection.classList.add('hidden');
    }
});