import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { readFileSync } from "node:fs";

export function loadNinerouterEnv() {
  let values: string[] = [];
  try {
    const file = resolve(process.env.HOME || "", ".config/9router/env");
    values = execFileSync("bash", ["--noprofile", "--norc", "-c",
      'if [[ -f "$1" ]]; then . "$1"; fi; printf "%s\\0%s" "${NINEROUTER_URL:-}" "${NINEROUTER_KEY:-}"', "9router", file],
      { encoding: "utf8", timeout: 2000, stdio: ["ignore", "pipe", "ignore"], env: { HOME: process.env.HOME, PATH: process.env.PATH } }).split("\0");
  } catch { /* Process variables remain usable if file cannot be loaded. */ }
  const url = process.env.NINEROUTER_URL ?? values[0] ?? "http://localhost:20128";
  const key = process.env.NINEROUTER_KEY ?? values[1] ?? "";
  let parsed: URL;
  try { parsed = new URL(url); } catch { throw new Error("Invalid 9Router URL"); }
  if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) throw new Error("Invalid 9Router URL: expected HTTP(S) without credentials, query, or fragment");
  return { url: url.replace(/\/+$/, ""), key };
}

export function validateModels(payload: unknown) {
  const data = (payload as { data?: unknown })?.data;
  if (!Array.isArray(data) || !data.length || data.length > 10000) throw new Error("Invalid 9Router model catalog");
  const ids = new Set<string>();
  return data.map((model) => {
    if (!model || typeof model.id !== "string" || !model.id.trim() || ids.has(model.id)) throw new Error("Invalid 9Router model ID");
    ids.add(model.id);
    const caps = model.capabilities;
    const context = caps?.contextWindow ?? model.context_length ?? 128000;
    const output = caps?.maxOutput ?? model.max_completion_tokens ?? 16384;
    if (!Number.isSafeInteger(context) || context <= 0 || !Number.isSafeInteger(output) || output <= 0) throw new Error("Invalid 9Router token limits");
    return {
      id: model.id, name: `9Router ${model.id}`, reasoning: caps?.reasoning === true,
      ...(caps?.reasoning === true && caps.thinkingCanDisable === false ? { thinkingLevelMap: { off: null } } : {}),
      input: caps?.vision === true ? ["text", "image"] as const : ["text"] as const,
      contextWindow: context, maxTokens: output,
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    };
  });
}

export default async function (pi: ExtensionAPI) {
  const { url, key } = loadNinerouterEnv();
  process.env.NINEROUTER_URL = url;
  process.env.NINEROUTER_KEY = key;
  // ponytail: offline fallback exposes configured default only; add persisted catalog when needed.
  let defaultModel = "cx/gpt-6.1-sol";
  try {
    const settings = JSON.parse(readFileSync(resolve(process.env.PI_CODING_AGENT_DIR || resolve(process.env.HOME || "", ".pi/agent"), "settings.json"), "utf8"));
    if (settings.defaultProvider === "9router" && typeof settings.defaultModel === "string" && settings.defaultModel.trim()) defaultModel = settings.defaultModel;
  } catch { /* Built-in fallback remains available for missing/invalid local settings. */ }
  const fallback = validateModels({ data: [{ id: defaultModel }] });
  const provider = {
    name: "9Router", baseUrl: `${url}/v1`, api: "openai-completions" as const,
    apiKey: key ? "$NINEROUTER_KEY" : "9router-no-auth", authHeader: Boolean(key),
    compat: { supportsDeveloperRole: false, supportsReasoningEffort: false },
  };
  pi.registerProvider("9router", { ...provider, models: fallback });
  try {
    const response = await fetch(`${url}/v1/models`, {
      headers: key ? { Authorization: `Bearer ${key}` } : {}, signal: AbortSignal.timeout(10000), redirect: "error",
    });
    if (!response.ok) throw new Error("Discovery HTTP error");
    const models = validateModels(await response.json());
    pi.registerProvider("9router", { ...provider, models });
  } catch {
    // Never print raw gateway errors: upstream text can contain credentials.
    console.warn("9Router discovery unavailable or invalid; using configured default model. Check gateway access, then /reload.");
  }
}
