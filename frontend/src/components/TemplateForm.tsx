'use client';

import React, { useState, useEffect } from 'react';
import Button from './Button';
import Input from './Input';
import RadioGroup from './RadioGroup';
import Checkbox from './Checkbox';

export interface FormData {
  userId: string;
  recipient: string;
  topic: {
    Work: boolean;
    Growth: boolean;
    Satisfaction: boolean;
    Relationships: boolean;
    'Junior Development': boolean;
  };
  context: string;
  questionCount: string;
  toneAndManner: string;
  language: string;
  questionTypes: {
    experience: boolean;
    reflection: boolean;
    action: boolean;
    relationship: boolean;
    growth: boolean;
    multiple_choice: boolean;
  };
}

interface TemplateFormProps {
  onGenerate: (formData: FormData) => void;
  isLoading: boolean;
}

interface User {
  user_id: string;
  name: string;
}

const TemplateForm: React.FC<TemplateFormProps> = ({ onGenerate, isLoading }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [formData, setFormData] = useState<FormData>({
    userId: '',
    recipient: '',
    topic: {
      Work: true,
      Growth: false,
      Satisfaction: false,
      Relationships: false,
      'Junior Development': false,
    },
    context: '',
    questionCount: 'standard',
    toneAndManner: 'polite',
    language: 'Korean',
    questionTypes: {
      experience: true,
      reflection: false,
      action: false,
      relationship: false,
      growth: false,
      multiple_choice: false,
    },
  });

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch('/api/users');
        const data: User[] = await response.json();
        setUsers(data);
        if (data.length > 0) {
          setFormData(prev => ({ ...prev, userId: data[0].user_id }));
        }
      } catch (error) {
        console.error("사용자 목록을 불러오는 데 실패했습니다.", error);
      }
    };
    fetchUsers();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const { checked } = e.target as HTMLInputElement;
      
      if (name in formData.questionTypes) {
        setFormData(prev => ({
          ...prev,
          questionTypes: {
            ...prev.questionTypes,
            [name]: checked,
          }
        }));
      } else if (name in formData.topic) {
        setFormData(prev => ({
          ...prev,
          topic: {
            ...prev.topic,
            [name]: checked,
          }
        }));
      }
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate(formData);
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-md h-fit">
      <h2 className="text-2xl font-bold mb-6">AI 템플릿 만들기</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-1">
            대상자 선택
          </label>
          <select
            id="userId"
            name="userId"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={formData.userId}
            onChange={handleChange}
            disabled={users.length === 0}
          >
            {users.length === 0 ? (
              <option>사용자 불러오는 중...</option>
            ) : (
              users.map(user => (
                <option key={user.user_id} value={user.user_id}>
                  {user.name}
                </option>
              ))
            )}
          </select>
        </div>

        <Input
          id="recipient"
          name="recipient"
          label="미팅 상대에 대해 알려주세요."
          type="text"
          placeholder="예: 김민준 팀장 (프로덕트 디자이너, 5년차)"
          value={formData.recipient}
          onChange={handleChange}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            대화 나누고 싶은 주제를 선택해주세요. (중복 가능)
          </label>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <Checkbox id="Work" name="Work" label="업무 (Work)" checked={formData.topic.Work} onChange={handleChange} />
            <Checkbox id="Growth" name="Growth" label="성장 (Growth)" checked={formData.topic.Growth} onChange={handleChange} />
            <Checkbox id="Satisfaction" name="Satisfaction" label="만족도 (Satisfaction)" checked={formData.topic.Satisfaction} onChange={handleChange} />
            <Checkbox id="Relationships" name="Relationships" label="관계 (Relationships)" checked={formData.topic.Relationships} onChange={handleChange} />
            <Checkbox id="Junior Development" name="Junior Development" label="주니어 육성 (Junior Development)" checked={formData.topic['Junior Development']} onChange={handleChange} />
          </div>
        </div>
        
        <div>
          <label htmlFor="context" className="block text-sm font-medium text-gray-700 mb-1">
            질문 생성에 참고할 만한 내용 또는 상황이 있나요?
          </label>
          <textarea
            id="context"
            name="context"
            rows={4}
            className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="• 문제 상황 (퍼포먼스, 협업, 이직장 등)
• 프로젝트 진행 상황
• 커리어와 성장에 대한 고민"
            value={formData.context}
            onChange={handleChange}
          ></textarea>
        </div>

        <details className="group" open>
          <summary className="text-lg font-semibold cursor-pointer list-none">
            <span className="group-open:hidden">▼</span>
            <span className="hidden group-open:inline">▲</span>
            세부 조정
          </summary>
          <div className="mt-4 space-y-6 border-t pt-6">
            <RadioGroup
              label="생성 질문 개수"
              name="questionCount"
              options={[
                { value: 'simple', label: '단순' },
                { value: 'standard', label: '표준' },
                { value: 'deep', label: '심화' },
              ]}
              value={formData.questionCount}
              onChange={handleChange}
            />
            <RadioGroup
              label="톤앤 매너"
              name="toneAndManner"
              options={[
                { value: 'polite', label: '정중한' },
                { value: 'casual', label: '캐주얼한' },
              ]}
              value={formData.toneAndManner}
              onChange={handleChange}
            />
            <div>
              <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
                언어
              </label>
              <select
                id="language"
                name="language"
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                value={formData.language}
                onChange={handleChange}
              >
                <option value="Korean">Korean</option>
                <option value="English">English</option>
              </select>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">생성 질문 종류</label>
                <div className="mt-2 grid grid-cols-2 gap-2">
                    <Checkbox id="experience" name="experience" label="경험/이야기" checked={formData.questionTypes.experience} onChange={handleChange} />
                    <Checkbox id="reflection" name="reflection" label="성찰/사고" checked={formData.questionTypes.reflection} onChange={handleChange} />
                    <Checkbox id="action" name="action" label="행동/실행" checked={formData.questionTypes.action} onChange={handleChange} />
                    <Checkbox id="relationship" name="relationship" label="관계/협업" checked={formData.questionTypes.relationship} onChange={handleChange} />
                    <Checkbox id="growth" name="growth" label="성장/목표" checked={formData.questionTypes.growth} onChange={handleChange} />
                    <Checkbox id="multiple_choice" name="multiple_choice" label="객관식" checked={formData.questionTypes.multiple_choice} onChange={handleChange} />
                </div>
            </div>
          </div>
        </details>

        <div className="pt-4">
            <Button type="submit" disabled={isLoading} variant="primary">
                {isLoading ? '생성 중...' : 'AI 템플릿 만들기'}
            </Button>
        </div>
      </form>
    </div>
  );
};

export default TemplateForm;
