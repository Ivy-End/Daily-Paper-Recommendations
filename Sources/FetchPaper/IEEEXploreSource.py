import os
import requests
from .Source import Source

class IEEEXploreSource(Source):
    """IEEE Xplore Search API wrapper.

    Docs: https://developer.ieee.org/ (institutional key required)
    We'll accept an API key via kwargs['api_key'] or env IEEE_API_KEY.
    Date-range filtering is applied on 'publication_date' (if present) or 'publication_year'.
    """
    name = "IEEE Xplore"

    def _in_range(self, date: str, day: str, nextDay: str) -> bool:
        if not date:
            return False
        # Accept YYYY, YYYY-MM, YYYY-MM-DD; compare lexicographically on prefix as best effort.
        # Normalize to YYYY-MM-DD when possible
        parts = date.split("-")
        if len(parts) == 1:
            d = f"{parts[0]}-01-01"
        elif len(parts) == 2:
            d = f"{parts[0]}-{int(parts[1]):02d}-01"
        else:
            d = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        return (day <= d < nextDay)

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        api_key = kwargs.get("api_key") or os.getenv("IEEE_API_KEY", "")
        if not api_key:
            # No key, skip gracefully
            return []

        base = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        max_records = int(kwargs.get("max_records", 200))
        page_size = min(int(kwargs.get("page_size", 100)), 200)  # API allows up to 200
        querytext = kwargs.get("querytext", "")  # optional filter
        sort_field = kwargs.get("sort_field", "publication_year")
        sort_order = kwargs.get("sort_order", "desc")

        params = {
            "apikey": api_key,
            "max_records": page_size,
            "start_record": 1,
            "sort_order": sort_order,
            "sort_field": sort_field,
        }
        if querytext:
            params["querytext"] = querytext

        out: list[dict] = []
        fetched = 0
        while fetched < max_records:
            r = requests.get(base, params=params, timeout=60)
            # If unauthorized or rate limited, stop silently
            if r.status_code != 200:
                break
            js = r.json()
            articles = (js.get("articles") or [])
            if not articles:
                break
            for a in articles:
                title = (a.get("title") or "").strip()
                abstract = (a.get("abstract") or "").strip()
                doi = (a.get("doi") or "").strip()
                url = a.get("html_url") or a.get("pdf_url") or a.get("htmlLink") or ""
                venue = (a.get("publication_title") or a.get("publisher") or "IEEE").strip()
                date = (a.get("publication_date") or str(a.get("publication_year") or "")).strip()
                if not self._in_range(date, day, nextDay):
                    continue

                art_id = a.get("article_number") or doi or title[:40]
                out.append(self._norm({
                    "id": str(art_id),
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue,
                    "date": date[:10],
                    "source": self.name,
                }))
            fetched += len(articles)
            if len(articles) < page_size:
                break
            params["start_record"] = int(params["start_record"]) + page_size

        return out
