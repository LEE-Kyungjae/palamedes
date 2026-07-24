type PlanEnvelope = {
  ok: boolean;
  tool_name: string;
  result_type: "plan";
  plan: {
    schema_version: string;
    version: string;
    goal: string;
    success_metric: string;
    deadline: string;
    [key: string]: unknown;
  };
  fingerprint: string;
  contract_version: string;
  implementation_version: string;
};

type CycleEnvelope = {
  ok: boolean;
  result_type: "cycle";
  plan: PlanEnvelope["plan"];
  fingerprint: string;
  contract_version: string;
  implementation_version: string;
  qa: {
    result: string;
    score: number;
  };
  health: {
    status: string;
  };
};

type ContractsEnvelope = {
  ok: boolean;
  result_type: "contracts";
  contract_version: string;
  contracts: {
    host_action_contract?: {
      capability_names?: string[];
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

type ToolCatalogEnvelope = {
  ok: boolean;
  result_type: "tool_catalog";
  catalog: {
    authoritative: boolean;
    execute_endpoint: string;
    tool_count: number;
  };
  tools: Array<{
    name: string;
    kind: "read" | "mutation";
    execute_via: {
      generic: string;
      legacy_wrapper: string;
    };
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
};

type ToolExecuteEnvelope = {
  tool: string;
  input: Record<string, unknown>;
  result: Record<string, unknown>;
};

type ErrorEnvelope = {
  error: string;
  type: string;
  error_code: string;
  retryable: boolean;
  operation?: string;
  step?: string;
  current_fingerprint?: string;
  [key: string]: unknown;
};

class PalamedesHttpError extends Error {
  status: number;
  payload: ErrorEnvelope;

  constructor(status: number, payload: ErrorEnvelope) {
    super(String(payload.error ?? `http_${status}`));
    this.status = status;
    this.payload = payload;
  }
}

class PalamedesTsConsumer {
  private readonly baseUrl: string;

  constructor(baseUrl = "http://127.0.0.1:8787") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private async request<T>(
    path: string,
    init?: RequestInit,
  ): Promise<{ payload: T; response: Response }> {
    const response = await fetch(`${this.baseUrl}${path}`, init);
    const payload = (await response.json()) as T;
    if (!response.ok) {
      throw new PalamedesHttpError(response.status, payload as ErrorEnvelope);
    }
    return { payload, response };
  }

  async getPlan(): Promise<{ envelope: PlanEnvelope; etag: string }> {
    const { payload, response } = await this.request<PlanEnvelope>("/plan");
    return { envelope: payload, etag: response.headers.get("etag") ?? "" };
  }

  async getCycle(limit = 5): Promise<CycleEnvelope> {
    const { payload } = await this.request<CycleEnvelope>(`/cycle?limit=${limit}`);
    return payload;
  }

  async getContracts(): Promise<ContractsEnvelope> {
    const { payload } = await this.request<ContractsEnvelope>("/contracts");
    return payload;
  }

  async getTools(): Promise<ToolCatalogEnvelope> {
    const { payload } = await this.request<ToolCatalogEnvelope>("/tools");
    return payload;
  }

  async updatePlan(payload: Record<string, unknown>, etag: string): Promise<PlanEnvelope> {
    const { payload: result } = await this.request<PlanEnvelope>("/plan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "If-Match": etag,
      },
      body: JSON.stringify(payload),
    });
    return result;
  }

  async executeTool(
    tool: string,
    input: Record<string, unknown>,
    etag = "",
  ): Promise<ToolExecuteEnvelope> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (etag) {
      headers["If-Match"] = etag;
    }
    const { payload } = await this.request<ToolExecuteEnvelope>("/tools/execute", {
      method: "POST",
      headers,
      body: JSON.stringify({ tool, input }),
    });
    return payload;
  }

  async expectConflict(
    payload: Record<string, unknown>,
    etag: string,
  ): Promise<ErrorEnvelope> {
    try {
      await this.updatePlan(payload, etag);
    } catch (error) {
      if (error instanceof PalamedesHttpError) {
        return error.payload;
      }
      throw error;
    }
    throw new Error("expected conflict but update succeeded");
  }

  async runSmoke(): Promise<Record<string, unknown>> {
    const checks: Array<Record<string, unknown>> = [];
    const { envelope: before, etag } = await this.getPlan();
    checks.push({
      name: "plan_envelope",
      ok: before.result_type === "plan" && Boolean(before.fingerprint),
      contract_version: before.contract_version,
    });

    const updated = await this.updatePlan(
      {
        goal: "TS reference consumer updated goal",
        success_metric: "Reach 2 retained pilots",
        deadline: "2026-05-01",
      },
      etag,
    );
    checks.push({
      name: "etag_write",
      ok: updated.plan.goal === "TS reference consumer updated goal" && updated.fingerprint !== before.fingerprint,
      fingerprint_changed: updated.fingerprint !== before.fingerprint,
    });

    const cycle = await this.getCycle(3);
    checks.push({
      name: "cycle_snapshot",
      ok: cycle.result_type === "cycle" && cycle.plan.goal === updated.plan.goal,
      qa_result: cycle.qa.result,
      health_status: cycle.health.status,
    });

    const conflict = await this.expectConflict({ goal: "stale write from ts" }, etag);
    checks.push({
      name: "stale_conflict",
      ok:
        conflict.error_code === "plan_fingerprint_mismatch" &&
        conflict.retryable === true &&
        Boolean(conflict.current_fingerprint),
      error_code: conflict.error_code,
      retryable: conflict.retryable,
      operation: conflict.operation ?? "",
      step: conflict.step ?? "",
    });

    const contracts = await this.getContracts();
    const capabilityNames = contracts.contracts.host_action_contract?.capability_names ?? [];
    checks.push({
      name: "contracts_catalog",
      ok: contracts.result_type === "contracts" && capabilityNames.includes("plan.write"),
      capability_count: capabilityNames.length,
    });

    const tools = await this.getTools();
    checks.push({
      name: "tool_catalog",
      ok:
        tools.result_type === "tool_catalog" &&
        tools.catalog.authoritative === true &&
        tools.catalog.execute_endpoint === "/tools/execute" &&
        tools.tools.some((tool) => tool.name === "request_review"),
      tool_count: tools.catalog.tool_count,
    });

    return {
      ok: checks.every((item) => Boolean(item.ok)),
      runtime: "node_typescript_strip",
      consumer: "palamedes_reference_consumer",
      base_url: this.baseUrl,
      checks,
      final_goal: cycle.plan.goal,
      contract_version: before.contract_version,
      implementation_version: before.implementation_version,
    };
  }
}

function readFlag(name: string, fallback: string): string {
  const args = process.argv.slice(2);
  const index = args.indexOf(name);
  if (index >= 0 && index + 1 < args.length) {
    return args[index + 1] ?? fallback;
  }
  return fallback;
}

async function main(): Promise<void> {
  const baseUrl = readFlag("--base-url", "http://127.0.0.1:8787");
  const mode = readFlag("--mode", "smoke");
  const client = new PalamedesTsConsumer(baseUrl);
  if (mode !== "smoke") {
    throw new Error(`unsupported mode: ${mode}`);
  }
  const report = await client.runSmoke();
  console.log(JSON.stringify(report, null, 2));
}

void main().catch((error: unknown) => {
  if (error instanceof PalamedesHttpError) {
    console.error(
      JSON.stringify(
        {
          ok: false,
          runtime: "node_typescript_strip",
          consumer: "palamedes_reference_consumer",
          status: error.status,
          payload: error.payload,
        },
        null,
        2,
      ),
    );
    process.exitCode = 1;
    return;
  }
  console.error(error);
  process.exitCode = 1;
});
