import requests
from .Source import Source

class DBLPSource(Source):
    """DBLP publications search (JSON).

    Docs: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
    We'll query by free text and then filter by [day, nextDay) using year/month/day if available.
    """
    name = "DBLP"

    def _normalize_date(self, y: str, m: str = "", d: str = "") -> str:
        if not y:
            return ""
        y = f"{int(y):04d}"
        if m:
            m = f"{int(m):02d}"
        else:
            m = "01"
        if d:
            d = f"{int(d):02d}"
        else:
            d = "01"
        return f"{y}-{m}-{d}"

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        base = "https://dblp.org/search/publ/api"
        query = kwargs.get("query", "") or ""
        h = int(kwargs.get("page_size", 200))
        f = 0
        max_pages = int(kwargs.get("max_pages", 5))

        out: list[dict] = []
        for _ in range(max_pages):
            params = {"q": query, "format": "json", "h": h, "f": f}
            r = requests.get(base, params=params, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            hits = ((js.get("result") or {}).get("hits") or {}).get("hit") or []
            if not hits:
                break
            for hit in hits:
                info = hit.get("info") or {}
                title = (info.get("title") or "").strip()
                venue = (info.get("venue") or info.get("journal") or info.get("booktitle") or "").strip()
                year = (info.get("year") or "").strip()
                # DBLP sometimes has 'ee' for full text URL
                url = (info.get("ee") or info.get("url") or "")
                # No abstract; leave empty
                abstract = ""
                # Some records have month/day in 'year' or 'date' field; try parse date
                date = ""
                date_field = (info.get("date") or "").strip()  # could be YYYY-MM
                if date_field:
                    parts = date_field.split("-")
                    if len(parts) == 2:
                        date = f"{int(parts[0]):04d}-{int(parts[1]):02d}-01"
                    elif len(parts) >= 3:
                        date = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                if not date:
                    date = self._normalize_date(year)

                if date and not (day <= date < nextDay):
                    continue

                out.append(self._norm({
                    "id": info.get("key") or title[:40],
                    "title": title,
                    "abstract": abstract,
                    "doi": (info.get("doi") or ""),
                    "url": url,
                    "venue": venue,
                    "date": date,
                    "source": self.name,
                }))
            f += h
        return out
