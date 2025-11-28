import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone
from html import escape

RSS_FEEDS = [
    "https://www.stilllisteningmagazine.com/features?format=rss",
    "https://www.stilllisteningmagazine.com/interviews?format=rss",
    "https://www.stilllisteningmagazine.com/reviews?format=rss",
    "https://www.stilllisteningmagazine.com/gig-reviews?format=rss",
    "https://www.stilllisteningmagazine.com/start-listening-to?format=rss",
]


def fetch_feed(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def parse_feed(data: bytes):
    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub_date = item.findtext("pubDate") or ""
        if not link or not pub_date:
            continue
        try:
            dt = parsedate_to_datetime(pub_date)
        except Exception:
            continue

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        items.append(
            {
                "title": title.strip(),
                "link": link.strip(),
                "published": dt,
            }
        )
    return items


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    all_items = []
    seen_links = set()

    for feed in RSS_FEEDS:
        try:
            data = fetch_feed(feed)
            items = parse_feed(data)
            for it in items:
                if it["link"] in seen_links:
                    continue
                if it["published"] < cutoff:
                    continue
                seen_links.add(it["link"])
                all_items.append(it)
        except Exception as e:
            print(f"Error processing feed {feed}: {e}")

    all_items.sort(key=lambda x: x["published"], reverse=True)

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
    )

    for it in all_items:
        loc = escape(it["link"])
        pub_iso = it["published"].strftime("%Y-%m-%dT%H:%M:%SZ")
        title = escape(it["title"])

        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append("    <news:news>")
        lines.append("      <news:publication>")
        lines.append("        <news:name>Still Listening Magazine</news:name>")
        lines.append("        <news:language>en</news:language>")
        lines.append("      </news:publication>")
        lines.append(f"      <news:publication_date>{pub_iso}</news:publication_date>")
        lines.append(f"      <news:title>{title}</news:title>")
        lines.append("    </news:news>")
        lines.append("  </url>")

    lines.append("</urlset>")

    with open("news-sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
