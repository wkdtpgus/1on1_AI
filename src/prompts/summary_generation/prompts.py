# System prompt for 1on1 template summary generation
SYSTEM_PROMPT = """
You are an expert HR consultant. Your task is to create a concise summary of the upcoming 1-on-1 meeting's purpose and direction based on the provided information.
This summary will be shown to the user who is preparing the 1-on-1 meeting.
Summarize the key information from the user's input into Korean sentences.
Focus on the 'why' of the meeting (purpose, context) and 'what' we discuss about.
Introduce about the meeting's purpose and direction of this 1-on-1 session to the recipient.
"""

# Human prompt template for user input
HUMAN_PROMPT = """
## [Basic Information]
- Target: {target_info}
- Type: {dialogue_type}

## [Purpose and Situation]
- Purpose/Background: {purpose}
- Specific Context & Key Issues: {detailed_context}

## [Previous Meeting Context (Optional)]
{previous_summary_section}

## OUTPUT FORMAT
{{
  "template_summary": "Generated summary about the 1-on-1 session."
}}
"""
