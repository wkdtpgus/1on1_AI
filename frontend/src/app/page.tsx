'use client';

import { useState } from 'react';
import TemplateForm, { FormData } from '@/components/TemplateForm';
import ResultDisplay from '@/components/ResultDisplay';

export interface GeneratedData {
  title: string;
  guide: string | null; // 가이드는 나중에 생성되므로 null일 수 있음
  questions: Record<string, string>;
}

export default function Home() {
  const [result, setResult] = useState<GeneratedData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGuideLoading, setIsGuideLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentFormData, setCurrentFormData] = useState<FormData | null>(null);

  const handleGenerate = async (formData: FormData) => {
    setIsLoading(true);
    setResult(null);
    setError(null);
    setCurrentFormData(formData); // 가이드 생성 시 사용하기 위해 폼 데이터 저장

    // --- 백엔드 스키마에 맞게 값 변환 ---
    const questionCountMap: { [key: string]: 'Simple' | 'Standard' | 'Advanced' } = {
      simple: 'Simple',
      standard: 'Standard',
      deep: 'Advanced',
    };
    const toneAndMannerMap: { [key: string]: string } = {
      polite: 'Formal',
      casual: 'Casual',
    };
    const questionTypeMap: { [key: string]: string } = {
        experience: 'Experience/Story-based',
        reflection: 'Reflection/Thought-provoking',
        action: 'Action/Implementation-focused',
        relationship: 'Relationship/Collaboration',
        growth: 'Growth/Goal-oriented',
        multiple_choice: 'Multiple choice',
    };
    // --- 변환 로직 끝 ---

    // 프론트엔드 폼 데이터를 백엔드 스키마에 맞게 변환
    const apiRequestData = {
      user_id: formData.userId, // 'test-user-id' 대신 선택된 값 사용
      target_info: formData.recipient,
      purpose: formData.topic,
      detailed_context: formData.context,
      num_questions: questionCountMap[formData.questionCount],
      question_composition: Object.entries(formData.questionTypes)
        .filter(([, checked]) => checked)
        .map(([type]) => questionTypeMap[type as keyof typeof questionTypeMap])
        .join(', ') || "Experience/Story-based", // 하나도 선택 안됐을 경우 기본값
      tone_and_manner: toneAndMannerMap[formData.toneAndManner],
      language: formData.language, // formData에서 직접 가져오도록 수정
      include_guide: false, // 가이드는 따로 생성하므로 false
    };

    try {
      // 1. 템플릿(질문) 생성 API 호출
      const templateResponse = await fetch('http://127.0.0.1:8000/api/template?generation_type=template', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(apiRequestData),
      });

      if (!templateResponse.ok) {
        throw new Error(`템플릿 생성 실패: ${templateResponse.statusText}`);
      }
      
      const templateData = await templateResponse.json();
      
      setResult({
        title: formData.topic,
        guide: null, // 가이드는 아직 생성되지 않음
        questions: templateData.generated_questions,
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateGuide = async () => {
    if (!result || !currentFormData) return;
    
    setIsGuideLoading(true);
    setError(null);

    // --- 백엔드 스키마에 맞게 값 변환 ---
    const questionCountMap: { [key: string]: 'Simple' | 'Standard' | 'Advanced' } = { simple: 'Simple', standard: 'Standard', deep: 'Advanced' };
    const toneAndMannerMap: { [key: string]: string } = { polite: 'Formal', casual: 'Casual' };
    const questionTypeMap: { [key: string]: string } = {
        experience: 'Experience/Story-based',
        reflection: 'Reflection/Thought-provoking',
        action: 'Action/Implementation-focused',
        relationship: 'Relationship/Collaboration',
        growth: 'Growth/Goal-oriented',
        multiple_choice: 'Multiple choice',
    };

    const guideRequestData = {
      user_id: currentFormData.userId,
      target_info: currentFormData.recipient,
      purpose: currentFormData.topic,
      detailed_context: currentFormData.context,
      num_questions: questionCountMap[currentFormData.questionCount],
      question_composition: Object.entries(currentFormData.questionTypes).filter(([, checked]) => checked).map(([type]) => questionTypeMap[type as keyof typeof questionTypeMap]).join(', ') || "Experience/Story-based",
      tone_and_manner: toneAndMannerMap[currentFormData.toneAndManner],
      language: currentFormData.language, // formData에서 직접 가져오도록 수정
      include_guide: true,
      generated_questions: result.questions,
    };
    
    try {
        const guideResponse = await fetch('http://127.0.0.1:8000/api/template?generation_type=guide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(guideRequestData),
        });
        
        if (!guideResponse.ok) {
            throw new Error(`가이드 생성 실패: ${guideResponse.statusText}`);
        }
        
        const reader = guideResponse.body?.getReader();
        if (!reader) throw new Error("가이드 응답을 읽을 수 없습니다.");
        
        const decoder = new TextDecoder();
        
        // 가이드 스트리밍 시작 시, guide 필드를 빈 문자열로 초기화
        setResult(prev => prev ? { ...prev, guide: "" } : null);

        let buffer = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // SSE 메시지 형식 (data: ...)으로 분리
            const parts = buffer.split("\n\n");
            buffer = parts.pop() || ""; // 마지막 불완전한 부분은 버퍼에 남김

            for (const part of parts) {
                if (part.startsWith("data: ")) {
                    const content = part.substring(6).trim();
                    try {
                        // "..." 형식의 JSON 문자열일 경우 파싱
                        const parsedContent = JSON.parse(content);
                        setResult(prev => prev ? { ...prev, guide: (prev.guide || "") + parsedContent } : null);
                    } catch { // 'e' is not used, so remove it
                        // 일반 문자열일 경우
                        setResult(prev => prev ? { ...prev, guide: (prev.guide || "") + content } : null);
                    }
                }
            }
        }

    } catch (err) {
        setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
        setIsGuideLoading(false);
    }
  };


  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
      <TemplateForm onGenerate={handleGenerate} isLoading={isLoading} />
      <ResultDisplay 
        result={result} 
        isLoading={isLoading} 
        isGuideLoading={isGuideLoading}
        onGenerateGuide={handleGenerateGuide}
        error={error} 
      />
    </div>
  );
}
