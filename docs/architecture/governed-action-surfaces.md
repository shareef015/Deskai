# Governed action surfaces

DeskPilot uses typed forms, modal confirmations and mobile-friendly drawers instead of browser prompts or alerts. Every payload is validated again on the server for tenant, incident, actor role, exact action fingerprint, allowed fields, length and secret-like content. Request identifiers make repeat submissions fail closed.

The UI traps the decision in an explicit review step, reports editing, confirming, submitting, success and failure states, and allows safe cancellation. Dialogs expose accessible names and descriptions, close with Escape or a cancel control, and restore focus to the action that opened them.
