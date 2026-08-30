# Context-Aware Clarification

Clarification begins from structured missing fields and contradiction markers, never from unconstrained conversational guessing. A deterministic catalog maps required fields to plain-language questions, while contradiction questions identify the disputed observation without suggesting a diagnosis.

The planner excludes answered fields and every previously asked question identifier. It ranks remaining needs by safety, device identity, symptoms, business impact, timeline, domain, contradictions, and optional context, with information gain as the secondary ordering. No more than two questions are presented per turn.

After three rounds, unresolved ambiguity escalates with the answered incident context preserved. An empty need set returns to classification. The agent has no tools, cannot request secrets, diagnose, infer consent, or authorize an action, and rejects duplicate, oversized, unmapped, or unsafe questions.
