import feedparser
import datetime
from concurrent.futures import ThreadPoolExecutor

# Source Map
FEEDS = {
    "🇩🇪 Germany & Stuttgart": [
        "https://www.tagesschau.de/xml/rss2",
        "https://www.spiegel.de/schlagzeilen/tops/index.rss",
        "https://rss.heise.de/developer/atom.xml",
        "https://www.handelsblatt.com/contentexport/feed/top-themen"
    ],
    "🇧🇷 Brazil & LATAM": [
        "https://g1.globo.com/rss/g1/",
        "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"
    ],
    "🤖 AI & Deep Tech": [
        "http://feeds.feedburner.com/TechCrunch/",
        "https://news.ycombinator.com/rss",
        "https://the-decoder.de/feed/",
        "http://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/index.xml",
        "https://huggingface.co/blog/feed.xml",
        "http://rss.slashdot.org/Slashdot/slashdot",
        "https://www.reddit.com/r/technology/top/.rss?t=day",
        "https://www.reddit.com/r/artificial/top/.rss?t=day",
        "https://www.reddit.com/r/rust/top/.rss?t=day"
    ],
    "🌏 Global, Asia & Econ": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.scmp.com/rss/2/feed",
        "https://asia.nikkei.com/rss/feed/nar",
        "https://www.caixinglobal.com/rss/",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://www.politico.eu/feed/"
    ]
}

def parse_feed(category, url):
    try:
        feed = feedparser.parse(url)
        entries = []
        # Get top 3 entries per feed
        for entry in feed.entries[:3]:
            # Clean title
            title = entry.title.replace('\n', ' ').strip()
            entries.append(f"[{category}] {title}: {entry.link}")
        return entries
    except Exception as e:
        return [f"Error parsing {url}: {e}"]

def main():
    print(f"FETCH_DATE: {datetime.date.today()}")
    all_news = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for category, urls in FEEDS.items():
            for url in urls:
                futures.append(executor.submit(parse_feed, category, url))
        
        for future in futures:
            all_news.extend(future.result())
    
    # Output formatted for the Agent to read
    print("\n".join(all_news))

if __name__ == "__main__":
    main()
