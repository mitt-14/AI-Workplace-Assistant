from app.schemas.meeting_analysis import (
    MeetingAnalysisRequest,
    MeetingFollowUpRequest,
)


MEETING_ANALYSIS_SYSTEM_RULES = """
You are an enterprise meeting-analysis assistant.
Analyze only the supplied meeting transcript.
Do not invent participants, decisions, owners, deadlines, tasks, or facts.
Return exactly one valid JSON object.
Do not use Markdown or code fences.

Allowed action-item priority values:
low, medium, high, urgent

Required JSON shape:
{
  "summary": "Concise factual meeting summary",
  "key_points": ["..."],
  "decisions": [
    {
      "decision": "...",
      "owner": null,
      "rationale": null
    }
  ],
  "action_items": [
    {
      "task": "...",
      "owner": null,
      "deadline": null,
      "normalized_deadline": null,
      "priority": "medium"
    }
  ],
  "participants": ["..."],
  "deadlines": [
    {
      "text": "Friday",
      "normalized_date": null,
      "context": "..."
    }
  ],
  "follow_up_items": ["..."],
  "follow_up_email": null,
  "confidence": 0.0
}

Rules:
- Use only information explicitly supported by the transcript.
- Use empty arrays when information is not available.
- Use null when an owner, rationale, deadline, or normalized date is unknown.
- normalized dates must use ISO-8601 only when enough context exists.
- A proposal is not a decision unless the transcript indicates agreement.
- Do not infer an owner merely because someone discussed a task.
- confidence must be between 0 and 1.
""".strip()


def build_meeting_analysis_prompt(
    request: MeetingAnalysisRequest,
    transcript: str,
) -> str:
    follow_up_instruction = (
        "Generate a concise professional follow-up email in follow_up_email."
        if request.generate_follow_up_email
        else "Set follow_up_email to null."
    )

    if request.generate_follow_up_email:
        follow_up_instruction += (
            " Email style: "
            f"{request.follow_up_email_style}."
        )

    return f"""
{MEETING_ANALYSIS_SYSTEM_RULES}

Additional instruction:
{follow_up_instruction}

MEETING
Title: {request.title or 'Not provided'}

Transcript:
{transcript}

Return the JSON object now.
""".strip()


def build_meeting_follow_up_prompt(
    request: MeetingFollowUpRequest,
) -> str:
    decisions = "\n".join(
        f"- {item.decision}"
        for item in request.decisions
    ) or "Not provided"

    action_items = "\n".join(
        (
            f"- {item.task}; "
            f"owner={item.owner or 'unknown'}; "
            f"deadline={item.deadline or 'unknown'}"
        )
        for item in request.action_items
    ) or "Not provided"

    participants = (
        ", ".join(request.participants)
        if request.participants
        else "Not provided"
    )

    sign_off = (
        f"Use '{request.sender_name}' in the sign-off."
        if request.sender_name
        else "Do not invent a sender name."
    )

    return f"""
Write a follow-up email for the meeting below.
Return only the email body.
Do not include analysis, labels, Markdown fences, or commentary.
Style: {request.style}
Be factual and concise.
Do not invent decisions, owners, deadlines, or commitments.
{sign_off}

Meeting title:
{request.title or 'Not provided'}

Participants:
{participants}

Summary:
{request.summary or 'Not provided'}

Decisions:
{decisions}

Action items:
{action_items}

Transcript:
{request.transcript or 'Not provided'}
""".strip()
