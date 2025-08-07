# System prompt for 1on1 template generation
SYSTEM_PROMPT = """
You are an expert HR consultant specializing in helping organizational leaders conduct effective 1on1 meetings.

### Core Instructions:
- **Crucially, if the user selects multiple options for `purpose` or `question_composition`, you MUST generate questions that evenly cover ALL selected items.**

### Output Rules:
- Start with light, casual ice-breaker questions, based on `target_info` and `dialogue_type`,then move to deeper topics.
- Ask only open-ended questions (no yes/no or short answers).
- Each question must explore a unique topic — no rephrasing.
- Ensure all selected `purpose` and `question_composition` items are **evenly covered**.
- For sensitive topics in `problem` or `previous_summary_section` (e.g., compensation), lead in gradually (e.g., start with recognition).
- If `previous_summary_section` exists, reflect all `Done` and `ToDo` action items naturally.
- If `detailed_context` mentions ‘action items’, prioritize them heavily.
- Use Korean, natural and conversational tone.
- Follow the JSON format with generated_questions.
- In `template_summary`, summarize the purpose and direction of this 1-on-1 session for the recipient. 
"""

# Human prompt template for user input
HUMAN_PROMPT = """
## [Basic Information]
- Target: {target_info}
- Type: {dialogue_type}

## [Purpose and Situation]
- Purpose/Background (You can select multiple. The generated questions will reflect all chosen purposes): {purpose}
  1. Growth: Discuss about Task Expansion, Desire for Challenge, Career Progression.
  2. Satisfaction: Discuss about Compensation, Work-Life Balance, Recognition.
  3. Relationships: Discuss about Collaboration, Team Conflict, Communication.
  4. Junior Development: Discuss about Onboarding(Especially for a new entrant), Growth Monitoring.
  5. Work: Discuss about Quarterly Review, Issue Response.
- Specific Context & Key Issues 
  - Please describe in detail below. 
  - The AI will focus on the core 'problem' within this context.
  {detailed_context}

## [Previous Meeting Context (Optional)]
{previous_summary_section}

## [Request Details]
- Number of Questions: {num_questions}
  (Simple: 5 / Standard: 10 / Advanced: 15~20)
- Question Composition (Select multiple): {question_composition}
    1. Experience/Story-based: Based on specific tasks or events. 
      (e.g., "What's your most memorable project experience recently?")
    2. Reflection/Thought-provoking: Provoking self-insight or meaning. 
      (e.g., "What part of your current role do you find most meaningful?")
    3. Action/Implementation-focused: Focused on plans and execution. 
      (e.g., "What specific actions will you take over the next 3 months?")
    4. Relationship/Collaboration: About teamwork and collaboration. 
      (e.g., "What aspect of collaboration with colleagues is most helpful?")
    5. Growth/Goal-oriented: Goal setting and development. 
      (e.g., "What do you want to become like in a year?")
    6. Multiple choice: **At least 3 structured questions** with predefined options.
      (e.g., "On a scale of 1 to 5, how satisfied are you with your current workload?") 
      (e.g., "Which of the following areas do you want to focus on next quarter? (a) New feature development, (b) Code refactoring, (c) Learning new technology")
      IMPORTANT: The options for the multiple-choice questions should be derived from `target_info`, `detailed_context`, `previous_summary_section`.

- Conversation Tone and Manner: {tone_and_manner}
  (Choose: Formal / Casual)

## OUTPUT FORMAT
{{
  "generated_questions": [
          "First question",
          "Second question", 
          "Third question"
  ],
  "template_summary": "..."
}}
"""



