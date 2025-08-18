from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
from src.utils.model import llm, llm_streaming
from src.prompts.guide_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT, INTENT_ANALYSIS_PROMPT
from src.utils.template_schemas import UsageGuideInput
from typing import Dict, Any, List, AsyncGenerator
from collections import Counter


def get_usage_guide_chain():
    """
    1on1 템플릿 활용 가이드 생성을 위한 스트리밍 LangChain 체인을 생성합니다.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    # JsonOutputParser를 제거하여 순수한 텍스트 스트림을 받도록 함
    return prompt | llm_streaming

def get_intent_analysis_chain():
    """
    질문 의도 분석을 위한 LangChain 체인을 생성합니다. (비스트리밍)
    """
    prompt = ChatPromptTemplate.from_template(INTENT_ANALYSIS_PROMPT)
    # 의도 분석은 전체 JSON을 한번에 받아야 하므로 일반 llm 사용
    parser = JsonOutputParser() 
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
    
    intents = [q.get("intent", "Unknown") for q in questions]
    intent_counts = Counter(intents)
    
    questions_with_intents = "\n".join([
        f"{i+1}. [{q.get('intent', 'Unknown')}] {q.get('question', '')}"
        for i, q in enumerate(questions)
    ])
    
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


async def generate_usage_guide(guide_input: UsageGuideInput) -> AsyncGenerator[str, None]:
    """
    입력 데이터를 기반으로 각 질문의 의도를 먼저 분석하고,
    그 결과를 바탕으로 활용 가이드를 '타이핑 효과' 스트리밍 방식으로 비동기 생성합니다.
    """
    # 1. 질문 의도 분석 단계 (이전과 동일)
    intent_analysis_chain = get_intent_analysis_chain()
    
    questions_for_analysis = "\n".join(
        [f'{num}. {text}' for num, text in guide_input.generated_questions.items()]
    )
    
    intent_prompt_variables = {
        "questions_for_intent_analysis": questions_for_analysis,
        "target_info": guide_input.target_info,
        "purpose": guide_input.purpose,
        "detailed_context": guide_input.detailed_context,
        "language": guide_input.language
    }
    
    try:
        intent_results = await intent_analysis_chain.ainvoke(intent_prompt_variables)
        questions_with_intents = list(intent_results.values())
    except Exception as e:
        questions_with_intents = [
            {"question": text, "intent": "Not analyzed"} 
            for text in guide_input.generated_questions.values()
        ]

    # 2. 활용 가이드 생성 단계 (스트리밍 방식 변경)
    guide_chain = get_usage_guide_chain()
    metadata = analyze_questions_metadata(questions_with_intents)
    
    guide_prompt_variables = {
        "target_info": guide_input.target_info,
        "purpose": guide_input.purpose,
        "detailed_context": guide_input.detailed_context,
        "total_questions": metadata["total_questions"],
        "questions_with_intents": metadata["questions_with_intents"],
        "intent_summary": metadata["intent_summary"],
        "language": guide_input.language
    }
    
    try:
        # 이제 chunk는 딕셔너리가 아닌 AIMessageChunk 객체
        async for chunk in guide_chain.astream(guide_prompt_variables):
            if chunk.content:
                # generate_template과 동일하게, 직접 SSE 형식으로 포장하여 yield
                yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_message = f"Error during usage guide generation: {e}"
        yield f"data: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"