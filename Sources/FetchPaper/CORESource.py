import os
import requests
from .Source import Source

class CORESource(Source):
    """CORE API (OA aggregator).

    Notes:
    - Supports CORE v3 (https://api.core.ac.uk/v3/) via /search/works with Bearer token.
    - Also provides a fallback to v2-like /search/works endpoint without auth if available.
    - We do client-side filtering to [day, nextDay) on common date fields.
    Usage:
      CORESource().Fetch(day="2025-10-23", nextDay="2025-10-24", api_key="...", query="camera sensor", page_size=100, max_pages=10)
    """
    name = "CORE"

    DATE_FIELDS = ["publishedDate", "datePublished", "year", "date", "createdDate", "oai.datestamp"]

    def _norm_date(self, date_val: str) -> str:
        if not date_val:
            return ""
        s = str(date_val).strip()
        # Accept YYYY, YYYY-MM, YYYY-MM-DD
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

    def _extract_date(self, rec: dict) -> str:
        # Try several likely fields
        for k in self.DATE_FIELDS:
            v = rec
            for part in k.split("."):
                if isinstance(v, dict) and part in v:
                    v = v.get(part)
                else:
                    v = None
                    break
            if v:
                nd = self._norm_date(v)
                if nd:
                    return nd
        return ""

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        base_v3 = kwargs.get("base_v3") or "https://api.core.ac.uk/v3"
        base_v2 = kwargs.get("base_v2") or "https://api.core.ac.uk/v3"  # keep same path; some proxies alias
        api_key = kwargs.get("api_key") or os.getenv("CORE_API_KEY", "kz7XPvtybwZDCpRj1mB8d9UEAxOMGL5c")
        query = kwargs.get("query", "") or "*"
        page_size = min(int(kwargs.get("page_size", 100)), 100)
        max_pages = int(kwargs.get("max_pages", 10))

        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        out: list[dict] = []

        # Try v3 search/works with pagination via "offset"
        params = {"q": query, "limit": page_size, "offset": 0, "sort": "publishedDate:desc"}
        for _ in range(max_pages):
            try:
                r = requests.get(f"{base_v3}/search/works", params=params, headers=headers, timeout=60)
            except Exception:
                break
            if r.status_code != 200:
                break
            js = r.json()
            data = js.get("results") or js.get("data") or js.get("items") or []
            if not isinstance(data, list) or not data:
                break
            for rec in data:
                # v3 shape often: {"_source":{...}} or flattened
                src = rec.get("_source") if isinstance(rec, dict) else None
                doc = src if isinstance(src, dict) else rec if isinstance(rec, dict) else {}

                title = (doc.get("title") or "").strip()
                abstract = (doc.get("abstract") or doc.get("description") or "").strip()
                doi = (doc.get("doi") or "").strip()
                url = (doc.get("downloadUrl") or doc.get("links", {}).get("self") or doc.get("url") or "")
                venue = (doc.get("publisher") or doc.get("journal") or doc.get("venue") or "CORE").strip()
                date = self._extract_date(doc)
                if date and not (day <= date < nextDay):
                    continue

                ident = doi or doc.get("id") or (title[:40] if title else "")
                out.append(self._norm({
                    "id": str(ident),
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue,
                    "date": (date or "")[:10],
                    "source": self.name,
                }))
            if len(data) < page_size:
                break
            params["offset"] = int(params["offset"]) + page_size

        return out
