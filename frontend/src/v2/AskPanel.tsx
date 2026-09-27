import { useEffect, useRef, useState } from "react";
import { api, askSuggestions, type AskAnswer } from "../lib/api";
import { useSelection } from "../state";
import { Chip, PillButton } from "./ui";

interface Exchange {
  question: string;
  answer?: AskAnswer;
  failed?: string;
}

/** How the answer was reached. Never implied, always stated. */
function SourceBadge({ answer }: { answer: AskAnswer }) {
  if (answer.source === "gemini_live" && answer.searched) {
    return <Chip tone="good" title="Gemini searched the web for this answer">Live · searched the web</Chip>;
  }
  if (answer.source === "gemini_live") {
    return <Chip tone="good" title="Answered live by Gemini from this campaign's data">Live · from your data</Chip>;
  }
  if (answer.source === "engine") {
    return <Chip tone="info" title="Answered from the engine's own output, with no model call">From your data</Chip>;
  }
  if (answer.source === "saved") {
    return <Chip tone="neutral" title="A saved answer — this demo has no backend behind it">Saved answer</Chip>;
  }
  return <Chip tone="warning">Needs a live key</Chip>;
}

export function AskPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { trendId } = useSelection();
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<Exchange[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const suggestions = askSuggestions();

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [history, busy]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || busy) return;
    setQuestion("");
    setHistory((h) => [...h, { question: q }]);
    setBusy(true);
    try {
      const answer = await api.ask(q, trendId ?? undefined);
      setHistory((h) => h.map((x, i) => (i === h.length - 1 ? { ...x, answer } : x)));
    } catch (err) {
      setHistory((h) =>
        h.map((x, i) =>
          i === h.length - 1
            ? { ...x, failed: err instanceof Error ? err.message : String(err) }
            : x,
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-30"
        style={{ background: "rgba(0,0,0,0.45)" }}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Ask Gemini"
        className="fixed inset-y-0 right-0 z-40 flex w-full flex-col bg-surface shadow-2xl sm:max-w-[440px]"
      >
        <header className="flex items-center justify-between gap-3 border-b border-hairline px-4 py-3">
          <div className="flex items-center gap-2">
            <GeminiGlyph />
            <span className="text-[15px] font-medium">Ask Gemini</span>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="v2-pill px-3 py-1.5 text-[13px] text-ink-2 ring-1 ring-hairline hover:bg-raised"
          >
            Close
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {history.length === 0 && (
            <div>
              <p className="text-[14px] leading-relaxed text-ink-2">
                Ask about this campaign or about what's happening in the market. Questions about
                the recommendation are answered from the engine's own numbers; questions about the
                world are searched, with sources.
              </p>
              <div className="mt-4 space-y-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="block w-full rounded-lg bg-raised px-3 py-2.5 text-left text-[13px] ring-1 ring-hairline hover:bg-surface"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-5">
            {history.map((x, i) => (
              <div key={i}>
                <p className="text-[14px] font-medium">{x.question}</p>
                {x.answer ? (
                  <div className="mt-2">
                    <SourceBadge answer={x.answer} />
                    <p className="mt-2 whitespace-pre-line text-[14px] leading-relaxed text-ink-2">
                      {x.answer.text}
                    </p>
                    {x.answer.citations.length > 0 && (
                      <ul className="mt-3 space-y-1.5 border-t pt-2" style={{ borderColor: "var(--gridline)" }}>
                        {x.answer.citations.slice(0, 5).map((c) => (
                          <li key={c.url} className="text-[12px]">
                            <a
                              href={c.url}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="underline decoration-dotted underline-offset-2"
                              style={{ color: "var(--series-1)" }}
                            >
                              {c.title || c.url}
                            </a>
                            {c.publisher && <span className="text-muted"> — {c.publisher}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : x.failed ? (
                  <p className="mt-2 text-[13px]" style={{ color: "var(--status-critical)" }}>
                    Couldn't reach Gemini: {x.failed}
                  </p>
                ) : (
                  <p className="mt-2 text-[13px] text-muted">Thinking…</p>
                )}
              </div>
            ))}
          </div>
          <div ref={endRef} />
        </div>

        <form
          className="flex items-center gap-2 border-t border-hairline px-4 py-3"
          onSubmit={(e) => {
            e.preventDefault();
            void send(question);
          }}
        >
          <input
            ref={inputRef}
            id="ask-gemini-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            maxLength={500}
            placeholder="Ask something…"
            className="v2-pill min-w-0 flex-1 bg-raised px-4 py-2.5 text-[14px] ring-1 ring-hairline focus:outline-none focus:ring-2"
            style={{ color: "var(--text-primary)" }}
          />
          <PillButton disabled={busy || !question.trim()}>{busy ? "…" : "Ask"}</PillButton>
        </form>
      </aside>
    </>
  );
}

/** A four-point spark — the shape Google uses for its AI features, drawn here
 *  rather than borrowed as an asset. */
export function GeminiGlyph({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 1.5c.5 4.9 4.1 8.5 9 9-4.9.5-8.5 4.1-9 9-.5-4.9-4.1-8.5-9-9 4.9-.5 8.5-4.1 9-9z"
        fill="currentColor"
      />
    </svg>
  );
}
