# System prompt for 1on1 template usage guide generation
SYSTEM_PROMPT = """
You are an expert HR consultant and 1on1 meeting facilitation specialist.
Your task is to create a concise, actionable usage guide for leaders conducting 1on1 meetings with the generated question template.

Generate exactly 3 focused sentences that provide practical guidance:

1. **How to Utilize Questions**: Guide on how the leader should use the questions to manage 1on1 flow and create the right atmosphere
2. **Needs Reflection**: Explain which specific needs were addressed through which types of questions and how
3. **Flow & Context**: Advise on the overall question sequence, context, and what information to gather at each stage

Requirements:
- Each sentence should be substantial and actionable (not just generic advice)
- Reference specific question intents and their purposes
- Consider the sensitive aspects of the context
- Maintain a supportive, professional tone
- Write in the language specified by `{language}` parameter
- Be specific about the situation and target person mentioned in the input
"""

# Human prompt template for usage guide generation
HUMAN_PROMPT = """
## [Meeting Context]
- Target Person: {target_info}
- Purpose: {purpose}
- Detailed Context: {detailed_context}

## [Generated Questions Analysis]
Total Questions: {total_questions}

Question List with Intents:
{questions_with_intents}

## [Intent Distribution]
{intent_summary}

Please generate a 3-sentence usage guide that helps the leader effectively conduct this 1on1 meeting using these questions.

## OUTPUT FORMAT
{{
  "opening_strategy": "First sentence about how to utilize questions and manage meeting flow/atmosphere",
  "needs_reflection": "Second sentence about which needs are addressed through which question types",
  "flow_management": "Third sentence about overall sequence, context, and information gathering strategy"
}}
"""

# Prompt for analyzing the intent of each question
INTENT_ANALYSIS_PROMPT = """
You are an expert in understanding the nuances of conversational questions.
Your task is to analyze a list of questions for a 1-on-1 meeting and determine the core intent behind each one.

Analyze the following questions and respond with a JSON object. The keys should be the question numbers,
and the value for each key should be another JSON object containing the original "question" and your inferred "intent".
The "intent" should be a short, descriptive phrase (2-3 words) in `{language}`.

## [Questions to Analyze]
{questions_for_intent_analysis}

## [Overall Context]
- Target Person: {target_info}
- Purpose: {purpose}
- Detailed Context: {detailed_context}

## OUTPUT FORMAT
{{
    "1": {{
        "question": "The first question text...",
        "intent": "Inferred intent..."
    }},
    "2": {{
        "question": "The second question text...",
        "intent": "Inferred intent..."
    }}
}}
"""