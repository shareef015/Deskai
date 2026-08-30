import type { NextRequest } from "next/server";

// Synthetic local responder for the standalone web app. When the DeskPilot API
// (services/api) is not running, this keeps the conversation workspace usable in
// synthetic-demonstration mode. It never contacts a managed endpoint.

const MAX_CHARS = 4000;

function assistantReply(message: string): string {
  const text = message.toLowerCase();
  if (/(outlook|email|mailbox|\bost\b|\bpst\b|send\/receive|add-in)/.test(text)) {
    return "That sounds like an Outlook for Windows issue. Before I inspect anything I need your consent to run read-only checks on the Outlook connection state, profile and OST health. I will not read message content or change settings. Do you allow those read-only checks?";
  }
  if (/(print|printer|spooler|queue|driver|toner|paper jam)/.test(text)) {
    return "Understood, a printing problem. With your consent I can run read-only checks on the print spooler, the queue and the printer's network reachability. Nothing is changed without a separate approval. May I run those read-only checks?";
  }
  if (/(scan|scanner|twain|\bwia\b)/.test(text)) {
    return "Got it, a scanning problem. With your consent I can check the scanner's WIA/TWAIN driver status and network path, all read-only. Shall I proceed with those checks?";
  }
  if (/(vpn|wi-?fi|network|\bdns\b|proxy|internet|offline|can'?t connect)/.test(text)) {
    return "Thanks, that points to Windows connectivity. With your consent I can run read-only checks on the network adapter, DNS, proxy and VPN state to narrow it down. Do you allow those read-only checks?";
  }
  return "Thanks for the details. To help safely I first confirm your identity and device, then ask for consent before any read-only diagnostics. I only work on Outlook, printing, scanning and the Windows connectivity behind them. Which device is affected, and what exactly is failing?";
}

export async function POST(request: NextRequest): Promise<Response> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "invalid_json" }, { status: 400 });
  }

  const content = (body as { content?: unknown }).content;
  if (typeof content !== "string" || content.trim().length === 0 || content.length > MAX_CHARS) {
    return Response.json({ error: "invalid_content" }, { status: 422 });
  }

  return Response.json({
    id: crypto.randomUUID(),
    role: "assistant",
    content: assistantReply(content),
    created_at: new Date().toISOString(),
  });
}
