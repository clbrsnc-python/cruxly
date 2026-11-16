NEWS_SOURCES = [
    # --- BENGALI DAILIES (WEST BENGAL) ---
    {
        "id": "anandabazar",
        "name": "Anandabazar Patrika",
        "language": "bn",
        "default_geography": "State",
        "rss_urls": [
            "https://news.google.com/rss/search?q=site:anandabazar.com%20when%3A2d&hl=bn&gl=IN&ceid=IN:bn",
        ],
    },
    {
        "id": "bartaman",
        "name": "Bartaman",
        "language": "bn",
        "default_geography": "State",
        "rss_urls": [
            "https://news.google.com/rss/search?q=site:bartamanpatrika.com%20when%3A2d&hl=bn&gl=IN&ceid=IN:bn",
        ],
    },
    {
        "id": "aajkaal",
        "name": "Aajkaal",
        "language": "bn",
        "default_geography": "State",
        "rss_urls": [
            "https://news.google.com/rss/search?q=site:aajkaal.in%20when%3A2d&hl=bn&gl=IN&ceid=IN:bn",
        ],
    },
    {
        "id": "sangbad_pratidin",
        "name": "Sangbad Pratidin",
        "language": "bn",
        "default_geography": "State",
        "rss_urls": [
            "https://www.sangbadpratidin.in/feed/",
            "https://news.google.com/rss/search?q=site:sangbadpratidin.in%20when%3A2d&hl=bn&gl=IN&ceid=IN:bn",
        ],
    },
    {
        "id": "ei_samay",
        "name": "Ei Samay",
        "language": "bn",
        "default_geography": "State",
        "rss_urls": [
            "https://eisamay.com/rssfeedstopstories.cms",
            "https://news.google.com/rss/search?q=site:eisamay.com%20when%3A2d&hl=bn&gl=IN&ceid=IN:bn",
        ],
    },
    # --- ENGLISH DAILIES (NATIONAL & KOLKATA) ---
    {
        "id": "the_hindu",
        "name": "The Hindu",
        "language": "en",
        "default_geography": "National",
        "rss_urls": [
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://www.thehindu.com/news/international/feeder/default.rss",
        ],
    },
    {
        "id": "indian_express",
        "name": "The Indian Express",
        "language": "en",
        "default_geography": "National",
        "rss_urls": [
            "https://indianexpress.com/section/india/feed/",
            "https://indianexpress.com/section/cities/kolkata/feed/",
        ],
    },
    {
        "id": "times_of_india",
        "name": "The Times of India",
        "language": "en",
        "default_geography": "National",
        "rss_urls": [
            "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "https://timesofindia.indiatimes.com/rssfeeds/-2128830821.cms",
        ],
    },
    {
        "id": "telegraph_india",
        "name": "The Telegraph",
        "language": "en",
        "default_geography": "State",
        "rss_urls": [
            "https://news.google.com/rss/search?q=site:telegraphindia.com%20when%3A2d&hl=en-IN&gl=IN&ceid=IN:en",
        ],
    },
    {
        "id": "hindustan_times",
        "name": "Hindustan Times",
        "language": "en",
        "default_geography": "National",
        "rss_urls": [
            "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
            "https://www.hindustantimes.com/feeds/rss/kolkata/rssfeed.xml",
        ],
    },
    {
        "id": "ndtv",
        "name": "NDTV",
        "language": "en",
        "default_geography": "National",
        "rss_urls": [
            "https://feeds.feedburner.com/ndtvnews-india-news",
        ],
    },
    # --- HINDI DAILIES ---
    {
        "id": "dainik_bhaskar",
        "name": "Dainik Bhaskar",
        "language": "hi",
        "default_geography": "National",
        "rss_urls": [
            "https://www.bhaskar.com/rss-v1--category-1061.xml",
        ],
    },
    {
        "id": "amar_ujala",
        "name": "Amar Ujala",
        "language": "hi",
        "default_geography": "National",
        "rss_urls": [
            "https://www.amarujala.com/rss/india-news.xml",
        ],
    },
    {
        "id": "navbharat_times",
        "name": "Navbharat Times",
        "language": "hi",
        "default_geography": "National",
        "rss_urls": [
            "https://navbharattimes.indiatimes.com/rssfeedstopstories.cms",
        ],
    },
    {
        "id": "live_hindustan",
        "name": "Live Hindustan",
        "language": "hi",
        "default_geography": "National",
        "rss_urls": [
            "https://www.livehindustan.com/rss/national.xml",
        ],
    },
]


def get_active_sources() -> list[dict]:
    return NEWS_SOURCES
