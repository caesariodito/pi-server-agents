import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFileSync } from "node:child_process";

type RemoteModel = {
  id: string;
  owned_by?: string;
  context_length?: number;
  max_completion_tokens?: number;
  capabilities?: {
    vision?: boolean;
    reasoning?: boolean;
    thinkingCanDisable?: boolean;
    thinkingEffortSupported?: boolean;
    contextWindow?: number;
    maxOutput?: number;
  };
};

type NinerouterEnv = {
  url?: string;
  key?: string;
};

function loadNinerouterEnv(): NinerouterEnv {
  if (process.env.NINEROUTER_URL || process.env.NINEROUTER_KEY) {
    return {
      url: process.env.NINEROUTER_URL,
      key: process.env.NINEROUTER_KEY,
    };
  }

  try {
    const output = execFileSync(
      "bash",
      [
        "-lc",
        '. "$HOME/.config/9router/env" 2>/dev/null || true; printf "%s\\n%s" "$NINEROUTER_URL" "$NINEROUTER_KEY"',
      ],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }
    );
    const [url, key] = output.split("\n");
    return {
      url: url || undefined,
      key: key || undefined,
    };
  } catch {
    return {};
  }
}

export default async function (pi: ExtensionAPI) {
  const env = loadNinerouterEnv();
  const root = (env.url || "http://100.70.192.32:20128").replace(/\/$/, "");
  const key = env.key;
  const response = await fetch(`${root}/v1/models`, {
    headers: key ? { Authorization: `Bearer ${key}` } : {},
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`9Router model discovery failed: HTTP ${response.status}`);

  const payload = (await response.json()) as { data?: RemoteModel[] };
  if (!Array.isArray(payload.data)) throw new Error("9Router model discovery failed: invalid data");

  pi.registerProvider("9router", {
    name: "9Router",
    baseUrl: `${root}/v1`,
    api: "openai-completions",
    apiKey: key || "!bash -lc '. \"$HOME/.config/9router/env\"; printf %s \"$NINEROUTER_KEY\"'",
    authHeader: true,
    compat: {
      supportsDeveloperRole: false,
      supportsReasoningEffort: false,
    },
    models: payload.data.map((remote) => {
      const capabilities = remote.capabilities;
      const reasoning = capabilities?.reasoning === true;
      return {
        id: remote.id,
        name: `9Router ${remote.id}${remote.owned_by ? ` (${remote.owned_by})` : ""}`,
        reasoning,
        ...(reasoning && capabilities?.thinkingCanDisable === false
          ? { thinkingLevelMap: { off: null } }
          : {}),
        input: capabilities?.vision ? (["text", "image"] as const) : (["text"] as const),
        contextWindow: capabilities?.contextWindow ?? remote.context_length ?? 128_000,
        maxTokens: capabilities?.maxOutput ?? remote.max_completion_tokens ?? 16_384,
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      };
    }),
  });
}
