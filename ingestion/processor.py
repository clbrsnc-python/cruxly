import json
import re
from datetime import datetime
import feedparser
import pytz
from ingestion.sources import get_active_sources

try:
    from google import genai
except Exception:
    genai = None

try:
    from groq import Groq
except Exception:
    Groq = None

IST = pytz.timezone("Asia/Kolkata")


def _clean_text(raw: str) -> str:
    """Strips HTML tags and excess whitespace from RSS snippets."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss_items(max_per_feed: int = 8) -> list[dict]:
    """Collects latest headlines, short descriptions, and direct links from active sources."""
    collected = []
    for source in get_active_sources():
        for rss_url in source.get("rss_urls", []):
            try:
                parsed = feedparser.parse(rss_url)
                for entry in parsed.entries[:max_per_feed]:
                    title = _clean_text(entry.get("title", ""))
                    link = (entry.get("link") or "").strip()
                    snippet = _clean_text(entry.get("summary") or entry.get("description") or "")[:450]
                    if title and link:
                        collected.append(
                            {
                                "source_id": source["id"],
                                "source_name": source["name"],
                                "language": source["language"],
                                "geography": source["default_geography"],
                                "title": title,
                                "snippet": snippet,
                                "url": link,
                                "published": entry.get("published", ""),
                            }
                        )
            except Exception:
                continue
    return collected


def cluster_items(items: list[dict], max_clusters: int = 8) -> list[list[dict]]:
    """Groups articles covering the same event across distinct newspapers by keyword overlap."""
    clusters: list[list[dict]] = []
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this", "into",
        "over", "after", "amid", "says", "new", "india", "news",
    }

    def tokenize(text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        return {w for w in words if w not in stop_words}

    for item in items:
        tokens = tokenize(item["title"])
        placed = False
        for cluster in clusters:
            existing_sources = {c["source_id"] for c in cluster}
            if item["source_id"] in existing_sources:
                continue
            ref_tokens = tokenize(cluster[0]["title"])
            if tokens and ref_tokens and len(tokens & ref_tokens) >= 2:
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])

    clusters.sort(key=lambda c: len(c), reverse=True)
    return clusters[:max_clusters]


def _build_synthesis_prompt(cluster: list[dict]) -> str:
    source_notes = "\n".join(
        f"- [{it['source_name']} ({it['language']})]: {it['title']} — {it['snippet']}"
        for it in cluster
    )
    return (
        "You are an objective news editor for Cruxly. Synthesize the following multi-source news notes "
        "into an original, neutral, abridged summary in BOTH English and Bengali. "
        "Do not copy verbatim sentences. Return valid JSON ONLY with keys: "
        "headline_en, primary_genre, geography, what_happened_en, key_details_en, what_happened_bn.\n\n"
        f"Source Notes:\n{source_notes}"
    )


def synthesize_cluster(
    cluster: list[dict],
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
) -> dict:
    """
    Generates an original consolidated abridged summary in English and Bengali.
    Supports Gemini or Groq automatically, with a clean fallback when neither key is set.
    """
    primary = cluster[0]
    source_names = sorted({item["source_name"] for item in cluster})
    geography = primary.get("geography", "National")
    prompt = _build_synthesis_prompt(cluster)
    raw_json = None

    # 1. Try Gemini if configured
    if gemini_api_key and genai is not None:
        try:
            client = genai.Client(api_key=gemini_api_key)
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw_json = resp.text
        except Exception:
            raw_json = None

    # 2. Try Groq if Gemini wasn't used and GROQ_API_KEY is configured
    if not raw_json and groq_api_key and Groq is not None:
        try:
            g_client = Groq(api_key=groq_api_key)
            chat_resp = g_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw_json = chat_resp.choices[0].message.content
        except Exception:
            raw_json = None

    if raw_json:
        try:
            cleaned = re.sub(r"^```json|```$", "", raw_json.strip()).strip()
            parsed = json.loads(cleaned)
            return {
                "headline_en": parsed.get("headline_en") or primary["title"],
                "primary_genre": parsed.get("primary_genre") or "General",
                "geography": parsed.get("geography") or geography,
                "summary_en": {
                    "what_happened": parsed.get("what_happened_en", ""),
                    "key_details": parsed.get("key_details_en", ""),
                    "sources": source_names,
                },
                "summary_bn": {
                    "what_happened": parsed.get("what_happened_bn", ""),
                },
            }
        except Exception:
            pass

    # 3. Clean fallback when no LLM API key is set yet
    combined_brief = primary["snippet"] or primary["title"]
    return {
        "headline_en": primary["title"],
        "primary_genre": "National" if geography == "National" else "Regional",
        "geography": geography,
        "summary_en": {
            "what_happened": combined_brief,
            "key_details": f"Corroborated across {', '.join(source_names)}. Click original publisher links for full coverage.",
            "sources": source_names,
        },
        "summary_bn": {
            "what_happened": f"সূত্র: {', '.join(source_names)} — {primary['title']}",
        },
    }


def run_ingestion_cycle(
    supabase,
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
) -> dict:
    """Executes one full collect -> cluster -> synthesize -> publish cycle."""
    raw_items = fetch_rss_items(max_per_feed=6)
    fetched_count = len(raw_items)
    if not raw_items:
        return {"fetched": 0, "published": 0, "message": "No RSS entries reachable right now."}

    clusters = cluster_items(raw_items, max_clusters=8)
    published_count = 0
    errors: list[str] = []
    now_ist_iso = datetime.now(IST).isoformat()

    for cluster in clusters:
        synthesized = synthesize_cluster(
            cluster,
            gemini_api_key=gemini_api_key,
            groq_api_key=groq_api_key,
        )
        story_payload = {
            "headline_en": synthesized["headline_en"],
            "primary_genre": synthesized["primary_genre"],
            "geography": synthesized["geography"],
            "summary_en": synthesized["summary_en"],
            "summary_bn": synthesized["summary_bn"],
            "status": "published",
            "published_at": now_ist_iso,
        }
        try:
            insert_res = supabase.table("stories").insert(story_payload).execute()
            if insert_res.data:
                story_id = insert_res.data[0]["id"]
                refs = [
                    {
                        "story_id": story_id,
                        "publisher_name": item["source_name"],
                        "article_url": item["url"],
                        "language": item["language"],
                    }
                    for item in cluster
                ]
                try:
                    supabase.table("story_references").insert(refs).execute()
                except Exception as ref_exc:
                    errors.append(f"Reference insert error: {ref_exc}")
                published_count += 1
        except Exception as ins_exc:
            errors.append(str(ins_exc))
            continue

    # Explicitly discard temporary source text immediately after processing
    raw_items.clear()
    clusters.clear()

    if published_count == 0 and errors:
        return {
            "fetched": fetched_count,
            "published": 0,
            "message": f"Fetched {fetched_count} RSS items, but insert failed: {errors[0]}",
        }

    return {
        "fetched": fetched_count,
        "published": published_count,
        "message": f"Fetched {fetched_count} RSS items and published {published_count} consolidated briefings.",
    }

    # Explicitly discard temporary source text immediately after processing
    raw_items.clear()
    clusters.clear()

    return {
        "fetched": fetched_count,
        "published": published_count,
        "message": f"Fetched {fetched_count} RSS items and published {published_count} consolidated briefings.",
    }
