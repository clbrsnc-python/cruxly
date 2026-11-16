import json
import re
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
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

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
except Exception:
    sanscript = None
    transliterate = None

IST = pytz.timezone("Asia/Kolkata")

PRIMARY_MODEL = "openai/gpt-oss-120b"
BACKUP_MODEL = "openai/gpt-oss-20b"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

DEFAULT_DPR_GENRES = [
    {"name_en": "Politics & Governance", "name_bn": "রাজনীতি ও প্রশাসন"},
    {"name_en": "Education", "name_bn": "শিক্ষা"},
    {"name_en": "Science & Technology", "name_bn": "বিজ্ঞান ও প্রযুক্তি"},
    {"name_en": "Business & Economy", "name_bn": "ব্যবসা ও অর্থনীতি"},
    {"name_en": "Health", "name_bn": "স্বাস্থ্য"},
    {"name_en": "Sports", "name_bn": "খেলাধুলা"},
    {"name_en": "Entertainment", "name_bn": "বিনোদন"},
    {"name_en": "Environment & Climate", "name_bn": "পরিবেশ ও জলবায়ু"},
    {"name_en": "Crime & Law", "name_bn": "অপরাধ ও আইন"},
    {"name_en": "Agriculture & Rural Affairs", "name_bn": "কৃষি ও গ্রামীণ বিষয়"},
    {"name_en": "Career & Employment", "name_bn": "কর্মসংস্থান ও পেশা"},
    {"name_en": "Culture & Literature", "name_bn": "সংস্কৃতি ও সাহিত্য"},
]

APPROVED_GENRES = [g["name_en"] for g in DEFAULT_DPR_GENRES]

ALLOWED_GEOGRAPHIES = ("State", "National", "International")
ALLOWED_EDITION_SLOTS = ("morning", "evening", "live")

ASTROLOGY_PATTERNS = re.compile(
    r"("
    r"\bhoroscope\b|\bastrology\b|\bzodiac\b|\btarot\b|\bpanchang\b|\brashifal\b|"
    r"\baries\b|\btaurus\b|\bgemini\b|\bscorpio\b|\bsagittarius\b|\bcapricorn\b|\baquarius\b|\bpisces\b|"
    r"/astrology/|/horoscope/|/rashifal/|"
    r"রাশিফল|আজকের রাশিফল|দৈনিক রাশিফল|জ্যোতিষ|পঞ্জিকা|ভাগ্যফল|"
    r"মেষ রাশি|বৃষ রাশি|মিথুন রাশি|কর্কট রাশি|সিংহ রাশি|কন্যা রাশি|তুলা রাশি|বৃশ্চিক রাশি|ধনু রাশি|মকর রাশি|কুম্ভ রাশি|মীন রাশি|"
    r"राशिफल|आज का राशिफल|ज्योतिष|पंचांग|टैरो"
    r")",
    flags=re.IGNORECASE,
)

# Cross-language entity canonicalization map (Bengali / Hindi -> canonical English concept token)
CROSS_LANG_ENTITY_MAP: dict[str, str] = {
    # Cities, States & Countries
    "কলকাতা": "kolkata", "कोलकाता": "kolkata", "calcutta": "kolkata",
    "পশ্চিমবঙ্গ": "bengal", "বাংলা": "bengal", "बंगाल": "bengal", "west bengal": "bengal",
    "দিল্লি": "delhi", "दिल्ली": "delhi", "new delhi": "delhi",
    "মুম্বই": "mumbai", "मुंबई": "mumbai",
    "চেন্নাই": "chennai", "चेन्नई": "chennai",
    "বেঙ্গালুরু": "bengaluru", "बेंगलुरु": "bengaluru", "bangalore": "bengaluru",
    "হায়দরাবাদ": "hyderabad", "हैदराबाद": "hyderabad",
    "ভারত": "india", "भारत": "india",
    "বাংলাদেশ": "bangladesh", "बांग्लादेश": "bangladesh",
    "পাকিস্তান": "pakistan", "पाकिस्तान": "pakistan",
    "চীন": "china", "चीन": "china",
    "আমেরিকা": "usa", "মার্কিন": "usa", "अमेरिका": "usa", "united states": "usa",
    "ইজরায়েল": "israel", "ইসরায়েল": "israel", "इजरायल": "israel",
    "গাজা": "gaza", "गाजा": "gaza",
    "রোহিঙ্গা": "rohingya", "রোহিঙ্গাদের": "rohingya", "रोहिंग्या": "rohingya",
    "মায়ানমার": "myanmar", "মিয়ানমার": "myanmar", "म्यांमार": "myanmar",
    "যাদবপুর": "jadavpur", "সল্টলেক": "saltlake", "হাওড়া": "howrah", "শিলিগুড়ি": "siliguri",
    "দার্জিলিং": "darjeeling", "মালদা": "malda", "মুর্শিদাবাদ": "murshidabad", "বীরভূম": "birbhum",
    "নন্দীগ্রাম": "nandigram", "সন্দেশখালি": "sandeshkhali", "আরজি কর": "rgkar",
    # Institutions & Governance
    "সুপ্রিম কোর্ট": "supremecourt", "सुप्रीम कोर्ट": "supremecourt", "supreme court": "supremecourt",
    "হাইকোর্ট": "highcourt", "हाईकोर्ट": "highcourt", "high court": "highcourt",
    "আন্তর্জাতিক আদালত": "icj", "icj": "icj",
    "নির্বাচন কমিশন": "electioncommission", "चुनाव आयोग": "electioncommission", "election commission": "electioncommission",
    "সংসদ": "parliament", "संसद": "parliament",
    "লোকসভা": "loksabha", "लोकसभा": "loksabha",
    "বিধানসভা": "assembly", "विधानसभा": "assembly",
    "নবান্ন": "nabanna", "রাজভবন": "rajbhavan",
    "পুলিশ": "police", "पुलिस": "police",
    "সিবিআই": "cbi", "ইডি": "ed", "এনআইএ": "nia",
    "এসআইআর": "sir", "ভোটার": "voter", "আধার": "aadhaar", "आधार": "aadhaar",
    "রেল": "railway", "रेलवे": "railway", "মেট্রো": "metro", "বিমান": "flight",
    "আরবিআই": "rbi", "সেবি": "sebi", "ইসরো": "isro", "নাসা": "nasa",
    # Political Leaders & Parties
    "মোদী": "modi", "মোদি": "modi", "मोदी": "modi",
    "মমতা": "mamata", "ममता": "mamata",
    "অভিষেক": "abhishek", "শুভেন্দু": "suvendu",
    "অমিত শাহ": "amitshah", "রাহুল": "rahul", "ট্রাম্প": "trump",
    "তৃণমূল": "tmc", "বিজেপি": "bjp", "কংগ্রেস": "congress", "সিপিএম": "cpim",
    # Major Recurring Themes
    "দূষণ": "pollution", "প্রদূষণ": "pollution", "प्रदूषण": "pollution",
    "ঘূর্ণিঝড়": "cyclone", "বৃষ্টি": "rain", "বন্যা": "flood", "ভূমিকম্প": "earthquake",
    "দুর্ঘটনা": "accident", "অগ্নিকাণ্ড": "fire", "বিস্ফোরণ": "blast",
    "গ্রেফতার": "arrest", "খুন": "murder", "ধর্ষণ": "rape",
    "পরীক্ষা": "exam", "নিয়োগ": "recruitment", "ধর্মঘট": "strike",
    "ক্রিকেট": "cricket", "ফুটবল": "football", "আইপিএল": "ipl", "মোহনবাগান": "mohunbagan", "ইস্টবেঙ্গল": "eastbengal",
}

BN_TO_ASCII_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯०१२३४५६७८९", "01234567890123456789")


def _is_astrology_item(title: str, snippet: str = "", url: str = "") -> bool:
    """Deterministically excludes horoscope, rashifal, zodiac, and astrology items across EN/BN/HI."""
    combined = f"{title} {snippet} {url}"
    return bool(ASTROLOGY_PATTERNS.search(combined))


def fetch_approved_genres(supabase) -> list[dict]:
    """Fetches active approved genres from public.genres, falling back to the 12 default DPR genres."""
    try:
        res = (
            supabase.table("genres")
            .select("id, name_en, name_bn, is_active")
            .eq("is_active", True)
            .order("id")
            .execute()
        )
        rows = res.data or []
        if rows:
            return rows
    except Exception:
        pass
    return [
        {"id": idx + 1, "name_en": g["name_en"], "name_bn": g["name_bn"], "is_active": True}
        for idx, g in enumerate(DEFAULT_DPR_GENRES)
    ]


def _clean_text(raw: str) -> str:
    """Strips HTML tags, trailing publisher suffixes from Google News titles, and excess whitespace."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"\s+[\-\u2013\u2014]\s+(?:Anandabazar Patrika|Bartaman|Aajkaal|Sangbad Pratidin|Ei Samay|The Telegraph|The Hindu|The Indian Express|Times of India|Hindustan Times|NDTV).*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    return text


def _normalize_publisher_key(source_name: str) -> str:
    """Normalizes publisher names so regional sub-feeds of the same newspaper do not count as separate outlets."""
    clean = re.sub(
        r"\s*[-–—|:]\s*(kolkata|delhi|mumbai|national|bengal|editorial|opinion|live|states|cities).*$",
        "",
        (source_name or "").strip(),
        flags=re.IGNORECASE,
    )
    return clean.strip().lower()


def _parse_entry_datetime_ist(entry) -> datetime | None:
    """Parses RSS entry publication date into IST timezone-aware datetime."""
    if getattr(entry, "published_parsed", None):
        try:
            ts = time.mktime(entry.published_parsed)
            return datetime.fromtimestamp(ts, tz=pytz.UTC).astimezone(IST)
        except Exception:
            pass
    raw_date = entry.get("published") or entry.get("updated") or ""
    if raw_date:
        try:
            dt = parsedate_to_datetime(raw_date)
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            return dt.astimezone(IST)
        except Exception:
            pass
    return None


def _resolve_cluster_published_at(cluster: list[dict], now_ist: datetime) -> str:
    """
    Preserves the authentic source publication timestamp when available
    in the cluster entries, clamped to <= now_ist.
    """
    valid_dts: list[datetime] = []
    for item in cluster:
        dt = item.get("published_dt")
        if isinstance(dt, datetime):
            clamped = dt if dt <= now_ist else now_ist
            valid_dts.append(clamped)
    if valid_dts:
        return min(valid_dts).isoformat()
    return now_ist.isoformat()


def _extract_named_entities(cluster: list[dict]) -> tuple[list[str], list[str]]:
    """
    Algorithmically extracts Proper Nouns and ALL-CAPS Acronyms from English source headlines
    so the Bengali editor transliterates them accurately without literal word-for-word translation.
    """
    acronyms: set[str] = set()
    proper_nouns: set[str] = set()
    ignore_caps = {
        "THE", "AND", "FOR", "WITH", "FROM", "INTO", "OVER", "AFTER",
        "AMID", "SAYS", "NEW", "WILL", "HOW", "WHY", "WHAT",
    }

    for item in cluster:
        if item.get("language") != "en":
            continue
        title = item.get("title") or ""
        for acr in re.findall(r"\b[A-Z]{2,6}\b", title):
            if acr not in ignore_caps:
                acronyms.add(acr)
        for match in re.findall(r"\b(?:[A-Z][a-z]{2,}\s+){1,3}[A-Z][a-z]{2,}\b", title):
            proper_nouns.add(match.strip())

    return sorted(acronyms), sorted(proper_nouns)


def _apply_universal_bengali_morphology(text: str) -> str:
    """
    Applies purely structural, algorithmic Bengali grammar & typography rules:
      1. Fixes Hindi '-varshiya' age calques across ALL Unicode hyphen/dash variants (\u2010-\u2015)
      2. Moves Bengali case suffixes trapped outside closing quotation marks back inside
    """
    if not text:
        return text

    bn_num_words = (
        "এক|দুই|তিন|চার|পাঁচ|ছয়|সাত|আট|নয়|দশ|"
        "এগারো|বারো|তেরো|চোদ্দ|পনেরো|ষোলো|সতেরো|আঠারো|উনিশ|বিশ|"
        "একুশ|বাইশ|তেইশ|চব্বিশ|পঁচিশ|ছাব্বিশ|সাতাশ|আঠাশ|ঊনত্রিশ|ত্রিশ|"
        "পঁয়ত্রিশ|চল্লিশ|পঁয়তাল্লিশ|পঞ্চাশ|ষাট|সত্তর|আশি|নব্বই"
    )
    text = re.sub(
        rf"([০-৯0-9]+|{bn_num_words})[\s\-\u2010-\u2015]*বছরীয়?[াীের]*",
        r"\1 বছর বয়সী",
        text,
    )
    text = re.sub(r"([‘’'\"])([েয়কেতর])", r"\2\1", text)
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
    if any(k in val for k in ("state", "bengal", "kolkata", "regional", "provincial", "maharashtra", "delhi", "tamil", "kerala", "karnataka", "odisha", "bihar", "assam", "punjab", "rajasthan", "gujarat", "uttar")):
        return "State"
    if any(k in val for k in ("internat", "world", "global", "foreign", "usa", "uk", "china", "un", "asean", "gaza", "myanmar", "europe", "russia", "uae", "emirates")):
        return "International"
    if any(k in val for k in ("national", "india", "domestic", "central")):
        return "National"
    fb_clean = (fallback or "").strip().title()
    return fb_clean if fb_clean in ALLOWED_GEOGRAPHIES else "National"


def _normalize_genre(raw_genre: str | None, allowed_names: list[str] | None = None) -> str:
    """Enforces classification strictly within currently active approved DPR genres."""
    valid_genres = allowed_names or APPROVED_GENRES
    cleaned = (raw_genre or "").strip()
    for allowed in valid_genres:
        if cleaned.lower() == allowed.lower():
            return allowed

    low = cleaned.lower()
    mapped = "Politics & Governance"
    if any(w in low for w in ("educat", "school", "college", "university", "exam", "student", "ugc", "jee", "neet")):
        mapped = "Education"
    elif any(w in low for w in ("scien", "tech", "space", "isro", "ai", "cyber", "digital", "software")):
        mapped = "Science & Technology"
    elif any(w in low for w in ("busin", "econom", "market", "bank", "finance", "trade", "tax", "rbi", "gdp")):
        mapped = "Business & Economy"
    elif any(w in low for w in ("health", "medic", "hospital", "disease", "doctor", "who", "respiratory")):
        mapped = "Health"
    elif any(w in low for w in ("sport", "cricket", "football", "olympic", "match", "tournament")):
        mapped = "Sports"
    elif any(w in low for w in ("entertain", "film", "cinema", "movie", "music", "actor")):
        mapped = "Entertainment"
    elif any(w in low for w in ("environ", "climat", "weather", "cyclone", "flood", "rain", "pollution", "imd")):
        mapped = "Environment & Climate"
    elif any(w in low for w in ("crime", "law", "court", "police", "arrest", "supreme court", "high court", "blast")):
        mapped = "Crime & Law"
    elif any(w in low for w in ("agricult", "farm", "rural", "crop", "monsoon", "kisan")):
        mapped = "Agriculture & Rural Affairs"
    elif any(w in low for w in ("career", "employ", "job", "recruit", "hiring", "vacancy")):
        mapped = "Career & Employment"
    elif any(w in low for w in ("cultur", "literat", "book", "festival", "heritage", "art")):
        mapped = "Culture & Literature"

    if mapped in valid_genres:
        return mapped
    return valid_genres[0] if valid_genres else "Politics & Governance"


def _normalize_secondary_genres(raw_list: list | None, primary: str, allowed_names: list[str]) -> list[str]:
    """Returns valid optional secondary DPR genres distinct from primary_genre."""
    if not isinstance(raw_list, list):
        return []
    result: list[str] = []
    for item in raw_list:
        g = _normalize_genre(str(item), allowed_names)
        if g != primary and g not in result:
            result.append(g)
    return result[:2]


def _detect_sensitive_status(headline_en: str, in_brief_en: str, is_sensitive_flag: bool = False) -> str:
    """Applies DPR Sensitive News Safeguard for unverified communal/graphic reports."""
    if is_sensitive_flag:
        return "flagged_review"
    combined = f"{headline_en} {in_brief_en}".lower()
    high_risk_patterns = (
        r"\bcommunal riot\b",
        r"\bmob lynch",
        r"\bsexual assault of minor\b",
        r"\bminor raped\b",
    )
    if any(re.search(pat, combined) for pat in high_risk_patterns):
        return "flagged_review"
    return "published"


def _has_bengali_script(text: str) -> bool:
    """Verifies that text uses genuine Bengali Unicode characters (U+0980..U+09FF)."""
    return bool(re.search(r"[\u0980-\u09FF]{4,}", text or ""))


def _is_verbatim_or_close_copy(candidate: str, source_titles: list[str]) -> bool:
    """
    Strictly rejects headlines that copy or lightly paraphrase any source newspaper title.
    Flags overlap >= 55% of non-trivial content words.
    """
    stop = {"the", "and", "for", "with", "from", "into", "over", "after", "amid", "says", "said", "on", "in", "to", "of", "as", "at", "by"}
    cand_words = [w for w in re.findall(r"[a-z0-9]+", (candidate or "").lower()) if w not in stop and len(w) > 2]
    if not cand_words:
        return True
    cand_set = set(cand_words)
    for src in source_titles:
        src_words = [w for w in re.findall(r"[a-z0-9]+", (src or "").lower()) if w not in stop and len(w) > 2]
        if not src_words:
            continue
        if cand_words == src_words:
            return True
        overlap_ratio = len(cand_set & set(src_words)) / max(1, min(len(cand_set), len(src_words)))
        if overlap_ratio >= 0.55:
            return True
    return False


def _build_non_verbatim_fallback_headline(primary: dict, genre: str, geo: str) -> str:
    """Constructs a clean editorial briefing title without copying a newspaper's headline verbatim."""
    acronyms, proper_nouns = _extract_named_entities([primary])
    subject = proper_nouns[0] if proper_nouns else (acronyms[0] if acronyms else geo)
    return f"{genre} Briefing: Key Developments Involving {subject}"


def _get_existing_urls_and_headlines(supabase) -> tuple[set[str], set[str]]:
    """Fetches recently published article URLs and normalized headlines to prevent duplicates."""
    existing_urls: set[str] = set()
    existing_headlines: set[str] = set()
    cutoff_iso = (datetime.now(IST) - timedelta(days=7)).isoformat()

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


def fetch_rss_items(
    max_per_feed: int = 10,
    since_dt_ist: datetime | None = None,
) -> tuple[list[dict], int]:
    """
    Collects latest headlines, short descriptions, and direct links across English, Bengali, and Hindi sources,
    excluding astrology/horoscope items and optionally filtering to entries published on or after since_dt_ist.
    """
    collected = []
    astrology_skipped = 0

    for source in get_active_sources():
        for rss_url in source.get("rss_urls", []):
            try:
                parsed = feedparser.parse(rss_url, agent=USER_AGENT)
                for entry in parsed.entries[:max_per_feed]:
                    title = _clean_text(entry.get("title", ""))
                    link = (entry.get("link") or "").strip()
                    snippet = _clean_text(entry.get("summary") or entry.get("description") or "")[:500]
                    if not title or not link:
                        continue

                    if _is_astrology_item(title, snippet, link):
                        astrology_skipped += 1
                        continue

                    entry_dt = _parse_entry_datetime_ist(entry)
                    if since_dt_ist is not None and entry_dt is not None and entry_dt < since_dt_ist:
                        continue

                    collected.append(
                        {
                            "source_id": source["id"],
                            "source_name": source["name"],
                            "publisher_key": _normalize_publisher_key(source["name"]),
                            "language": source["language"],
                            "geography": _normalize_geography(source.get("default_geography"), "National"),
                            "title": title,
                            "snippet": snippet,
                            "url": link,
                            "published": entry_dt.isoformat() if entry_dt else entry.get("published", ""),
                            "published_dt": entry_dt,
                        }
                    )
            except Exception:
                continue
    return collected, astrology_skipped


def cluster_items(items: list[dict], max_clusters: int | None = 20) -> list[list[dict]]:
    """
    Groups matching stories across distinct English, Bengali, and Hindi newspapers using
    cross-language entity canonicalization, proper-noun matching, and publish-window proximity.
    """
    clusters: list[list[dict]] = []
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this", "into",
        "over", "after", "amid", "says", "said", "new", "india", "news", "will",
        "credit", "card", "bank", "report", "reports", "state", "govt", "government",
        "more", "case", "court", "year", "years", "people", "during", "against",
        "এবং", "করে", "হয়েছে", "থেকে", "জন্য", "নিয়ে", "বলেছেন", "রাজ্য", "খবর", "আরও",
    }

    def tokenize(text: str) -> set[str]:
        normalized = text.translate(BN_TO_ASCII_DIGITS).lower()
        for phrase, canon in CROSS_LANG_ENTITY_MAP.items():
            if phrase in normalized:
                normalized = normalized.replace(phrase, f" {canon} ")

        canonical_tokens: set[str] = set()
        en_words = re.findall(r"[a-zA-Z]{3,}", normalized)
        indic_words = re.findall(r"[\u0980-\u09FF\u0900-\u097F]{2,}", normalized)
        numbers = re.findall(r"\b\d{2,}\b", normalized)

        for w in en_words + indic_words:
            if w not in stop_words:
                canonical_tokens.add(CROSS_LANG_ENTITY_MAP.get(w, w))
        for num in numbers:
            canonical_tokens.add(f"num_{num}")

        return canonical_tokens

    item_tokens = [tokenize(f"{it['title']} {it.get('snippet', '')[:220]}") for it in items]

    for idx, item in enumerate(items):
        tokens = item_tokens[idx]
        item_pub_key = item.get("publisher_key") or _normalize_publisher_key(item["source_name"])
        item_dt = item.get("published_dt")
        placed = False

        for cluster in clusters:
            existing_publishers = {
                c.get("publisher_key") or _normalize_publisher_key(c["source_name"])
                for c in cluster
            }
            if item_pub_key in existing_publishers:
                continue

            cluster_dts = [c["published_dt"] for c in cluster if isinstance(c.get("published_dt"), datetime)]
            if isinstance(item_dt, datetime) and cluster_dts:
                if abs((item_dt - cluster_dts[0]).total_seconds()) > 36 * 3600:
                    continue

            cluster_tokens: set[str] = set()
            for member in cluster:
                cluster_tokens |= member["_tokens"]

            overlap = tokens & cluster_tokens
            union_size = max(1, len(tokens | cluster_tokens))
            jaccard = len(overlap) / union_size

            if len(overlap) >= 2 or (len(overlap) >= 1 and jaccard >= 0.18):
                item["_tokens"] = tokens
                cluster.append(item)
                placed = True
                break

        if not placed:
            item["_tokens"] = tokens
            clusters.append([item])

    for cluster in clusters:
        for member in cluster:
            member.pop("_tokens", None)

    bn_clusters = [c for c in clusters if any(it["language"] == "bn" for it in c)]
    other_clusters = [c for c in clusters if not any(it["language"] == "bn" for it in c)]

    bn_clusters.sort(key=lambda c: len(c), reverse=True)
    other_clusters.sort(key=lambda c: len(c), reverse=True)

    if max_clusters is None:
        merged: list[list[dict]] = []
        max_len = max(len(bn_clusters), len(other_clusters))
        for i in range(max_len):
            if i < len(bn_clusters):
                merged.append(bn_clusters[i])
            if i < len(other_clusters):
                merged.append(other_clusters[i])
        return merged

    bn_quota = min(len(bn_clusters), max_clusters // 2)
    selected = bn_clusters[:bn_quota] + other_clusters[: max_clusters - bn_quota]
    if len(selected) < max_clusters:
        remaining_bn = bn_clusters[bn_quota : bn_quota + (max_clusters - len(selected))]
        selected.extend(remaining_bn)

    return selected[:max_clusters]


def _build_synthesis_prompt(cluster: list[dict], valid_genres: list[str]) -> str:
    has_bn_source = any(it["language"] == "bn" for it in cluster)
    acronyms, proper_nouns = _extract_named_entities(cluster)
    source_notes = "\n".join(
        f"- [{it['source_name']} ({it['language']})]: {it['title']} — {it['snippet']}"
        for it in cluster
    )
    genres_list = json.dumps(valid_genres)
    bn_guidance = (
        "Original Bengali newspaper notes are provided above—synthesize directly from the authentic Bengali reporting rather than translating from English."
        if has_bn_source
        else "Write natural, idiomatic West Bengal / Kolkata standard Bengali (পশ্চিমবঙ্গ বাংলা আকাদেমি ও কলকাতার সংবাদপত্রের মান্য চলিত রীতি), NOT Bangladeshi orthography and NOT literal English/Hindi calques."
    )
    entity_lock = ""
    if acronyms or proper_nouns:
        entity_lock = (
            f"Detected Source Acronyms: {acronyms} (transliterate letter-by-letter accurately into Bengali). "
            f"Detected Proper Nouns: {proper_nouns} (NEVER translate proper nouns/companies/places by dictionary meaning; transliterate using standard Indian Bengali spelling)."
        )

    return (
        "You are a senior copy editor at a major Kolkata broadsheet. Synthesize the following news notes "
        "into an original, objective, consolidated abridged report in BOTH English and standard Bengali (বাংলা লিপি).\n"
        "CRITICAL EDITORIAL & COPYRIGHT PRINCIPLES:\n"
        "1. ORIGINAL HEADLINE SYNTHESIS (STRICTLY MANDATORY): Write completely fresh, original editorial broadsheet headlines for 'headline_en' and 'headline_bn' using new sentence structure and vocabulary derived from the event facts. NEVER copy, mirror, or lightly reword any source headline.\n"
        f"2. {bn_guidance}\n"
        f"3. {entity_lock}\n"
        "4. Use West Bengal / Kolkata Bengali standard vocabulary and place orthography (Paschimbanga Bangla Akademi standard), never Hindi morphological calques (e.g., use 'বছর বয়সী', never 'বছরী'/'বছরীয়') and never Bangladeshi regional spellings.\n"
        "5. Preserve exact subject-object grammatical agency (who performed the action vs. who was named or affected).\n"
        "6. 'geography' MUST be strictly one of: [\"State\", \"National\", \"International\"].\n"
        "7. If 'geography' is \"State\", set 'state_name' to the Indian state name; otherwise set 'state_name' to null.\n"
        f"8. 'primary_genre' MUST be strictly one of the currently approved genres: {genres_list}.\n"
        "9. Set 'is_sensitive' to true ONLY if the story involves unverified communal violence, graphic abuse of minors, or sensitive public-order rumors requiring editorial review; otherwise false.\n"
        "10. Combine all facts and context into a single cohesive paragraph for 'in_brief_en' (3-5 sentences) and 'in_brief_bn' (3-5 sentences). Do NOT append '(Corroborated across...)' inside the text.\n\n"
        "Respond ONLY with a raw JSON object containing EXACTLY these keys:\n"
        '- "headline_en": Freshly synthesized, non-verbatim factual English broadsheet headline (max 14 words).\n'
        '- "headline_bn": Freshly synthesized, non-verbatim idiomatic Bengali broadsheet headline in Bengali Unicode script.\n'
        '- "primary_genre": Exact string from the currently approved genres above.\n'
        '- "secondary_genres": Array of 0 to 2 additional genres from the approved genres.\n'
        '- "geography": Exact string from ["State", "National", "International"].\n'
        '- "state_name": Indian state name if geography is "State", else null.\n'
        '- "is_sensitive": Boolean (true or false).\n'
        '- "in_brief_en": Unified 3-5 sentence objective English summary.\n'
        '- "in_brief_bn": Unified 3-5 sentence objective Bengali summary in standard Kolkata newspaper Bengali.\n\n'
        f"Source Notes:\n{source_notes}"
    )


def _automated_bengali_copy_edit(
    g_client,
    cluster: list[dict],
    headline_en: str,
    headline_bn: str,
    in_brief_en: str,
    in_brief_bn: str,
) -> tuple[str, str]:
    """Second-pass autonomous Bengali desk copy-editor audit using the 120B model."""
    acronyms, proper_nouns = _extract_named_entities(cluster)
    source_notes = "\n".join(
        f"- [{it['source_name']} ({it['language']})]: {it['title']}"
        for it in cluster
    )
    audit_prompt = (
        "You are the Chief Bengali Sub-Editor in Kolkata (Paschimbanga Bangla Akademi standard) auditing a draft before publication.\n"
        "Verify the Bengali draft against the Original Source Headlines and Detected Entities below, and fix ANY defect in:\n"
        f"1. Proper Noun & Acronym Integrity — Acronyms: {acronyms}, Proper Nouns: {proper_nouns}. "
        "Ensure every acronym is spelled phonetically right and NO proper noun/brand/place is mistranslated by literal word meaning.\n"
        "2. Original Headline Check — Ensure 'headline_bn' is an original editorial headline and not a verbatim copy of any Bengali source title.\n"
        "3. West Bengal Press Standard — Use Kolkata newspaper orthography and vocabulary (not Bangladeshi orthography and not Hindi calques like 'বছরী'/'বছরীয়').\n"
        "4. Grammatical Agency — Verify subject vs. object meaning matches the English source accurately.\n\n"
        f"Original Source Headlines:\n{source_notes}\n\n"
        f"English Headline: {headline_en}\n"
        f"English Summary: {in_brief_en}\n"
        f"Draft Bengali Headline: {headline_bn}\n"
        f"Draft Bengali Summary: {in_brief_bn}\n\n"
        "Respond ONLY with a raw JSON object with keys \"headline_bn\" and \"in_brief_bn\" containing the final publication-ready Bengali copy."
    )
    try:
        resp = g_client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are the Chief Bengali Sub-Editor in Kolkata. Return strictly valid JSON with publication-ready West Bengal standard Bengali.",
                },
                {"role": "user", "content": audit_prompt},
            ],
            reasoning_effort="low",
            temperature=0.1,
            max_tokens=2048,
        )
        edited = _extract_json_object(resp.choices[0].message.content or "")
        new_h_bn = (edited.get("headline_bn") or headline_bn).strip()
        new_b_bn = (edited.get("in_brief_bn") or in_brief_bn).strip()
        if _has_bengali_script(new_h_bn) and _has_bengali_script(new_b_bn):
            return new_h_bn, new_b_bn
    except Exception:
        pass
    return headline_bn, in_brief_bn


def synthesize_cluster(
    cluster: list[dict],
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
    valid_genres: list[str] | None = None,
) -> tuple[dict, str | None]:
    """Generates an original consolidated abridged summary and non-verbatim headlines in English and Bengali."""
    active_genres = valid_genres or APPROVED_GENRES
    primary = cluster[0]
    source_titles = [item["title"] for item in cluster]
    source_names = sorted({item["source_name"] for item in cluster})
    fallback_geo = _normalize_geography(primary.get("geography"), "National")
    prompt = _build_synthesis_prompt(cluster, active_genres)
    llm_error = None

    def _finalize_parsed(parsed: dict, g_client=None) -> dict:
        geo = _normalize_geography(parsed.get("geography"), fallback_geo)
        if geo not in ALLOWED_GEOGRAPHIES:
            geo = "National"
        genre = _normalize_genre(parsed.get("primary_genre"), active_genres)
        sec_genres = _normalize_secondary_genres(parsed.get("secondary_genres"), genre, active_genres)
        state_val = (parsed.get("state_name") or "").strip() if geo == "State" else None
        if geo == "State" and not state_val:
            state_val = "West Bengal"

        raw_h_en = (parsed.get("headline_en") or "").strip()
        if not raw_h_en or _is_verbatim_or_close_copy(raw_h_en, source_titles):
            headline_en = _build_non_verbatim_fallback_headline(primary, genre, geo)
        else:
            headline_en = raw_h_en

        headline_bn = (parsed.get("headline_bn") or "").strip()
        in_brief_en = (parsed.get("in_brief_en") or parsed.get("what_happened_en") or primary["snippet"] or headline_en).strip()
        in_brief_bn = (parsed.get("in_brief_bn") or parsed.get("what_happened_bn") or "").strip()

        if g_client is not None and _has_bengali_script(headline_bn):
            headline_bn, in_brief_bn = _automated_bengali_copy_edit(
                g_client=g_client,
                cluster=cluster,
                headline_en=headline_en,
                headline_bn=headline_bn,
                in_brief_en=in_brief_en,
                in_brief_bn=in_brief_bn,
            )

        headline_bn = _apply_universal_bengali_morphology(headline_bn)
        in_brief_bn = _apply_universal_bengali_morphology(in_brief_bn)

        if not _has_bengali_script(headline_bn) or headline_bn.strip() in source_titles:
            headline_bn = f"{genre} সংবাদ সংক্ষেপ ({', '.join(source_names)})"
        if not _has_bengali_script(in_brief_bn):
            in_brief_bn = f"সূত্র: {', '.join(source_names)} — {headline_en}"

        story_status = _detect_sensitive_status(
            headline_en,
            in_brief_en,
            bool(parsed.get("is_sensitive", False)),
        )

        return {
            "headline_en": headline_en,
            "headline_bn": headline_bn,
            "primary_genre": genre,
            "secondary_genres": sec_genres,
            "geography": geo,
            "state_name": state_val,
            "status": story_status,
            "summary_en": {
                "in_brief": in_brief_en,
                "sources": source_names,
            },
            "summary_bn": {
                "headline_bn": headline_bn,
                "in_brief": in_brief_bn,
            },
        }

    # 1. Try Groq 120B (primary) then 20B (backup)
    if groq_api_key and Groq is not None:
        g_client = Groq(api_key=groq_api_key.strip(), max_retries=1)
        for model_id in (PRIMARY_MODEL, BACKUP_MODEL):
            try:
                chat_resp = g_client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a senior copy editor at a Kolkata broadsheet following Paschimbanga Bangla Akademi standards. "
                                "Output valid JSON only. Always generate original, non-verbatim editorial headlines; never copy or lightly paraphrase source headlines."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    reasoning_effort="low",
                    temperature=0.35,
                    max_tokens=4096,
                )
                content = chat_resp.choices[0].message.content or ""
                parsed = _extract_json_object(content)
                audit_client = g_client if model_id == PRIMARY_MODEL else None
                return _finalize_parsed(parsed, g_client=audit_client), None
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

    # 3. Non-verbatim fallback when LLM is unavailable or errored
    safe_geo = fallback_geo if fallback_geo in ALLOWED_GEOGRAPHIES else "National"
    safe_genre = _normalize_genre(primary["title"], active_genres)
    non_verbatim_en = _build_non_verbatim_fallback_headline(primary, safe_genre, safe_geo)
    combined_brief = primary["snippet"] or non_verbatim_en
    bn_fallback_title = f"{safe_genre} সংবাদ সংক্ষেপ ({', '.join(source_names)})"
    bn_fallback_brief = f"সূত্র: {', '.join(source_names)} — {non_verbatim_en}"
    return (
        {
            "headline_en": non_verbatim_en,
            "headline_bn": bn_fallback_title,
            "primary_genre": safe_genre,
            "secondary_genres": [],
            "geography": safe_geo,
            "state_name": "West Bengal" if safe_geo == "State" else None,
            "status": _detect_sensitive_status(non_verbatim_en, combined_brief, False),
            "summary_en": {
                "in_brief": combined_brief,
                "sources": source_names,
            },
            "summary_bn": {
                "headline_bn": bn_fallback_title,
                "in_brief": bn_fallback_brief,
            },
        },
        llm_error,
    )


def regenerate_existing_headlines(
    supabase,
    groq_api_key: str | None = None,
    gemini_api_key: str | None = None,
    limit: int = 150,
) -> dict:
    """
    One-time editorial maintenance helper: rewrites headline_en and headline_bn on existing
    published stories in Supabase into fresh, non-verbatim broadsheet headlines derived from
    their consolidated summaries, without altering IDs, timestamps, or source links.
    """
    try:
        res = (
            supabase.table("stories")
            .select("id, headline_en, headline_bn, primary_genre, geography, summary_en, summary_bn")
            .eq("status", "published")
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = res.data or []
    except Exception as exc:
        return {"updated": 0, "message": f"Failed to fetch existing stories: {exc}"}

    if not rows:
        return {"updated": 0, "message": "No published stories found to regenerate."}

    g_client = Groq(api_key=groq_api_key.strip(), max_retries=1) if (groq_api_key and Groq is not None) else None
    gem_client = genai.Client(api_key=gemini_api_key.strip()) if (gemini_api_key and genai is not None) else None

    updated_count = 0
    errors: list[str] = []

    for row in rows:
        old_en = (row.get("headline_en") or "").strip()
        old_bn = (row.get("headline_bn") or "").strip()
        genre = row.get("primary_genre") or "General"
        geo = row.get("geography") or "National"
        sum_en_obj = row.get("summary_en") or {}
        sum_bn_obj = row.get("summary_bn") or {}
        brief_en = (sum_en_obj.get("in_brief") if isinstance(sum_en_obj, dict) else str(sum_en_obj)) or old_en
        brief_bn = (sum_bn_obj.get("in_brief") if isinstance(sum_bn_obj, dict) else str(sum_bn_obj)) or old_bn

        # Clean inline '(Corroborated across...)' if present in older summaries
        clean_brief_en = re.sub(r"\s*\(Corroborated across[^)]*\)\.?", "", brief_en, flags=re.IGNORECASE).strip()

        rewrite_prompt = (
            "You are a senior copy editor at a Kolkata broadsheet. Rewrite the existing headline below into a completely fresh, "
            "original, non-verbatim editorial broadsheet headline in BOTH English and West Bengal standard Bengali (বাংলা লিপি), "
            "based strictly on the summary facts.\n"
            "RULES:\n"
            "1. Do NOT reuse the phrasing, word order, or structure of the Existing Headline.\n"
            "2. Keep 'headline_en' crisp, factual, and under 14 words.\n"
            "3. Write 'headline_bn' in natural Kolkata newspaper Bengali (Paschimbanga Bangla Akademi standard).\n"
            "Respond ONLY with a raw JSON object containing keys \"headline_en\" and \"headline_bn\".\n\n"
            f"Genre: {genre} | Geography: {geo}\n"
            f"Existing English Headline (DO NOT COPY): {old_en}\n"
            f"English Summary: {clean_brief_en}\n"
            f"Bengali Summary: {brief_bn}"
        )

        new_en = ""
        new_bn = ""

        if g_client is not None:
            for model_id in (PRIMARY_MODEL, BACKUP_MODEL):
                try:
                    resp = g_client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "Return strictly valid JSON with fresh non-verbatim broadsheet headlines."},
                            {"role": "user", "content": rewrite_prompt},
                        ],
                        reasoning_effort="low",
                        temperature=0.4,
                        max_tokens=512,
                    )
                    parsed = _extract_json_object(resp.choices[0].message.content or "")
                    new_en = (parsed.get("headline_en") or "").strip()
                    new_bn = (parsed.get("headline_bn") or "").strip()
                    if new_en:
                        break
                except Exception as exc:
                    if str(exc) not in errors:
                        errors.append(str(exc))

        if not new_en and gem_client is not None:
            try:
                resp = gem_client.models.generate_content(model="gemini-2.5-flash", contents=rewrite_prompt)
                parsed = _extract_json_object(resp.text or "")
                new_en = (parsed.get("headline_en") or "").strip()
                new_bn = (parsed.get("headline_bn") or "").strip()
            except Exception as exc:
                if str(exc) not in errors:
                    errors.append(str(exc))

        if not new_en or _is_verbatim_or_close_copy(new_en, [old_en]):
            new_en = f"{genre} Dispatch: Key {geo} Developments"

        new_bn = _apply_universal_bengali_morphology(new_bn)
        if not _has_bengali_script(new_bn) or new_bn == old_bn:
            new_bn = f"{genre} সংবাদ সংক্ষেপ"

        updated_sum_en = dict(sum_en_obj) if isinstance(sum_en_obj, dict) else {"in_brief": clean_brief_en}
        updated_sum_en["in_brief"] = clean_brief_en
        updated_sum_bn = dict(sum_bn_obj) if isinstance(sum_bn_obj, dict) else {"in_brief": brief_bn}
        updated_sum_bn["headline_bn"] = new_bn

        try:
            supabase.table("stories").update(
                {
                    "headline_en": new_en,
                    "headline_bn": new_bn,
                    "summary_en": updated_sum_en,
                    "summary_bn": updated_sum_bn,
                }
            ).eq("id", row["id"]).execute()
            updated_count += 1
        except Exception as upd_exc:
            if str(upd_exc) not in errors:
                errors.append(str(upd_exc))

        time.sleep(0.25)

    diag = f" (Note: {errors[0]})" if errors else ""
    return {
        "updated": updated_count,
        "message": f"Regenerated non-verbatim English & Bengali headlines for {updated_count} of {len(rows)} existing stories.{diag}",
    }


def run_ingestion_cycle(
    supabase,
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
    edition_slot: str = "live",
    since_date: str | None = None,
    exhaustive: bool = False,
) -> dict:
    """
    Executes collect -> exclude astrology -> deduplicate -> cross-language cluster -> synthesize -> publish.
    """
    slot = edition_slot if edition_slot in ALLOWED_EDITION_SLOTS else "live"
    since_dt_ist: datetime | None = None
    if since_date:
        try:
            parsed_d = datetime.strptime(since_date.strip()[:10], "%Y-%m-%d")
            since_dt_ist = IST.localize(parsed_d)
        except Exception:
            since_dt_ist = None

    per_feed_limit = 25 if (exhaustive or since_dt_ist is not None) else 10
    raw_items, astrology_skipped = fetch_rss_items(
        max_per_feed=per_feed_limit,
        since_dt_ist=since_dt_ist,
    )
    fetched_count = len(raw_items)
    if not raw_items:
        return {
            "fetched": 0,
            "published": 0,
            "message": f"No non-astrology RSS entries reachable (excluded {astrology_skipped} astrology/horoscope items).",
        }

    bn_fetched = sum(1 for it in raw_items if it["language"] == "bn")
    active_genre_rows = fetch_approved_genres(supabase)
    valid_genre_names = [g["name_en"] for g in active_genre_rows]
    existing_urls, existing_headlines = _get_existing_urls_and_headlines(supabase)

    fresh_items = [it for it in raw_items if it["url"] not in existing_urls]
    if not fresh_items:
        raw_items.clear()
        return {
            "fetched": fetched_count,
            "published": 0,
            "message": (
                f"Fetched {fetched_count} RSS items ({bn_fetched} Bengali, excluded {astrology_skipped} astrology items); "
                f"all were already published in recent cycles."
            ),
        }

    cluster_cap = None if (exhaustive or since_dt_ist is not None) else 25
    clusters = cluster_items(fresh_items, max_clusters=cluster_cap)

    published_count = 0
    bn_published = 0
    multi_source_count = 0
    flagged_count = 0
    skipped
