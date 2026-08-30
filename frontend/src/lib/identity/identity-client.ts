import { BrowserSessionSchema, type BrowserSession, LogoutResponseSchema, StepUpRequiredSchema, type StepUpRequired } from "../../schemas/identity.schema";
import { secureFetch } from "../security/secure-fetch";
import { requireCsrfToken } from "./csrf-token";

export class IdentityContractError extends Error {}

async function readJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) throw new IdentityContractError("Identity endpoint returned non-JSON content");
  return response.json() as Promise<unknown>;
}

export async function getBrowserSession(signal?: AbortSignal): Promise<BrowserSession> {
  const options = signal ? { method: "GET", signal, cache: "no-store" as const } : { method: "GET", cache: "no-store" as const };
  const response = await secureFetch("/api/auth/session", options);
  if (!response.ok) throw new IdentityContractError(`Session endpoint failed with ${response.status}`);
  return BrowserSessionSchema.parse(await readJson(response));
}

export async function beginStepUp(action: string, resourceId: string): Promise<StepUpRequired> {
  const response = await secureFetch("/api/auth/step-up", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action, resourceId }),
    csrfToken: requireCsrfToken(),
  });
  const payload = await readJson(response);
  if (!response.ok) throw new IdentityContractError(`Step-up endpoint failed with ${response.status}`);
  return StepUpRequiredSchema.parse(payload);
}

export async function logoutEverywhere(): Promise<string | null> {
  const response = await secureFetch("/api/auth/logout", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ allSessions: true }),
    csrfToken: requireCsrfToken(),
  });
  if (!response.ok) throw new IdentityContractError(`Logout failed with ${response.status}`);
  const payload = LogoutResponseSchema.parse(await readJson(response));
  return payload.logoutUrl ?? null;
}
