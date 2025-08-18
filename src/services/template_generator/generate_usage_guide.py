from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.utils.model import llm
from src.prompts.guide_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import UsageGuideOutput, UsageGuideInput
from typing import Dict, Any, List
from collections import Counter


def get_usage_guide_chain():
    """
    1on1 템플릿 활용 가이드 생성을 위한 LangChain 체인을 생성합니다.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=UsageGuideOutput)
    chain = prompt | llm | parser
    return chain


def analyze_questions_metadata(questions: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    생성된 질문들을 분석하여 메타데이터를 추출합니다.
    
    Args:
        questions: [{"question": "...", "intent": "..."}] 형태의 질문 리스트
    
    Returns:
        분석된 메타데이터 딕셔너리
    """
    if not questions:
        return {
            "total_questions": 0,
            "intent_distribution": {},
            "questions_with_intents": "",
            "intent_summary": "No questions provided"
        }
    
    # 의도별 분포 계산
    intents = [q.get("intent", "Unknown") for q in questions]
    intent_counts = Counter(intents)
    
    # 질문과 의도를 문자열로 포맷팅
    questions_with_intents = "\n".join([
        f"{i+1}. [{q.get('intent', 'Unknown')}] {q.get('question', '')}"
        for i, q in enumerate(questions)
    ])
    
    # 의도 요약
    intent_summary = "\n".join([
        f"- {intent}: {count}개 질문"
        for intent, count in intent_counts.most_common()
    ])
    
    return {
        "total_questions": len(questions),
        "intent_distribution": dict(intent_counts),
        "questions_with_intents": questions_with_intents,
        "intent_summary": intent_summary
    }


async def generate_usage_guide(guide_input: UsageGuideInput) -> Dict[str, Any]:
    """
    입력 데이터와 생성된 템플릿을 기반으로 활용 가이드를 비동기적으로 생성합니다.
    
    Args:
        guide_input: UsageGuideInput 스키마에 맞는 입력 데이터
    
    Returns:
        생성된 활용 가이드 딕셔너리
    """
    chain = get_usage_guide_chain()
    
    # 질문 분석
    metadata = analyze_questions_metadata(guide_input.generated_questions)
    
    prompt_variables = {
        "target_info": guide_input.target_info,
        "purpose": guide_input.purpose,
        "detailed_context": guide_input.detailed_context,
        "total_questions": metadata["total_questions"],
        "questions_with_intents": metadata["questions_with_intents"],
        "intent_summary": metadata["intent_summary"],
        "language": guide_input.language
    }
    
    try:
        response = await chain.ainvoke(prompt_variables)
        return response
    except Exception as e:
        # 에러 발생 시 기본 가이드 반환
        return {
            "opening_strategy": f"Begin the 1on1 meeting with a warm greeting and the first few questions to establish rapport with {guide_input.target_info}.",
            "needs_reflection": f"The questions are designed to address the specific context of {guide_input.detailed_context} through a balanced mix of different question types.",
            "flow_management": f"Follow the sequence from relationship building to deeper exploration, ending with actionable next steps and open discussion."
        }