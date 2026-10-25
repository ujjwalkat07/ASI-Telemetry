"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Activity,
  ArrowUpRight,
  Bot,
  Check,
  Code2,
  Copy,
  Cpu,
  ExternalLink,
  Key,
  Layers,
  Network,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { CodeBlock, dracula } from "react-code-blocks";
import { cn } from "@/lib/utils";

interface HomeSectionProps {
  apiKey?: string;
  projectName?: string;
}

// Tailored high-contrast code theme for crystal-clear readability
const highContrastTheme = {
  ...dracula,
  backgroundColor: "transparent",
  lineNumberColor: "#475569",
  lineNumberBgColor: "transparent",
  textColor: "#f8fafc", // Crisp light text, NEVER black
  keywordColor: "#f43f5e", // Def, import, from, return, if, class
  functionColor: "#38bdf8", // Function calls & definitions
  titleColor: "#38bdf8", // Function name in def run_agent()
  stringColor: "#34d399", // Strings
  commentColor: "#94a3b8", // Comments
  variableColor: "#f8fafc", // Variables
  numberColor: "#fbbf24", // Numbers
  builtInColor: "#a78bfa", // Builtin types / print
  metaColor: "#ec4899", // Decorators (@traceable)
  metaKeywordColor: "#ec4899",
  attributeColor: "#38bdf8",
  typeColor: "#38bdf8",
  literalColor: "#fbbf24",
  symbolColor: "#fbbf24",
};

const customBlockStyle: Record<string, string> = {
  backgroundColor: "transparent",
  padding: "1rem 1.25rem",
  fontSize: "0.825rem",
  fontFamily: 'var(--font-mono), ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  lineHeight: "1.7",
  color: "#f8fafc", // Explicit high-contrast text
};

export function HomeSection({
  apiKey: initialApiKey = "<your-asi-api-key>",
  projectName = "asi-production-fleet",
}: HomeSectionProps) {
  // Language tab
  const [selectedLanguage, setSelectedLanguage] = React.useState<"python">("python");

  // Dependency manager tab: pip vs uv vs local
  const [depManager, setDepManager] = React.useState<"pip" | "uv">("pip");

  // Environment format tab: Shell vs .env
  const [envFormat, setEnvFormat] = React.useState<"Shell" | ".env">("Shell");

  // Quickstart SDK usage showcase tab
  const [sdkUsageTab, setSdkUsageTab] = React.useState<
    "unified" | "gemini" | "openai" | "swarm" | "metrics"
  >("unified");

  const [realKey, setRealKey] = React.useState<string | null>(null);
  const [copiedSection, setCopiedSection] = React.useState<string | null>(null);

  React.useEffect(() => {
    import("@/lib/api-keys").then(({ fetchBackendApiKeys }) => {
      fetchBackendApiKeys().then((keys) => {
        if (keys && keys.length > 0) {
          const active = keys.find((k) => k.status === "active") || keys[0];
          if (active) {
            setRealKey(active.fullKey || active.keyPrefix);
          }
        }
      });
    });
  }, []);

  const activeApiKey = realKey || initialApiKey;

  const handleCopy = (text: string, sectionId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(sectionId);
    setTimeout(() => {
      setCopiedSection(null);
    }, 2000);
  };

  // Code snippets: Installation
  const installCode =
    depManager === "pip"
      ? `# Install official ASI Telemetry SDK\npip install -U asi-telemetry\n\n# Optional: install model providers for auto-instrumentation\npip install google-genai openai`
      : `# Install with uv package manager\nuv add asi-telemetry\n\n# Optional: model providers\nuv add google-genai openai`;

  // Code snippets: Environment
  const envCodeShell = `export ASI_TELEMETRY_ENDPOINT=http://localhost:8080
export ASI_API_KEY=${activeApiKey}
export ASI_PROJECT="${projectName}"

# Optional LLM credentials for traced model calls
export GOOGLE_API_KEY=<your-google-api-key>
export OPENAI_API_KEY=<your-openai-api-key>`;

  const envCodeDotEnv = `ASI_TELEMETRY_ENDPOINT=http://localhost:8080
ASI_API_KEY=${activeApiKey}
ASI_PROJECT="${projectName}"

# Optional LLM credentials for traced model calls
GOOGLE_API_KEY=<your-google-api-key>
OPENAI_API_KEY=<your-openai-api-key>`;

  const envCode = envFormat === "Shell" ? envCodeShell : envCodeDotEnv;

  // Code snippets: Latest SDK Usages
  const usageSnippets: Record<
    "unified" | "gemini" | "openai" | "swarm" | "metrics",
    {
      title: string;
      badge: string;
      fileName: string;
      description: string;
      code: string;
    }
  > = {
    unified: {
      title: "Unified Telemetry Client",
      badge: "Recommended",
      fileName: "agent_quickstart.py",
      description:
        "Initialize ASI_Telemetry once with credentials to automatically manage tool execution monitoring, model auto-instrumentation, and distributed trace propagation.",
      code: `from asi_telemetry import ASI_Telemetry
from google import genai

# 1. Initialize the unified telemetry client
observe = ASI_Telemetry(
    api_key="${activeApiKey}",
    agent_name="production-assistant",
    backend_url="http://localhost:8080"
)

# 2. Auto-instrument Gemini client (tracks tokens, latency & costs)
client = genai.Client()
observe.instrument_gemini(client)

# 3. Track tool execution latency & ClickHouse metrics
@observe.track("knowledge_search")
@observe.traceable(name="search_vector_db", run_type="tool")
def search_vector_db(query: str):
    return f"Retrieved knowledge context for: {query}"

# 4. Trace high-level agent decision workflows
@observe.traceable(name="autonomous_decision_cycle", run_type="chain")
def run_agent(task_prompt: str):
    context = search_vector_db(task_prompt)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Task: {task_prompt}\\nContext: {context}"
    )
    return {"status": "success", "result": response.text}

if __name__ == "__main__":
    result = run_agent("Analyze telemetry logs and suggest optimizations")
    print("Execution complete:", result)`,
    },
    gemini: {
      title: "Google Gemini Auto-Instrumentation",
      badge: "LLM Observability",
      fileName: "gemini_tracing.py",
      description:
        "Native auto-instrumentation for the official Google GenAI SDK. Automatically records model names, input/output tokens, execution latency, and cost estimation to ClickHouse.",
      code: `import os
from google import genai
from asi_telemetry import traceable, instrument_gemini

# 1. Initialize Google GenAI client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. Auto-instrument client for automatic token counting & tracing
instrument_gemini(client)

@traceable(name="gemini_reasoning_step", run_type="llm", metadata={"model": "gemini-2.5-flash"})
def generate_solution(prompt: str) -> str:
    """Captured live in ASI Telemetry with prompt, response, tokens & cost."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Solve step-by-step: {prompt}"
    )
    return response.text

if __name__ == "__main__":
    reply = generate_solution("Plan a multi-hop agent routing architecture")
    print("Gemini Output:", reply)`,
    },
    openai: {
      title: "OpenAI & LLM Providers",
      badge: "Chat & Reasoning",
      fileName: "openai_tracing.py",
      description:
        "Seamless auto-instrumentation for OpenAI, ASI-1, and compatible LLM clients. Captures ChatCompletions, prompt tokens, completion tokens, and real-time costs.",
      code: `import os
from openai import OpenAI
from asi_telemetry import traceable, instrument_openai

# 1. Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Auto-instrument client to track model tokens and costs
instrument_openai(client)

@traceable(name="openai_agent_reasoning", run_type="llm")
def reason_with_openai(user_message: str):
    """Execution telemetry streamed immediately to backend ClickHouse."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    result = reason_with_openai("Synthesize multi-agent coordination rules")
    print(result)`,
    },
    swarm: {
      title: "Multi-Agent Swarms & Distributed Context",
      badge: "Swarm Tracing",
      fileName: "agent_swarm.py",
      description:
        "Propagate distributed trace context (trace_id, parent_id, span_id) seamlessly across autonomous agents, microservices, and network boundaries.",
      code: `import time
from asi_telemetry import traceable, create_trace_context, set_agent_info

# --- AGENT A: Orchestrator ---
set_agent_info(agent_name="Orchestrator", agent_address="agent1_orchestrator")

@traceable(name="plan_and_delegate", run_type="chain")
def orchestrator(task: str):
    print(f"[Orchestrator] Planning task: {task}")
    # Generate distributed trace context to pass across network
    trace_context = create_trace_context()
    return {"task": task, "trace_context": trace_context}

# --- AGENT B: Specialist Worker ---
set_agent_info(agent_name="Specialist Worker", agent_address="agent1_worker")

@traceable(name="execute_specialist_job", run_type="tool")
def specialist_worker(message: dict):
    # Execution automatically links to Agent A's root span!
    task = message.get("task")
    time.sleep(0.04)
    return f"Completed processing for: {task}"

if __name__ == "__main__":
    delegated_payload = orchestrator("Verify network telemetry anomalies")
    worker_reply = specialist_worker(delegated_payload)
    print("[Swarm Result]:", worker_reply)`,
    },
    metrics: {
      title: "Tool & Agent Runtime Metrics",
      badge: "Runtime Metrics",
      fileName: "metrics_monitoring.py",
      description:
        "Non-blocking background workers measure tool execution latency, success/error rates, and p95 performance with zero overhead on agent response times.",
      code: `import time
from asi_telemetry import MetricsTracker

# Initialize lightweight runtime performance tracker
tracker = MetricsTracker(
    agent_name="database-indexer",
    backend_url="http://localhost:8080"
)

@tracker.track(tool_name="sync_database_records")
def sync_records(batch_size: int = 500):
    """Measures latency, request count, and error rates in ClickHouse."""
    time.sleep(0.02)
    return {"status": "synced", "records": batch_size}

if __name__ == "__main__":
    print("Executing tracked tool batches...")
    for _ in range(5):
        sync_records(1000)
    print("Telemetry metrics dispatched asynchronously to ClickHouse.")`,
    },
  };

  const activeSnippet = usageSnippets[sdkUsageTab];

  return (
    <div className="max-w-4xl mx-auto py-4 space-y-8 text-foreground">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-b from-card via-card to-muted/20 p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Quickstart & Telemetry Setup
            </h1>
            <p className="text-sm text-muted-foreground max-w-2xl">
              Instrument autonomous agents, multi-model LLMs (Gemini, OpenAI, ASI-1), and tool pipelines with distributed tracing and zero-overhead performance tracking.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/api-keys"
              className={cn(buttonVariants({ size: "sm" }), "gap-1.5 text-xs font-semibold shadow-xs")}
            >
              <Key className="h-3.5 w-3.5" />
              Manage API Keys
            </Link>
          </div>
        </div>
      </div>

      {/* Steps Flow */}
      <div className="space-y-8">
        {/* Step 1: Select a language */}
        <div className="relative flex gap-4 group">
          <div className="relative flex flex-col items-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-xs z-10 shrink-0">
              1
            </div>
            <div className="absolute top-8 bottom-0 w-[2px] bg-border" />
          </div>

          <div className="flex-1 min-w-0 space-y-3 pt-0.5 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-foreground tracking-tight">
                  Select a language & runtime
                </h2>
                <p className="text-xs text-muted-foreground">
                  Choose your agent runtime environment
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Python */}
              <button
                type="button"
                onClick={() => setSelectedLanguage("python")}
                className={cn(
                  "relative flex items-center justify-between p-3.5 rounded-xl border text-left transition-all",
                  selectedLanguage === "python"
                    ? "border-primary bg-primary/5 ring-1 ring-primary/20 shadow-xs"
                    : "border-border bg-card hover:bg-muted/40 hover:border-border/80"
                )}
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-card border border-border shadow-xs shrink-0">
                    <Image
                      src="/image.png"
                      alt="Python"
                      width={18}
                      height={18}
                      className="h-4.5 w-4.5 object-contain"
                    />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      Python
                      <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-muted text-muted-foreground">
                        3.10+
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground">Official SDK</div>
                  </div>
                </div>
                {selectedLanguage === "python" && (
                  <Check className="h-4 w-4 text-primary shrink-0" />
                )}
              </button>
            </div>
          </div>
          </div>

        {/* Step 2: Install dependencies */}
        <div className="relative flex gap-4 group">
          <div className="relative flex flex-col items-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-xs z-10 shrink-0">
              2
            </div>
            <div className="absolute top-8 bottom-0 w-[2px] bg-border" />
          </div>

          <div className="flex-1 min-w-0 space-y-3 pt-0.5 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-foreground tracking-tight">
                  Install dependencies
                </h2>
                <p className="text-xs text-muted-foreground">
                  Install the lightweight SDK via pip or uv
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-border/80 bg-card overflow-hidden shadow-xs">
              {/* Terminal Title Bar */}
              <div className="flex items-center justify-between border-b border-border/80 px-4 py-2.5 bg-muted/40">
                <div className="flex items-center gap-3">
                  {/* macOS Dots */}
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80 inline-block" />
                  </div>

                  <div className="h-4 w-px bg-border/60 mx-0.5" />

                  {/* Switcher */}
                  <div className="flex items-center gap-1 bg-muted p-0.5 rounded-md">
                    <button
                      type="button"
                      onClick={() => setDepManager("pip")}
                      className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                        depManager === "pip"
                          ? "bg-background text-foreground shadow-xs font-semibold"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      pip
                    </button>
                    <button
                      type="button"
                      onClick={() => setDepManager("uv")}
                      className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                        depManager === "uv"
                          ? "bg-background text-foreground shadow-xs font-semibold"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      uv
                    </button>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleCopy(installCode, "install")}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground transition-colors hover:bg-muted"
                  title="Copy snippet"
                >
                  {copiedSection === "install" ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                      <span className="text-emerald-600 dark:text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Code Surface */}
              <div className="overflow-x-auto bg-[#090d16] text-[#f8fafc]">
                <CodeBlock
                  text={installCode}
                  language="bash"
                  showLineNumbers={false}
                  theme={highContrastTheme}
                  customStyle={customBlockStyle}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: Configure environment */}
        <div className="relative flex gap-4 group">
          <div className="relative flex flex-col items-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-xs z-10 shrink-0">
              3
            </div>
            <div className="absolute top-8 bottom-0 w-[2px] bg-border" />
          </div>

          <div className="flex-1 min-w-0 space-y-3 pt-0.5 pb-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-foreground tracking-tight">
                  Configure telemetry environment
                </h2>
                <p className="text-xs text-muted-foreground">
                  Set endpoint and telemetry credentials for ClickHouse ingestion
                </p>
              </div>

              <Link
                href="/api-keys"
                className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-1.5 text-xs font-medium")}
              >
                <Key className="h-3.5 w-3.5" />
                Manage API Keys
              </Link>
            </div>

            <div className="rounded-xl border border-border/80 bg-card overflow-hidden shadow-xs">
              {/* Terminal Title Bar */}
              <div className="flex items-center justify-between border-b border-border/80 px-4 py-2.5 bg-muted/40">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80 inline-block" />
                  </div>

                  <div className="h-4 w-px bg-border/60 mx-0.5" />

                  <div className="flex items-center gap-1 bg-muted p-0.5 rounded-md">
                    <button
                      type="button"
                      onClick={() => setEnvFormat("Shell")}
                      className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                        envFormat === "Shell"
                          ? "bg-background text-foreground shadow-xs font-semibold"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Shell (export)
                    </button>
                    <button
                      type="button"
                      onClick={() => setEnvFormat(".env")}
                      className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                        envFormat === ".env"
                          ? "bg-background text-foreground shadow-xs font-semibold"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      .env
                    </button>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleCopy(envCode, "env")}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground transition-colors hover:bg-muted"
                  title="Copy snippet"
                >
                  {copiedSection === "env" ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                      <span className="text-emerald-600 dark:text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Code Surface */}
              <div className="overflow-x-auto bg-[#090d16] text-[#f8fafc]">
                <CodeBlock
                  text={envCode}
                  language="bash"
                  showLineNumbers={false}
                  theme={highContrastTheme}
                  customStyle={customBlockStyle}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Step 4: Run the quickstart & Latest Usages */}
        <div className="relative flex gap-4 group">
          <div className="relative flex flex-col items-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-xs z-10 shrink-0">
              4
            </div>
            <div className="absolute top-8 bottom-0 w-[2px] bg-border" />
          </div>

          <div className="flex-1 min-w-0 space-y-3 pt-0.5 pb-4">
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-foreground tracking-tight">
                  Run the quickstart & explore latest SDK patterns
                </h2>
                <span className="text-xs text-muted-foreground font-mono">
                  {activeSnippet.fileName}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Select an integration pattern below to see the latest SDK usage
              </p>
            </div>

            {/* SDK Usage Selector Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              <button
                type="button"
                onClick={() => setSdkUsageTab("unified")}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 border",
                  sdkUsageTab === "unified"
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted/50"
                )}
              >
                <Sparkles className="h-3.5 w-3.5" />
                Unified Client
                <span
                  className={cn(
                    "text-[10px] px-1 py-0.2 rounded font-semibold",
                    sdkUsageTab === "unified"
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                  )}
                >
                  Recommended
                </span>
              </button>

              <button
                type="button"
                onClick={() => setSdkUsageTab("gemini")}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 border",
                  sdkUsageTab === "gemini"
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted/50"
                )}
              >
                <Bot className="h-3.5 w-3.5" />
                Google Gemini Tracing
              </button>

              <button
                type="button"
                onClick={() => setSdkUsageTab("openai")}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 border",
                  sdkUsageTab === "openai"
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted/50"
                )}
              >
                <Zap className="h-3.5 w-3.5" />
                OpenAI & LLMs
              </button>

              <button
                type="button"
                onClick={() => setSdkUsageTab("swarm")}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 border",
                  sdkUsageTab === "swarm"
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted/50"
                )}
              >
                <Network className="h-3.5 w-3.5" />
                Multi-Agent Swarm
              </button>

              <button
                type="button"
                onClick={() => setSdkUsageTab("metrics")}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 border",
                  sdkUsageTab === "metrics"
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted/50"
                )}
              >
                <Activity className="h-3.5 w-3.5" />
                Tool Metrics
              </button>
            </div>

            {/* Description Card */}
            <div className="rounded-lg border border-border/70 bg-muted/30 px-3.5 py-2.5 text-xs text-muted-foreground flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-semibold text-foreground shrink-0">{activeSnippet.title}:</span>
                <span className="truncate">{activeSnippet.description}</span>
              </div>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-background border border-border text-foreground shrink-0">
                {activeSnippet.badge}
              </span>
            </div>

            {/* Code Surface */}
            <div className="rounded-xl border border-border/80 bg-card overflow-hidden shadow-xs">
              <div className="flex items-center justify-between border-b border-border/80 px-4 py-2.5 bg-muted/40">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80 inline-block" />
                  </div>
                  <span className="text-xs font-mono text-muted-foreground">
                    {activeSnippet.fileName}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => handleCopy(activeSnippet.code, "quickstart")}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground transition-colors hover:bg-muted"
                  title="Copy snippet"
                >
                  {copiedSection === "quickstart" ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                      <span className="text-emerald-600 dark:text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy Code</span>
                    </>
                  )}
                </button>
              </div>

              <div className="overflow-x-auto bg-[#090d16] text-[#f8fafc]">
                <CodeBlock
                  text={activeSnippet.code}
                  language="python"
                  showLineNumbers={false}
                  theme={highContrastTheme}
                  customStyle={customBlockStyle}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Step 5: Verify Live Telemetry */}
        <div className="relative flex gap-4 group">
          <div className="relative flex flex-col items-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-xs z-10 shrink-0">
              5
            </div>
          </div>

          <div className="flex-1 min-w-0 space-y-3 pt-0.5">
            <div>
              <h2 className="text-sm font-semibold text-foreground tracking-tight">
                Verify live telemetry stream
              </h2>
              <p className="text-xs text-muted-foreground">
                As soon as your script executes, spans, tool calls, and tokens stream directly to ClickHouse
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Link
                href="/llm-traces"
                className="group/card flex items-center justify-between p-4 rounded-xl border border-border bg-card hover:bg-muted/40 hover:border-border/80 transition-all shadow-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary shrink-0 group-hover/card:scale-105 transition-transform">
                    <Bot className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      View LLM Traces
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-primary/10 text-primary font-medium">
                        Live
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      Inspect token usage, latencies & costs
                    </div>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover/card:text-foreground transition-colors" />
              </Link>

              <Link
                href="/tool-monitoring"
                className="group/card flex items-center justify-between p-4 rounded-xl border border-border bg-card hover:bg-muted/40 hover:border-border/80 transition-all shadow-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shrink-0 group-hover/card:scale-105 transition-transform">
                    <Activity className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      Tool Performance
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium">
                        Metrics
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      Monitor error rates, p95 latencies & health
                    </div>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover/card:text-foreground transition-colors" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
