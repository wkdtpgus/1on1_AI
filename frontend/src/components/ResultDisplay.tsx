'use client';

import React, { useState, useEffect } from 'react';
import { GeneratedData } from '../app/page';
import Button from './Button';

interface ResultDisplayProps {
  result: GeneratedData | null;
  isLoading: boolean;
  isGuideLoading: boolean;
  onGenerateGuide: () => void;
  error: string | null;
}

const LoadingSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 bg-gray-200 rounded w-3/4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 rounded"></div>
      <div className="h-4 bg-gray-200 rounded w-5/6"></div>
    </div>
    <div className="space-y-3 pt-6">
      <div className="h-6 bg-gray-200 rounded w-1/2"></div>
      <div className="h-10 bg-gray-200 rounded"></div>
      <div className="h-10 bg-gray-200 rounded"></div>
      <div className="h-10 bg-gray-200 rounded"></div>
    </div>
  </div>
);

const GuideContent: React.FC<{ text: string }> = ({ text }) => {
    const [cleanedText, setCleanedText] = useState("");

    useEffect(() => {
        let processedText = text;

        // 1. ```json 과 같은 마크다운 코드 블록 제거
        processedText = processedText.replace(/^```json\s*|\s*```$/g, '');

        // 2. JSON 구조(중괄호, 필드명 등)를 제거하여 순수 내용만 추출
        const contentMatch = processedText.match(/"usage_guide"\s*:\s*"(.*)/s);
        
        if (contentMatch && contentMatch[1]) {
            processedText = contentMatch[1];
            // 스트리밍 데이터의 마지막에 올 수 있는 "}, ` 등을 제거
            processedText = processedText.replace(/"\s*}\s*$/, '');
        } else {
            // 아직 "usage_guide" 필드가 나타나기 전의 초기 데이터 처리
            processedText = processedText.replace(/[{\s]*/, '');
        }

        // 3. 이스케이프된 줄바꿈 문자를 실제 줄바꿈으로 변경
        processedText = processedText.replace(/\\n/g, '\n');

        setCleanedText(processedText);
    }, [text]);

    return (
        <div className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
            {cleanedText}
        </div>
    );
};


const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, isLoading, isGuideLoading, onGenerateGuide, error }) => {
  if (isLoading) {
    return <div className="bg-white p-8 rounded-lg shadow-md"><LoadingSkeleton /></div>;
  }
  if (error) {
    return (
      <div className="bg-white p-8 rounded-lg shadow-md h-fit text-center text-red-500">
        <h3 className="text-lg font-semibold">오류 발생</h3>
        <p className="mt-2 text-sm">{error}</p>
      </div>
    );
  }
  if (!result) {
    return (
      <div className="bg-white p-8 rounded-lg shadow-md h-fit text-center text-gray-500">
        <p>좌측 폼을 채우고 템플릿을 생성해주세요.</p>
        <p className="mt-2 text-sm">AI가 미팅을 위한 맞춤 질문과 가이드를 만들어 드립니다.</p>
      </div>
    );
  }

  const questionEntries = Object.entries(result.questions);

  return (
    <div className="bg-white p-8 rounded-lg shadow-md">
      <div className="flex justify-between items-start">
        <h2 className="text-2xl font-bold mb-2">AI 템플릿</h2>
        {result.guide === null && !isGuideLoading && (
            <Button onClick={onGenerateGuide} variant="secondary">
                가이드 생성
            </Button>
        )}
      </div>

      {isGuideLoading && result.guide === ""}
      
      {result.guide !== null && (
        <div className="mb-6 pb-6 border-b">
          <h3 className="text-lg font-semibold mb-2">AI 가이드</h3>
          {isGuideLoading && result.guide === "" ? (
            <div className="space-y-2 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-full"></div>
            </div>
          ) : (
            <GuideContent text={result.guide || ""} />
          )}
        </div>
      )}
      
      <div>
        <h3 className="text-lg font-semibold mb-4">추천 질문</h3>
        <div className="space-y-3">
          {questionEntries.map(([id, text]) => (
            <div key={id} className="flex items-start">
              <input
                id={`q-${id}`}
                type="checkbox"
                className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1"
                defaultChecked
              />
              <label htmlFor={`q-${id}`} className="ml-3 text-gray-700">{text}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-8 text-right">
        <Button variant="primary">
          선택한 질문 사용하기 ({questionEntries.length})
        </Button>
      </div>
    </div>
  );
};

export default ResultDisplay;
