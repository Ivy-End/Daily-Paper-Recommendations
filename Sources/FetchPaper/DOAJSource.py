import requests
from .Source import Source

class DOAJSource(Source):
    """DOAJ (Directory of Open Access Journals) search API.

    Docs: https://doaj.org/api/v2/docs
    We use /search/articles/{query}?pageSize=&page=
    We'll filter locally to [day, nextDay) using year/created_date if present.
    """
    name = "DOAJ"

    def _norm_date(self, date_val: str) -> str:
        if not date_val:
            return ""
        s = str(date_val).strip()
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

    def _extract_date(self, bib: dict) -> str:
        # Prefer year then created_date
        y = (bib.get("year") or "").strip() if isinstance(bib.get("year"), str) else str(bib.get("year") or "")
        if y:
            d = self._norm_date(y)
            if d:
                return d
        cd = bib.get("created_date") or ""
        if isinstance(cd, str) and cd:
            return self._norm_date(cd[:10])
        return ""

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        base = "https://doaj.org/api/v2/search/articles/"
        query = kwargs.get("query", "") or ""
        page_size = int(kwargs.get("page_size", 100))
        max_pages = int(kwargs.get("max_pages", 10))

        out: list[dict] = []
        page = 1
        while page <= max_pages:
            url = f"{base}{requests.utils.quote(query)}"
            params = {"pageSize": page_size, "page": page}
            r = requests.get(url, params=params, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            results = js.get("results") or []
            if not results:
                break
            for item in results:
                bib = (item.get("bibjson") or {})
                title = (bib.get("title") or "").strip()
                abstract = (bib.get("abstract") or "").strip()
                doi = ""
                for iden in (bib.get("identifier") or []):
                    if (iden.get("type") or "").lower() == "doi":
                        doi = iden.get("id") or ""
                        break
                url = ""
                links = bib.get("link") or []
                if isinstance(links, list):
                    for ln in links:
                        if ln.get("type") == "fulltext" and ln.get("url"):
                            url = ln.get("url")
                            break
                    if not url and links:
                        url = links[0].get("url") or ""
                venue = ""
                j = bib.get("journal") or {}
                venue = j.get("title") or ""
                date = self._extract_date(bib)
                if date and not (day <= date < nextDay):
                    continue

                out.append(self._norm({
                    "id": doi or (item.get("id") or title[:40]),
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue or "DOAJ",
                    "date": date,
                    "source": self.name,
                }))
            page += 1
        return out
