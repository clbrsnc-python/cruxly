"""
Cruxly Source Registry (DPR Section 4: Sources & Collection Policy)
Defines the initial target newspapers across English, Bengali, and Hindi,
with RSS endpoints and official domain references for fair-dealing attribution.
"""

SOURCES_REGISTRY = [
    # --- ENGLISH (7) ---
    {
        "id": "the_hindu",
        "name": "The Hindu",
        "language": "en",
        "domain": "https://www.thehindu.com",
        "rss_urls": [
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://www.thehindu.com/news/international/feeder/default.rss",
            "https://www.thehindu.com/business/feeder/default.rss",
        ],
        "default_geography": "National",
        "active": True,
    },
    {
        "id": "indian_express",
        "name": "The Indian Express",
        "language": "en",
        "domain": "https://indianexpress.com",
        "rss_urls": [
            "https://indianexpress.com/section/india/feed/",
            "https://indianexpress.com/section/cities/kolkata/feed/",
            "https://indianexpress.com/section/world/feed/",
        ],
        "default_geography": "National",
        "active": True,
    },
    {
        "id": "hindustan_times",
        "name": "Hindustan Times",
        "language": "en",
        "domain": "https://www.hindustantimes.com",
        "rss_urls": [
            "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
            "https://www.hindustantimes.com/feeds/rss/cities/kolkata-news/rssfeed.xml",
            "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
        ],
        "default_geography": "National",
        "active": True,
    },
    {
        "id": "times_of_india",
        "name": "The Times of India",
        "language": "en",
        "domain": "https://timesofindia.indiatimes.com",
        "rss_urls": [
            "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
            "https://timesofindia.indiatimes.com/rssfeeds/-2128830821.cms",
        ],
        "default_geography": "National",
        "active": True,
    },
    {
        "id": "the_telegraph",
        "name": "The Telegraph",
        "language": "en",
        "domain": "https://www.telegraphindia.com",
        "rss_urls": [
            "https://www.telegraphindia.com/rss/india",
            "https://www.telegraphindia.com/rss/west-bengal",
            "https://www.telegraphindia.com/rss/world",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "the_statesman",
        "name": "The Statesman",
        "language": "en",
        "domain": "https://www.thestatesman.com",
        "rss_urls": [
            "https://www.thestatesman.com/feed",
            "https://www.thestatesman.com/bengal/feed",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "business_standard",
        "name": "Business Standard",
        "language": "en",
        "domain": "https://www.business-standard.com",
        "rss_urls": [
            "https://www.business-standard.com/rss/home_page_top_stories.rss",
            "https://www.business-standard.com/rss/economy-102.rss",
        ],
        "default_geography": "National",
        "active": True,
    },

    # --- BENGALI (6) ---
    {
        "id": "anandabazar",
        "name": "Anandabazar Patrika",
        "language": "bn",
        "domain": "https://www.anandabazar.com",
        "rss_urls": [
            "https://www.anandabazar.com/rss/west-bengal",
            "https://www.anandabazar.com/rss/national",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "bartaman",
        "name": "Bartaman",
        "language": "bn",
        "domain": "https://bartamanpatrika.com",
        "rss_urls": [
            "https://bartamanpatrika.com/feed",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "ei_samay",
        "name": "Ei Samay",
        "language": "bn",
        "domain": "https://eisamay.com",
        "rss_urls": [
            "https://eisamay.com/rssfeedstopstories.cms",
            "https://eisamay.com/west-bengal-news/rssfeedsection/15819574.cms",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "sangbad_pratidin",
        "name": "Sangbad Pratidin",
        "language": "bn",
        "domain": "https://www.sangbadpratidin.in",
        "rss_urls": [
            "https://www.sangbadpratidin.in/feed/",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "aajkaal",
        "name": "Aajkaal",
        "language": "bn",
        "domain": "https://www.aajkaal.in",
        "rss_urls": [
            "https://www.aajkaal.in/rss/west-bengal",
            "https://www.aajkaal.in/rss/national",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },
    {
        "id": "uttarbanga_sambad",
        "name": "Uttarbanga Sambad",
        "language": "bn",
        "domain": "https://uttarbangasambad.com",
        "rss_urls": [
            "https://uttarbangasambad.com/feed/",
        ],
        "default_geography": "West Bengal",
        "active": True,
    },

    # --- HINDI (2) ---
    {
        "id": "punjab_kesari",
        "name": "Punjab Kesari",
        "language": "hi",
        "domain": "https://www.punjabkesari.in",
        "rss_urls": [
            "https://www.punjabkesari.in/rss/national.xml",
        ],
        "default_geography": "National",
        "active": True,
    },
    {
        "id": "prabhat_khabar",
        "name": "Prabhat Khabar",
        "language": "hi",
        "domain": "https://www.prabhatkhabar.com",
        "rss_urls": [
            "https://www.prabhatkhabar.com/rss/national",
            "https://www.prabhatkhabar.com/rss/kolkata",
        ],
        "default_geography": "National",
        "active": True,
    },
]


def get_active_sources() -> list[dict]:
    """Returns all active newspaper configurations."""
    return [src for src in SOURCES_REGISTRY if src.get("active", True)]
