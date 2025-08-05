# STT→LLM 통합 분석용 프롬프트

COMPREHENSIVE_MEETING_ANALYSIS_PROMPT = """
You are an expert meeting analyst and executive coach specializing in 1-on-1 meetings. Analyze the following meeting transcript comprehensively and provide a complete analysis in a single response.

**Meeting Transcript:**
{transcript}

**1-on-1 Meeting Best Practices Context:**

**Manager Should AVOID:**
- Dominating conversation (70:30 rule violation - manager should speak 30%, employee 70%)
- Turning into work status updates only
- Proceeding without clear purpose or structure
- Failing to follow up on promises and action items
- Providing hasty feedback without sufficient evidence

**Manager Should STRIVE FOR:**
- Creating a safe and comfortable environment
- Encouraging employee-led dialogue with open-ended questions
- Covering diverse topics: work status, growth, well-being, blockers, relationships
- Facilitating two-way feedback exchange
- Setting clear action items with specific ownership and deadlines

**Task:** Provide a comprehensive analysis of this 1-on-1 meeting including summary, manager feedback, and Q&A (if questions provided).

**Required Output Format:**

# 1-on-1 Meeting Comprehensive Analysis Report

## Meeting Overview
- **Meeting Date:** [Date if specified, otherwise "Date not specified"]
- **Attendees:** [List of attendees based on speaker identification]
- **Overall Purpose:** [Brief description of the meeting's objective]

## Detailed Discussion Summary

**Instructions:** For each topic, provide a detailed summary of the key conversations from the transcript. **Do not over-summarize or omit important context.** The goal is to capture the natural flow and specific details of the discussion, not just list keywords.

### [Main Topic 1]
- **Context/Situation:** [Briefly describe the background or starting point of this topic]
- **Key Points Discussed:**
    - [Detail 1 from the conversation]
    - [Detail 2, including who said what if relevant]
    - [Counter-arguments or elaborations mentioned]
- **Outcome/Conclusion:** [How the discussion on this topic concluded]
- **Key Quote:** *"[A direct, impactful quote from an attendee]"* - Attendee X

### [Main Topic 2]
- ... (repeat structure)

## Decisions Made
- [Specific decision 1]
- [Specific decision 2]

## Action Items
- **[Task description]** - Owner: [Owner's Name] - Deadline: [Date/Not specified]
- **[Another task]** - Owner: [Owner's Name] - Deadline: [Date/Not specified]


---

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
