export type ConversationStatus = "open" | "waiting_for_user" | "resolved" | "escalated";
export type ConsentScope = "diagnostic" | "remediation" | "remote_session";
export type ConsentDecision = "granted" | "denied";

export interface CreateConversationRequest { device_id: string; initial_message: string }
export interface Conversation { id: string; status: ConversationStatus; created_at: string }
export interface SendMessageRequest { content: string }
export interface ConsentRequest { scope: ConsentScope; decision: ConsentDecision; expires_at: string }
export interface ConsentReceipt { id: string; conversation_id: string; scope: string; decision: string; recorded_at: string }
export interface Problem { type: string; title: string; status: number; detail?: string; correlation_id: string }
