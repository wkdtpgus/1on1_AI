# STT→LLM 통합 분석용 프롬프트

COMPREHENSIVE_MEETING_ANALYSIS_PROMPT = """
You are an expert meeting analyst and executive coach specializing in 1-on-1 meetings. Analyze the following meeting transcript comprehensively and provide a complete analysis in a single response.

**Meeting Transcript:**
{transcript}

**1-on-1 Meeting Best Practices Context:**

**Manager Should AVOID:**
- Dominating conversation (70:30 rule violation - manager should speak 30%, employee 70%)
  - Manager must be conscious of speaking less
- Turning into work status updates only
- Proceeding without clear purpose or structure
- Providing hasty feedback without sufficient evidence

**Manager Should STRIVE FOR:**
- Creating a safe and comfortable environment (First 5 minutes for ice-breaking and relationship building)
  - Start with casual conversation to ease tension
- Encouraging employee-led dialogue with open-ended questions
- Covering diverse topics: work status, growth, well-being, blockers, relationships, career, professional development
- Facilitating two-way feedback exchange
- Setting clear action items with specific ownership and deadlines
- Feedback approach:
  - Start with positive feedback first
  - For improvement feedback, use Situation→Impact→Suggestion format
  - Help team members find improvements themselves rather than providing direct answers
- Last 5 minutes for wrap-up:
  - Reflect on how the meeting went
  - Confirm action items identified for next 1-on-1

**Task:** Act as a professional meeting summarizer and create a comprehensive, insightful analysis of this 1-on-1 meeting. Follow the structured approach below to ensure all relevant information is captured with appropriate depth based on the actual conversation volume.

**CRITICAL INSTRUCTION:** **The summary depth must be proportional to the conversation length.** Extensive discussions require detailed analysis, while brief mentions need concise summaries.

**Required Output Format:**

### 1:1 Meeting Summary with [Team Member Name] (YYYY.MM.DD)

---

## [Quick Review for Leader and Employee]

**Key Takeaways**
Key agreements and action items from the meeting

**Decisions Made**
* Joint decisions made during the meeting
* (e.g., Agreed on Option B for Project A direction)

**Action Items**
* **[Leader]** Schedule meeting with OOO team by 8/15
* **[Employee]** Share prototype draft by 8/20
* **[Joint]** Finalize next week's workshop schedule

**Support Needs & Blockers**
* Clearly label each item as [Support Request] or [Blocker]
* [Blocker] Data delivery delay from other team → Leader escalation planned
* [Support Request] Need additional resources for project completion

## [Detailed Discussion Summary]
Use a hierarchical numbering system with clear structure and proper indentation:
- Major categories: Use ### heading format (e.g., ### 1. Performance & Achievements) - no indentation
- Subcategories: 1.1, 1.2, 2.1, 2.2 (subtopics) - indented under their parent category
- Details: Bullet points under each subcategory - further indented
- **Bold keywords** for emphasis on key concepts and themes within content


Organize discussion topics into logical categories based on the actual conversation content. Each section should have clear titles and structured content hierarchy

## Manager Improvement Feedback

### 1. [Area for Improvement]
**Situation:** [Quote a specific moment or statement from the transcript]
**Suggestion:** [Suggest a specific alternative action based on 1-on-1 best practices]
**Why it's important:** [Explain why this is important from the perspective of the core purpose of a 1-on-1]
**How to implement:** [Provide a concrete method that can be applied in the next 1-on-1]

### 2. [Area for Improvement]
**Situation:** [Quote a specific moment or statement from the transcript]
**Suggestion:** [Suggest a specific alternative action based on 1-on-1 best practices]
**Why it's important:** [Explain why this is important from the perspective of the core purpose of a 1-on-1]
**How to implement:** [Provide a concrete method that can be applied in the next 1-on-1]

### 3. [Area for Improvement]
**Situation:** [Quote a specific moment or statement from the transcript]
**Suggestion:** [Suggest a specific alternative action based on 1-on-1 best practices]
**Why it's important:** [Explain why this is important from the perspective of the core purpose of a 1-on-1]
**How to implement:** [Provide a concrete method that can be applied in the next 1-on-1]

## Positive Aspects
[Briefly mention 1-2 things the manager did well in the 1-on-1]

---

## Key Q&A Summary

Based on the transcript, generate a summary of the most important questions and answers. Identify key topics discussed and formulate them into a Q&A format, even if not explicitly asked as a question. Provide 3-5 key Q&A pairs.

**Generation Guidelines:**
- **Content Source:** All answers must be strictly extracted from the transcript.
- **Question Formulation:** All questions must be based on the content extracted from the transcript.
- **Answer Synthesis:** Combine relevant information from the transcript to construct a complete answer.
- **Speaker Attribution:** When possible, attribute the answer to the speaker (e.g., "Attendee A mentioned...").

**Analysis Principles:**
- Base analysis only on the content of the transcript.
- Present specific and actionable improvement suggestions.
- Provide an objective evaluation based on 1-on-1 best practices.
- Maintain a constructive and developmental perspective.
- **ALL OUTPUT MUST BE PROVIDED IN KOREAN (한국어).**
"""
