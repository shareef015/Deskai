import type { Conversation, CreateConversationRequest, Problem } from "@deskpilot/schemas";

export class ApiError extends Error {
  constructor(readonly problem: Problem) { super(problem.title); }
}

export class DeskPilotClient {
  constructor(private readonly baseUrl = "/api/v1", private readonly fetcher = fetch) {}

  async createConversation(input: CreateConversationRequest): Promise<Conversation> {
    const response = await this.fetcher(`${this.baseUrl}/conversations`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!response.ok) throw new ApiError(await response.json() as Problem);
    return response.json() as Promise<Conversation>;
  }
}
