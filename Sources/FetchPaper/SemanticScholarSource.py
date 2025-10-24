import os
import requests
from .Source import Source

class SemanticScholarSource(Source):
    """Semantic Scholar Graph API (paper search).

    Docs: https://api.semanticscholar.org/api-docs/graph
    Optional API key via kwargs['api_key'] or env S2_API_KEY for higher limits.
    We'll use /graph/v1/paper/search with a year window and then day-precision filtering.
    """
    name = "Semantic Scholar"

    FIELDS = "title,abstract,venue,publicationDate,year,externalIds,url"

    def _in_range(self, date: str, day: str, nextDay: str) -> bool:
        if not date:
            return False
        # Expect YYYY-MM-DD (or YYYY-MM). Normalize to YYYY-MM-DD
        parts = date.split("-")
        try:
            if len(parts) == 1:
                d = f"{parts[0]}-01-01"
            elif len(parts) == 2:
                d = f"{parts[0]}-{int(parts[1]):02d}-01"
            else:
                d = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        except Exception:
            return False
        return day <= d < nextDay

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        api_key = kwargs.get("api_key") or os.getenv("S2_API_KEY", "")
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        base = "https://api.semanticscholar.org/graph/v1/paper/search"
        page_size = min(int(kwargs.get("page_size", 100)), 100)
        max_pages = int(kwargs.get("max_pages", 10))
        query = kwargs.get("query", "") or ""

        y0 = int(day[:4])
        y1 = int(nextDay[:4])
        year_param = f"{y0}-{y1}" if y0 != y1 else str(y0)

        params = {
            "query": query if query else "*",
            "fields": self.FIELDS,
            "limit": page_size,
            "offset": 0,
            "year": year_param,
            "sort": "publicationDate:desc",
        }

        out: list[dict] = []
        for _ in range(max_pages):
            r = requests.get(base, params=params, headers=headers, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            data = js.get("data") or []
            if not data:
                break
            for p in data:
                title = (p.get("title") or "").strip()
                abstract = (p.get("abstract") or "").strip()
                doi = ""
                ex = p.get("externalIds") or {}
                if isinstance(ex, dict):
                    doi = (ex.get("DOI") or "").strip()
                url = (p.get("url") or (f"https://doi.org/{doi}" if doi else "")) or ""
                venue = (p.get("venue") or "").strip()
                date = (p.get("publicationDate") or str(p.get("year") or "")).strip()
                if not self._in_range(date, day, nextDay):
                    continue
                out.append(self._norm({
                    "id": doi or title[:40],
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue,
                    "date": date[:10] if date else "",
                    "source": self.name,
                }))
            if len(data) < page_size:
                break
            params["offset"] = int(params["offset"]) + page_size

        return out
