import json
import re
from datetime import datetime, timedelta
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

GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

APPROVED_GENRES = [
    "Politics & Governance",
    "Education",
    "Science & Technology",
    "Business & Economy",
    "Health",
    "Sports",
    "Entertainment",
    "Environment & Climate",
    "Crime & Law",
    "Agriculture & Rural Affairs",
    "Career & Employment",
    "Culture & Literature",
]

ALLOWED_GEOGRAPHIES = {"State", "National", "International"}


def _clean_text(raw: str) -> str:
    """Strips HTML tags and excess whitespace from RSS snippets."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", text).strip()


def _extract_json_object(raw_text: str) -> dict:
    """Extracts and parses the first valid JSON object from LLM text output."""
    cleaned = re.sub(r"^```json|```$", "", (raw_text or "").strip()).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return json.loads(match.group(0))


def _normalize_geography(raw_geo: str | None, fallback: str = "National") -> str:
    """Maps geography strictly onto ['State', 'National', 'International'] to satisfy stories_geography_check."""
    val = (raw_geo or "").strip().lower()
    if any(k in val for k in ("state", "bengal", "kolkata", "regional", "provincial")):
        return "State"
    if any(k in val for k in ("internat", "world", "global", "foreign", "usa", "uk", "china", "un")):
        return "International"
    if any(k in val for k in ("national", "india", "domestic", "central")):
        return "National"
    fb_clean = (fallback or "").strip().title()
    return fb_clean if fb_clean in ALLOWED_GEOGRAPHIES else "National"


def _normalize_genre(raw_genre: str | None) -> str:
    """Enforces classification strictly within the 12 approved DPR genres."""
    cleaned = (raw_genre or "").strip()
    for allowed in APPROVED_GENRES:
        if cleaned.lower() == allowed.lower():
            return allowed

    low = cleaned.lower()
    if any(w in low for w in ("politic", "govern", "elect", "parliament", "minister", "policy")):
        return "Politics & Governance"
    if any(w in low for w in ("educat", "school", "college", "university", "exam", "student")):
        return "Education"
    if any(w in low for w in ("scien", "tech", "space", "isro", "ai", "cyber", "digital")):
        return "Science & Technology"
    if any(w in low for w in ("busin", "econom", "market", "bank", "finance", "trade", "tax")):
        return "Business & Economy"
    if any(w in low for w in ("health", "medic", "hospital", "disease", "doctor", "who")):
        return "Health"
    if any(w in low for w in ("sport", "cricket", "football", "olympic", "match", "tournament")):
        return "Sports"
    if any(w in low for w in ("entertain", "film", "cinema", "movie", "music", "actor")):
        return "Entertainment"
    if any(w in low for w in ("environ", "climat", "weather", "cyclone", "flood", "rain", "pollution")):
        return "Environment & Climate"
    if any(w in low for w in ("crime", "law", "court", "police", "arrest", "supreme court", "high court")):
        return "Crime & Law"
    if any(w in low for w in ("agricult", "farm", "rural", "crop", "monsoon", "kisan")):
        return "Agriculture & Rural Affairs"
    if any(w in low for w in ("career", "employ", "job", "recruit", "hiring", "vacancy")):
        return "Career & Employment"
    if any(w in low for w in ("cultur", "literat", "book", "festival", "heritage", "art")):
        return "Culture & Literature"

    return "Politics & Governance"


def _has_bengali_script(text: str) -> bool:
    """Verifies that text uses genuine Bengali Unicode characters (U+0980..U+09FF)."""
    return bool(re.search(r"[\u0980-\u09FF]{4,}", text or ""))


def _get_existing_urls_and_headlines(supabase) -> tuple[set[str], set[str]]:
    """Fetches recently published article URLs and normalized headlines to prevent duplicates."""
    existing_urls: set[str] = set()
    existing_headlines: set[str] = set()
    cutoff_iso = (datetime.now(IST) - timedelta(days=3)).isoformat()

    try:
        refs_res = (
            supabase.table("story_references")
            .select("article_url")
            .gte("created_at", cutoff_iso)
            .execute()
        )
        for row in refs_res.data or []:
            if row.get("article_url"):
                existing_urls.add(row["article_url"].strip())
    except Exception:
        pass

    try:
        stories_res = (
            supabase.table("stories")
            .select("headline_en")
            .gte("published_at", cutoff_iso)
            .execute()
        )
        for row in stories_res.data or []:
            if row.get("headline_en"):
                norm = re.sub(r"[^a-z0-9]+", " ", row["headline_en"].lower()).strip()
                existing_headlines.add(norm)
    except Exception:
        pass

    return existing_urls, existing_headlines


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
                    snippet = _clean_text(entry.get("summary") or entry.get("description") or "")[:500]
                    if title and link:
                        collected.append(
                            {
                                "source_id": source["id"],
                                "source_name": source["name"],
                                "language": source["language"],
                                "geography": _normalize_geography(source.get("default_geography"), "National"),
                                "title": title,
                                "snippet": snippet,
                                "url": link,
                                "published": entry.get("published", ""),
                            }
                        )
            except Exception:
                continue
    return collected


def cluster_items(items: list[dict], max_clusters: int = 20) -> list[list[dict]]:
    """Groups articles covering the same specific event across distinct newspapers."""
    clusters: list[list[dict]] = []
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this", "into",
        "over", "after", "amid", "says", "new", "india", "news", "will",
        "credit", "card", "bank", "report", "state", "govt", "government",
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
            if tokens and ref_tokens and len(tokens & ref_tokens) >= 3:
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
    genres_list = json.dumps(APPROVED_GENRES)
    return (
        "You are a senior bilingual news editor for Cruxly. Synthesize the following news notes "
        "into an original, objective, consolidated abridged report in BOTH English and standard Bengali (বাংলা লিপি).\n"
        "CRITICAL RULES:\n"
        "1. 'headline_bn' and 'in_brief_bn' MUST be written strictly in Bengali Unicode script (বাংলা বর্ণমালা). "
        "NEVER use Hindi (Devanagari) or Punjabi (Gurmukhi) script.\n"
        "2. 'geography' MUST be strictly one of: [\"State\", \"National\", \"International\"]. Use \"State\" for Indian state-level news, \"National\" for India-wide news, and \"International\" for global/foreign news.\n"
        f"3. 'primary_genre' MUST be strictly one of the 12 approved genres: {genres_list}.\n"
        "4. Combine all facts and context into a single cohesive paragraph for 'in_brief_en' (3-5 sentences) and 'in_brief_bn' (3-5 sentences). Do NOT copy sentences verbatim.\n\n"
        "Respond ONLY with a raw JSON object containing EXACTLY these 6 keys:\n"
        '- "headline_en": Concise, factual English headline (max 15 words).\n'
        '- "headline_bn": Natural, accurate Bengali headline in Bengali Unicode script.\n'
        '- "primary_genre": Exact string from the 12 approved genres above.\n'
        '- "geography": Exact string from ["State", "National", "International"].\n'
        '- "in_brief_en": Unified 3-5 sentence objective English summary covering what happened and key context.\n'
        '- "in_brief_bn": Unified 3-5 sentence objective Bengali summary in Bengali Unicode script only.\n\n'
        f"Source Notes:\n{source_notes}"
    )


def synthesize_cluster(
    cluster: list[dict],
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
) -> tuple[dict, str | None]:
    """
    Generates an original consolidated abridged summary in English and Bengali.
    Enforces strict DPR geography ['State', 'National', 'International'], 12 approved genres,
    Bengali headlines, and Bengali Unicode script validation.
    """
    primary = cluster[0]
    source_names = sorted({item["source_name"] for item in cluster})
    fallback_geo = _normalize_geography(primary.get("geography"), "National")
    prompt = _build_synthesis_prompt(cluster)
    llm_error = None

    def _finalize_parsed(parsed: dict) -> dict:
        geo = _normalize_geography(parsed.get("geography"), fallback_geo)
        genre = _normalize_genre(parsed.get("primary_genre"))
        headline_en = (parsed.get("headline_en") or primary["title"]).strip()
        headline_bn = (parsed.get("headline_bn") or "").strip()
        in_brief_en = (parsed.get("in_brief_en") or parsed.get("what_happened_en") or primary["snippet"] or primary["title"]).strip()
        in_brief_bn = (parsed.get("in_brief_bn") or parsed.get("what_happened_bn") or "").strip()

        if not _has_bengali_script(headline_bn):
            headline_bn = f"সংবাদ শিরোনাম ({', '.join(source_names)})"
        if not _has_bengali_script(in_brief_bn):
            in_brief_bn = f"সূত্র: {', '.join(source_names)} — {headline_en}"

        return {
            "headline_en": headline_en,
            "primary_genre": genre,
            "geography": geo,
            "summary_en": {
                "in_brief": in_brief_en,
                "sources": source_names,
            },
            "summary_bn": {
                "headline_bn": headline_bn,
                "in_brief": in_brief_bn,
            },
        }

    # 1. Try Groq reasoning models
    if groq_api_key and Groq is not None:
        g_client = Groq(api_key=groq_api_key.strip())
        for model_id in GROQ_MODELS:
            try:
                chat_resp = g_client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise bilingual news editor. Output valid JSON only. "
                                "Write Bengali headlines and summaries strictly in Bengali Unicode script (বাংলা)."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    reasoning_effort="low",
                    temperature=0.2,
                    max_tokens=4096,
                )
                content = chat_resp.choices[0].message.content or ""
                parsed = _extract_json_object(content)
                return _finalize_parsed(parsed), None
            except Exception as g_exc:
                llm_error = f"Groq ({model_id}) error: {g_exc}"

    # 2. Try Gemini if configured
    if gemini_api_key and genai is not None:
        try:
            client = genai.Client(api_key=gemini_api_key.strip())
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            parsed = _extract_json_object(resp.text or "")
            return _finalize_parsed(parsed), None
        except Exception as gem_exc:
            llm_error = f"Gemini API error: {gem_exc}"

    # 3. Fallback when LLM is unavailable or errored
    combined_brief = primary["snippet"] or primary["title"]
    return (
        {
            "headline_en": primary["title"],
            "primary_genre": _normalize_genre(primary["title"]),
            "geography": fallback_geo,
            "summary_en": {
                "in_brief": f"{combined_brief} (Corroborated across {', '.join(source_names)}.)",
                "sources": source_names,
            },
            "summary_bn": {
                "headline_bn": f"সংবাদ শিরোনাম ({', '.join(source_names)})",
                "in_brief": f"সূত্র: {', '.join(source_names)} — {primary['title']}",
            },
        },
        llm_error,
    )


def run_ingestion_cycle(
    supabase,
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
) -> dict:
    """Executes one full collect -> deduplicate -> cluster -> synthesize -> publish cycle."""
    raw_items = fetch_rss_items(max_per_feed=8)
    fetched_count = len(raw_items)
    if not raw_items:
        return {"fetched": 0, "published": 0, "message": "No RSS entries reachable right now."}

    existing_urls, existing_headlines = _get_existing_urls_and_headlines(supabase)

    fresh_items = [it for it in raw_items if it["url"] not in existing_urls]
    if not fresh_items:
        raw_items.clear()
        return {
            "fetched": fetched_count,
            "published": 0,
            "message": f"Fetched {fetched_count} RSS items; all were already published in recent cycles.",
        }

    clusters = cluster_items(fresh_items, max_clusters=20)
    published_count = 0
    skipped_dups = 0
    errors: list[str] = []
    now_ist_iso = datetime.now(IST).isoformat()

    for cluster in clusters:
        norm_primary = re.sub(r"[^a-z0-9]+", " ", cluster[0]["title"].lower()).strip()
        if norm_primary in existing_headlines:
            skipped_dups += 1
            continue

        synthesized, llm_err = synthesize_cluster(
            cluster,
            gemini_api_key=gemini_api_key,
            groq_api_key=groq_api_key,
        )
        if llm_err and llm_err not in errors:
            errors.append(llm_err)

        norm_synth = re.sub(r"[^a-z0-9]+", " ", synthesized["headline_en"].lower()).strip()
        if norm_synth in existing_headlines:
            skipped_dups += 1
            continue

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
                existing_headlines.add(norm_synth)
                refs = [
                    {
                        "story_id": story_id,
                        "source_name": item["source_name"],
                        "article_url": item["url"],
                        "hindi_original_headline": item["title"] if item["language"] == "hi" else None,
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

    raw_items.clear()
    fresh_items.clear()
    clusters.clear()

    diag_suffix = f" (Diagnostic: {errors[0]})" if errors else ""
    return {
        "fetched": fetched_count,
        "published": published_count,
        "message": (
            f"Fetched {fetched_count} RSS items, skipped {skipped_dups} duplicates, "
            f"and published {published_count} consolidated briefings.{diag_suffix}"
        ),
    }
