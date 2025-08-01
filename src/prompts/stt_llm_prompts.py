# STT→LLM 분석용 프롬프트

MEETING_SUMMARY_PROMPT = """
You are an expert meeting analyst. Analyze the following meeting transcript and provide a comprehensive summary in a readable format.

**Meeting Transcript:**
{transcript}

**Instructions:**
Analyze the transcript and provide a well-structured summary following the format below. When speakers are identified by numbers (e.g., Participant 1, Participant 2), use those identifiers consistently.

**Response Format:**

# [Concise Meeting Title]

## Meeting Overview
- **Date of Meeting:** [Date if specified, otherwise "Date not specified"]
- **Attendees:** [List participants based on speaker identification]
- **Overall Purpose:** [Brief statement of meeting objective]

## Key Discussion Points

### [Major Topic 1]
- [Key point or discussion detail]
- [Another important detail]
- **Quote:** *"[Verbatim quote from participant]"* - Participant X

### [Major Topic 2]
- [Key point or discussion detail]
- [Sub-discussion points]

## Decisions Made
- [Concrete decision 1]
- [Concrete decision 2]

## Action Items
- **[Task description]** - Assigned to: [Person] - Deadline: [Date/Not specified]
- **[Another task]** - Assigned to: [Person] - Deadline: [Date/Not specified]

## Key Quotes
- *"[Important quote 1]"* - Participant X
- *"[Important quote 2]"* - Participant Y

**Guidelines:**
- Use clear headings and bullet points for readability
- Include verbatim quotes that emphasize key points
- Organize information logically
- Use participant numbers when speakers are identified
- If information is not available, state "Not specified" or "Not mentioned"
- Focus on actionable items and concrete decisions
"""