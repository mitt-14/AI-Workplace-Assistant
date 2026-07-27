from app.schemas.email_analysis import EmailAnalysisRequest, EmailReplyRequest


EMAIL_ANALYSIS_SYSTEM_RULES = """
You are an enterprise email-analysis assistant. Analyze only the supplied email.
Do not invent names, dates, deadlines, tasks, risks, or facts.
Return exactly one valid JSON object. Do not use Markdown or code fences.

Allowed values:
classification: hr, finance, legal, support, complaint, sales, meeting,
technical, personal, spam, phishing, general
priority: low, medium, high, urgent
sentiment: positive, neutral, negative, mixed
risk type: phishing, spam, suspicious_link, credential_theft, payment_fraud,
malicious_attachment, social_engineering, privacy, other
risk severity: low, medium, high, critical

Required JSON shape:
{
  "classification": "general",
  "priority": "medium",
  "sentiment": "neutral",
  "summary": "Concise factual summary",
  "key_points": ["..."],
  "tasks": [
    {
      "task": "...",
      "owner": null,
      "deadline": null,
      "priority": "medium"
    }
  ],
  "deadlines": [
    {
      "text": "Friday",
      "normalized_date": null,
      "context": "..."
    }
  ],
  "entities": {
    "people": [],
    "organizations": [],
    "email_addresses": [],
    "phone_numbers": [],
    "urls": [],
    "monetary_amounts": []
  },
  "risks": [
    {
      "type": "phishing",
      "severity": "high",
      "description": "...",
      "evidence": "..."
    }
  ],
  "suggested_reply": null,
  "confidence": 0.0
}

Rules:
- Use empty arrays when no item is supported by the email.
- Use null when an owner, deadline, normalized date, evidence, or reply is unknown.
- normalized_date must be ISO-8601 only when the email gives enough context.
- Do not classify an email as phishing merely because it contains a link.
- confidence must reflect certainty and be between 0 and 1.
""".strip()


def build_email_analysis_prompt(request: EmailAnalysisRequest) -> str:
    reply_instruction = (
        f"Generate a {request.reply_style.value} suggested reply."
        if request.generate_reply
        else "Set suggested_reply to null."
    )
    if request.custom_reply_instructions:
        reply_instruction += (
            " Follow these reply instructions: "
            f"{request.custom_reply_instructions}"
        )

    recipients = ", ".join(request.recipients) if request.recipients else "Not provided"

    return f"""
{EMAIL_ANALYSIS_SYSTEM_RULES}

Additional instruction:
{reply_instruction}

EMAIL
Subject: {request.subject or 'Not provided'}
From: {request.sender or 'Not provided'}
To: {recipients}
Body:
{request.body}

Return the JSON object now.
""".strip()


def build_email_reply_prompt(request: EmailReplyRequest) -> str:
    style_instruction = request.style.value
    if request.style.value == "custom":
        style_instruction = request.custom_instructions or "professional"

    recipients = ", ".join(request.recipients) if request.recipients else "Not provided"
    sign_off = (
        f"Use '{request.sender_name}' in the sign-off."
        if request.sender_name
        else "Do not invent a sender name."
    )

    return f"""
Write a reply to the email below.
Return only the reply text, with no analysis, labels, Markdown fences, or commentary.
Style: {style_instruction}
Be factual, helpful, and concise. Do not promise actions that are not supported.
{sign_off}

ORIGINAL EMAIL
Subject: {request.subject or 'Not provided'}
From: {request.sender or 'Not provided'}
To: {recipients}
Body:
{request.body}
""".strip()
