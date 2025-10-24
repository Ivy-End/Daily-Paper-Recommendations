import os
import requests
from .Source import Source

class NASAADSSource(Source):
    """NASA ADS (Astrophysics Data System) search.

    Docs: https://ui.adsabs.harvard.edu/help/api/
    - Endpoint: https://api.adsabs.harvard.edu/v1/search/query
    - Auth: Bearer token via kwargs['api_key'] or env ADS_API_TOKEN
    - Server-side date window using pubdate range; client-side day filter as fallback.
    """

    name = "NASA ADS"

    FIELDS = [
        "id", "title", "abstract", "doi", "pubdate", "year", "pub", "page", "esources",
        "identifier", "url"
    ]

    def _norm_date(self, s: str) -> str:
        if not s:
            return ""
        s = str(s).strip()
        # ADS pubdate often "YYYY-MM"
        parts = s.split("-")
        try:
            if len(parts) == 1:
                return f"{int(parts[0]):04d}-01-01"
            elif len(parts) == 2:
                return f"{int(parts[0]):04d}-{int(parts[1]):02d}-01"
            else:
                return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        except Exception:
            return ""

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        token = kwargs.get("api_key") or os.getenv("ADS_API_TOKEN", "")
        if not token:
            # No token, skip gracefully
            return []

        base = "https://api.adsabs.harvard.edu/v1/search/query"
        page_size = min(int(kwargs.get("page_size", 100)), 200)
        max_pages = int(kwargs.get("max_pages", 10))
        query = kwargs.get("query", "") or "*"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        # ADS Lucene-like filter for publication date
        # Inclusive range: pubdate:[day TO nextDay}
        # ADS usually stores pubdate as YYYY-MM; still works for windowing.
        q = query
        fq = f"pubdate:[{day} TO {nextDay}}]"

        params = {
            "q": q,
            "fq": fq,
            "fl": ",".join(self.FIELDS),
            "rows": page_size,
            "start": 0,
            "sort": "date desc",
        }

        out: list[dict] = []
        for _ in range(max_pages):
            r = requests.get(base, params=params, headers=headers, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            docs = ((js.get("response") or {}).get("docs") or [])
            if not docs:
                break
            for d in docs:
                title = ""
                t = d.get("title")
                if isinstance(t, list) and t:
                    title = (t[0] or "").strip()
                elif isinstance(t, str):
                    title = t.strip()

                abstract = (d.get("abstract") or "").strip()
                doi = ""
                if isinstance(d.get("doi"), list) and d["doi"]:
                    doi = d["doi"][0]
                elif isinstance(d.get("doi"), str):
                    doi = d["doi"]
                url = ""
                # prefer ui link
                if d.get("id"):
                    url = f"https://ui.adsabs.harvard.edu/abs/{d['id']}"
                elif doi:
                    url = f"https://doi.org/{doi}"
                venue = (d.get("pub") or "").strip()
                date = self._norm_date(d.get("pubdate") or d.get("year"))

                # final guard for date
                if date and not (day <= date < nextDay):
                    continue

                out.append(self._norm({
                    "id": d.get("id") or doi or title[:40],
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue or "NASA ADS",
                    "date": date,
                    "source": self.name,
                }))
            if len(docs) < page_size:
                break
            params["start"] = int(params["start"]) + page_size

        return out
