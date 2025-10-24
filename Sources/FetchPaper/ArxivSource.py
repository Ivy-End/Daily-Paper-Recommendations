import requests
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from .Source import Source

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

def _parse_atom_date(s: str) -> str:
    # arXiv uses RFC3339/ATOM format, e.g., "2025-10-23T17:31:15Z"
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.date().isoformat()
    except Exception:
        try:
            # Fallback for any slight variants
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
        except Exception:
            return ""

class ArxivSource(Source):
    name = "arXiv"

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        """Fetch arXiv entries submitted between [day, nextDay).

        arXiv API (Atom feed) does not support an explicit date range filter,
        so we fetch pages by submittedDate (desc) and stop when entries fall before 'day'.
        """
        perPage = int(kwargs.get("perPage", 200))
        maxPages = int(kwargs.get("maxPages", 6))

        # Construct base query: everything, sorted by submitted date desc
        # Doc: https://info.arxiv.org/help/api/user-manual.html
        base_url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": "all",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": 0,
            "max_results": perPage,
        }

        out: list[dict] = []
        for _ in range(maxPages):
            r = requests.get(base_url, params=params, timeout=60)
            r.raise_for_status()
            feed = ET.fromstring(r.text)

            entries = feed.findall("atom:entry", ATOM_NS)
            if not entries:
                break

            stop_paging = False
            for e in entries:
                # id / link
                id_text = (e.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()

                # title / summary
                title = (e.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
                abstract = (e.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()

                # published date
                published_raw = (e.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
                pub_date = _parse_atom_date(published_raw)

                if pub_date and pub_date < day:
                    stop_paging = True
                    continue
                if pub_date and not (day <= pub_date < nextDay):
                    continue

                # doi (optional)
                doi = (e.findtext("arxiv:doi", default="", namespaces=ATOM_NS) or "").strip()

                # url: prefer alternate link
                url = ""
                for link in e.findall("atom:link", ATOM_NS):
                    if link.get("rel") == "alternate" and link.get("href"):
                        url = link.get("href")
                        break
                if not url:
                    url = id_text

                # venue: use primary category if available
                primary_cat = e.find("arxiv:primary_category", ATOM_NS)
                venue = primary_cat.get("term") if primary_cat is not None else ""

                out.append(self._norm({
                    "id": id_text,
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue,
                    "date": pub_date,
                    "source": self.name,
                }))

            if stop_paging:
                break

            params["start"] = int(params["start"]) + perPage

        return out
