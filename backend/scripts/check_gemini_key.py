"""Does this Gemini key work, and does it come with grounding?

One real call, so the answer is observed rather than assumed. Everything the
console needs from Gemini rides on Grounding with Google Search: without it the
trend scout has no live web to read and the Ask panel cannot cite anything.
Whether grounding is included on a free-tier key is the one question worth
answering before wiring the key into a deployment.

    python scripts/check_gemini_key.py                # reads GEMINI_API_KEY
    python scripts/check_gemini_key.py AIza...        # or takes it as an argument

The key is read from the environment or the command line and is never printed,
logged, or written anywhere.
"""

from __future__ import annotations

import os
import sys

QUESTION = (
    "In one short paragraph: what running-related trend is getting attention "
    "on YouTube and social media this month? Name the trend and say why now."
)


def main() -> int:
    key = (sys.argv[1] if len(sys.argv) > 1 else "") or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("No key. Pass it as an argument or set GEMINI_API_KEY.")
        return 2

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("The SDK is missing. Run:  pip install -r requirements.txt")
        return 2

    client = genai.Client(api_key=key)
    model = os.environ.get("GEMINI_GROUNDED_MODEL", "gemini-2.5-flash")

    # 1 · plain call — is the key valid at all?
    print(f"model              {model}")
    try:
        client.models.generate_content(model=model, contents="Reply with the word: ok")
    except Exception as exc:  # noqa: BLE001 — the message is the whole point
        print(f"key                REJECTED\n\n{_explain(exc)}")
        return 1
    print("key                works")

    # 2 · grounded call — is Google Search included on this key's tier?
    try:
        response = client.models.generate_content(
            model=model,
            contents=QUESTION,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            ),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"grounding          NOT AVAILABLE on this key\n\n{_explain(exc)}")
        print(
            "\nThe console still runs: trend scouting falls back to the saved\n"
            "signals and the Ask panel answers from the engine's own numbers.\n"
            "What you lose is the live web and the citations under each answer."
        )
        return 1

    chunks = []
    meta = getattr(response.candidates[0], "grounding_metadata", None) if response.candidates else None
    for chunk in getattr(meta, "grounding_chunks", None) or []:
        web = getattr(chunk, "web", None)
        if web is not None:
            chunks.append((getattr(web, "title", "") or "", getattr(web, "uri", "") or ""))

    queries = list(getattr(meta, "web_search_queries", None) or [])
    print(f"grounding          {'works' if chunks or queries else 'accepted, but nothing was searched'}")
    print(f"searches made      {len(queries)}" + (f"  {queries[:3]}" if queries else ""))
    print(f"citations returned {len(chunks)}")
    print("\n--- answer ---")
    print((response.text or "").strip()[:900])
    if chunks:
        print("\n--- sources ---")
        for title, uri in chunks[:6]:
            print(f"  {title or '(untitled)'}\n    {uri}")
        print(
            "\nShowing these sources is a condition of using grounding, which is why\n"
            "the console prints them under every scouted trend and every answer."
        )
    else:
        print(
            "\nNo citations came back. The call was accepted but the model answered\n"
            "from its own knowledge, so nothing here is live."
        )
    print("\nTo use it:  set GEMINI_MODE=live and GEMINI_API_KEY in backend/.env")
    return 0


def _explain(exc: Exception) -> str:
    text = str(exc)
    if "API_KEY_INVALID" in text or "API key not valid" in text:
        return "The key itself was refused. Check it at https://aistudio.google.com/apikey"
    if "PERMISSION_DENIED" in text or "403" in text:
        return f"The key is not allowed to do this:\n{text[:400]}"
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return f"Quota, not permission — try again shortly:\n{text[:400]}"
    return text[:600]


if __name__ == "__main__":
    raise SystemExit(main())
