"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  CallBrief,
  ICP,
  LogEvent,
  ProspectView,
  RunSnapshot,
  eventsUrl,
  fetchRun,
} from "../../lib/api";

const PROSPECT_STEPS = ["queued", "research", "ingest", "analyze", "brief", "done"] as const;

export default function RunView({ runId }: { runId: string }) {
  const [snapshot, setSnapshot] = useState<RunSnapshot | null>(null);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    fetchRun(runId)
      .then((s) => alive && setSnapshot(s))
      .catch((e) => alive && setErr(e.message));
    const es = new EventSource(eventsUrl(runId));
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data);
        if (parsed.type === "state") setSnapshot(parsed.data);
        else if (parsed.type === "log") {
          setLogs((prev) => {
            const next = [...prev, parsed];
            return next.length > 400 ? next.slice(-400) : next;
          });
        }
      } catch {
        /* ignore */
      }
    };
    return () => {
      alive = false;
      es.close();
    };
  }, [runId]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs.length]);

  const status = snapshot?.step ?? "loading";
  const isDone = status === "done";
  const isError = status === "error";

  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_360px]">
      <main className="px-6 py-8 lg:px-12 max-w-4xl">
        <header className="mb-8 flex items-start justify-between gap-4">
          <div>
            <Link
              href="/"
              className="text-xs uppercase tracking-[0.2em] text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              ← Autonomous SDR
            </Link>
            <h1 className="mt-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
              Run <span className="font-mono text-base text-zinc-500">{runId}</span>
            </h1>
            {snapshot?.product && (
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400 max-w-2xl">
                {snapshot.product}
              </p>
            )}
          </div>
          <StatusBadge status={status} done={isDone} error={isError} />
        </header>

        {err && (
          <ErrorBanner message={err} />
        )}
        {snapshot?.error && (
          <ErrorBanner message={snapshot.error} />
        )}

        <Section title="ICP" loading={!snapshot?.icp && !isError}>
          {snapshot?.icp && <ICPCard icp={snapshot.icp} />}
        </Section>

        <Section
          title={`Prospects${snapshot ? ` (${snapshot.prospects.length})` : ""}`}
          loading={!!snapshot && snapshot.prospects.length === 0 && !isError && !isDone}
        >
          <div className="space-y-3">
            {snapshot?.prospects.map((p) => (
              <ProspectCard key={p.candidate.name} prospect={p} />
            ))}
          </div>
        </Section>
      </main>

      <aside className="border-t lg:border-t-0 lg:border-l border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950">
        <div className="sticky top-0 max-h-screen flex flex-col">
          <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Activity
            </span>
            <span className="flex items-center gap-1.5 text-xs text-zinc-500">
              <span
                className={`inline-block h-1.5 w-1.5 rounded-full ${
                  connected ? "bg-emerald-500" : "bg-zinc-400"
                }`}
              />
              {connected ? "live" : "disconnected"}
            </span>
          </div>
          <div
            ref={logRef}
            className="flex-1 overflow-y-auto max-h-[calc(100vh-46px)] lg:max-h-screen px-3 py-3 text-xs font-mono space-y-1"
          >
            {logs.length === 0 && (
              <div className="text-zinc-400 italic">waiting for events…</div>
            )}
            {logs.map((l, i) => (
              <LogLine key={i} log={l} />
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}

function StatusBadge({
  status,
  done,
  error,
}: {
  status: string;
  done: boolean;
  error: boolean;
}) {
  const cls = error
    ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200"
    : done
    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
    : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200";
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${cls}`}>
      {!done && !error && (
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
      )}
      <span className="font-mono">{status}</span>
    </span>
  );
}

function Section({
  title,
  loading,
  children,
}: {
  title: string;
  loading?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-8">
      <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">
        {title}
      </h2>
      {loading ? <Skeleton /> : children}
    </section>
  );
}

function Skeleton() {
  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="space-y-2 animate-pulse">
        <div className="h-3 w-1/3 rounded bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-3 w-2/3 rounded bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-3 w-1/2 rounded bg-zinc-200 dark:bg-zinc-800" />
      </div>
    </div>
  );
}

function ICPCard({ icp }: { icp: ICP }) {
  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 space-y-3">
      <Field label="Industries" values={icp.industries} />
      <Field label="Company size" values={[icp.company_size]} />
      {icp.geographies.length > 0 && (
        <Field label="Geographies" values={icp.geographies} />
      )}
      <Field label="Target roles" values={icp.target_roles} />
      <Field label="Pain signals" values={icp.pain_signals} />
      <details className="text-xs text-zinc-500">
        <summary className="cursor-pointer hover:text-zinc-700 dark:hover:text-zinc-300">
          Search queries ({icp.search_queries.length})
        </summary>
        <ul className="mt-2 space-y-1 pl-3 font-mono">
          {icp.search_queries.map((q, i) => (
            <li key={i}>· {q}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function Field({ label, values }: { label: string; values: string[] }) {
  if (!values || values.length === 0) return null;
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3">
      <div className="text-xs font-medium uppercase tracking-wider text-zinc-500 sm:w-28 sm:shrink-0">
        {label}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {values.map((v, i) => (
          <span
            key={i}
            className="text-xs px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300"
          >
            {v}
          </span>
        ))}
      </div>
    </div>
  );
}

function ProspectCard({ prospect }: { prospect: ProspectView }) {
  const [open, setOpen] = useState(false);
  const ready = prospect.status === "done";
  const errored = prospect.status === "error";

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
      <button
        onClick={() => (ready || prospect.dossier) && setOpen((o) => !o)}
        className="w-full p-4 flex items-center gap-4 text-left hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2">
            <div className="font-medium text-zinc-900 dark:text-zinc-100 truncate">
              {prospect.candidate.name}
            </div>
            <a
              href={prospect.candidate.homepage_url}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 truncate font-mono"
            >
              {prettyUrl(prospect.candidate.homepage_url)}
            </a>
            {prospect.dossier && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                fit {prospect.dossier.fit_score}/10
              </span>
            )}
          </div>
          <div className="mt-0.5 text-xs text-zinc-500 truncate">
            {prospect.candidate.one_liner}
          </div>
        </div>
        <StepIndicator status={prospect.status} />
      </button>
      {errored && (
        <div className="px-4 pb-4 text-xs text-red-600 dark:text-red-400">
          {prospect.error}
        </div>
      )}
      {open && prospect.dossier && (
        <div className="border-t border-zinc-200 dark:border-zinc-800 p-4 space-y-4 bg-zinc-50/50 dark:bg-zinc-950/50">
          <Dossier d={prospect.dossier} />
          {prospect.brief && <Brief b={prospect.brief} />}
        </div>
      )}
    </div>
  );
}

function StepIndicator({ status }: { status: string }) {
  if (status === "error") {
    return (
      <span className="text-xs px-2 py-1 rounded-full bg-red-100 dark:bg-red-950 text-red-800 dark:text-red-200">
        error
      </span>
    );
  }
  const idx = PROSPECT_STEPS.indexOf(status as (typeof PROSPECT_STEPS)[number]);
  return (
    <div className="flex items-center gap-1">
      {PROSPECT_STEPS.slice(1).map((s, i) => {
        const sIdx = i + 1;
        const done = sIdx < idx;
        const active = sIdx === idx;
        return (
          <div key={s} className="flex flex-col items-center gap-1">
            <div
              className={`h-1.5 w-6 rounded-full transition-colors ${
                done
                  ? "bg-zinc-900 dark:bg-zinc-100"
                  : active
                  ? "bg-amber-500 animate-pulse"
                  : "bg-zinc-200 dark:bg-zinc-700"
              }`}
              title={s}
            />
          </div>
        );
      })}
      <span className="ml-2 text-xs font-mono text-zinc-500 w-16 text-right">
        {status}
      </span>
    </div>
  );
}

function Dossier({ d }: { d: { what_they_do: string; decision_makers: string[]; pain_signals_found: string[]; fit_rationale: string; citations: string[] } }) {
  return (
    <div className="space-y-3 text-sm">
      <div>
        <div className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
          What they do
        </div>
        <p className="text-zinc-700 dark:text-zinc-300">{d.what_they_do}</p>
      </div>
      {d.decision_makers.length > 0 && (
        <Field label="Decision makers" values={d.decision_makers} />
      )}
      {d.pain_signals_found.length > 0 && (
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
            Pain signals found
          </div>
          <ul className="list-disc pl-5 space-y-0.5 text-zinc-700 dark:text-zinc-300">
            {d.pain_signals_found.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <div className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
          Fit rationale
        </div>
        <p className="text-zinc-700 dark:text-zinc-300 italic">{d.fit_rationale}</p>
      </div>
      {d.citations.length > 0 && (
        <details className="text-xs text-zinc-500">
          <summary className="cursor-pointer hover:text-zinc-700 dark:hover:text-zinc-300">
            Citations ({d.citations.length})
          </summary>
          <ul className="mt-2 pl-3 space-y-1">
            {d.citations.map((c, i) => (
              <li key={i}>
                <a
                  href={c}
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono break-all hover:text-zinc-900 dark:hover:text-zinc-100"
                >
                  {c}
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function Brief({ b }: { b: CallBrief }) {
  return (
    <div className="border-t border-zinc-200 dark:border-zinc-800 pt-4 space-y-3 text-sm">
      <div className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Call brief
      </div>
      <BriefField label="Opener" value={b.opener} />
      <BriefField label="Value prop" value={b.value_prop} />
      <BriefList label="Discovery questions" items={b.discovery_questions} />
      <BriefList label="Likely objections" items={b.likely_objections} />
      <BriefField label="Next step ask" value={b.next_step_ask} />
    </div>
  );
}

function BriefField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
        {label}
      </div>
      <p className="text-zinc-700 dark:text-zinc-300">{value}</p>
    </div>
  );
}

function BriefList({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
        {label}
      </div>
      <ul className="list-disc pl-5 space-y-0.5 text-zinc-700 dark:text-zinc-300">
        {items.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </div>
  );
}

function LogLine({ log }: { log: LogEvent }) {
  const time = new Date(log.ts * 1000).toLocaleTimeString(undefined, {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const color =
    log.level === "error"
      ? "text-red-500"
      : log.agent
      ? "text-zinc-700 dark:text-zinc-300"
      : "text-zinc-500";
  return (
    <div className={`leading-relaxed ${color}`}>
      <span className="text-zinc-400 dark:text-zinc-600">{time}</span>{" "}
      {log.agent && (
        <span className="text-emerald-700 dark:text-emerald-400">[{log.agent}]</span>
      )}{" "}
      {log.prospect && (
        <span className="text-sky-700 dark:text-sky-400">{log.prospect}:</span>
      )}{" "}
      <span>{log.message}</span>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-6 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-300">
      {message}
    </div>
  );
}

function prettyUrl(u: string): string {
  try {
    const url = new URL(u);
    return url.host + (url.pathname !== "/" ? url.pathname : "");
  } catch {
    return u;
  }
}
