"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createRun } from "./lib/api";

const EXAMPLES = [
  "AI observability for Rust microservices — auto-instrumentation, anomaly detection, alerts that don't page on noise.",
  "Compliance automation for Series B fintechs — SOC2, ISO 27001, evidence collection, vendor reviews.",
  "Voice AI for outbound recruiting — books interviews end-to-end, integrates with Greenhouse and Lever.",
];

export default function Home() {
  const router = useRouter();
  const [product, setProduct] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!product.trim() || busy) return;
    setBusy(true);
    setErr(null);
    try {
      const { run_id } = await createRun(product.trim());
      router.push(`/runs/${run_id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-2xl">
        <div className="mb-12">
          <div className="text-xs uppercase tracking-[0.2em] text-zinc-500 mb-3">
            Autonomous SDR
          </div>
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Find your next 5 buyers.
          </h1>
          <p className="mt-3 text-zinc-600 dark:text-zinc-400 text-lg">
            Describe what you sell. The agent researches the open web, builds a grounded
            dossier on each prospect, and writes you a call brief.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              What do you sell?
            </span>
            <textarea
              value={product}
              onChange={(e) => setProduct(e.target.value)}
              rows={5}
              placeholder="e.g. AI observability for Rust microservices…"
              className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-4 py-3 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-200"
            />
          </label>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-zinc-500">Try:</span>
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setProduct(ex)}
                className="text-xs px-2.5 py-1 rounded-full border border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:border-zinc-500 dark:hover:border-zinc-500 transition-colors"
              >
                example {i + 1}
              </button>
            ))}
          </div>

          {err && (
            <div className="rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-300">
              {err}
            </div>
          )}

          <button
            type="submit"
            disabled={busy || !product.trim()}
            className="w-full sm:w-auto inline-flex items-center justify-center rounded-full bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-6 py-3 text-sm font-medium hover:bg-zinc-700 dark:hover:bg-zinc-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {busy ? "Starting run…" : "Find buyers →"}
          </button>
        </form>
      </div>
    </div>
  );
}
