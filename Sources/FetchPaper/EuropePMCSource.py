import requests
from .Source import Source

class EuropePMCSource(Source):
    """Europe PMC search (covers PubMed + many OA sources).

    Docs: https://europepmc.org/RestfulWebService
    Supports date range via PUB_DATE:[from TO to].
    """
    name = "Europe PMC"

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        base = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        page_size = int(kwargs.get("page_size", 100))
        max_pages = int(kwargs.get("max_pages", 10))
        query = kwargs.get("query", "") or ""

        q = f"PUB_DATE:[{day} TO {nextDay}]"
        if query:
            q = f"({q}) AND ({query})"

        params = {
            "query": q,
            "format": "json",
            "pageSize": page_size,
            "cursorMark": "*",
        }
        out: list[dict] = []
        for _ in range(max_pages):
            r = requests.get(base, params=params, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            res = (js.get("resultList") or {}).get("result") or []
            if not res:
                break
            for it in res:
                title = (it.get("title") or "").strip()
                abstract = (it.get("abstractText") or "").strip()
                doi = (it.get("doi") or "").strip()
                url = (it.get("fullTextUrlList", {}) or {}).get("fullTextUrl", [])
                link = ""
                if isinstance(url, list) and url:
                    link = url[0].get("url") or ""
                if not link:
                    link = it.get("pubUrl") or (f"https://doi.org/{doi}" if doi else "")
                venue = (it.get("journalTitle") or it.get("bookOrReportDetails", {}).get("publisher", "") or "").strip()
                date = (it.get("firstPublicationDate") or it.get("pubYear") or "").strip()
                out.append(self._norm({
                    "id": doi or it.get("id") or title[:40],
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": link,
                    "venue": venue,
                    "date": date[:10] if date else "",
                    "source": self.name,
                }))
            next_cursor = js.get("nextCursorMark")
            if not next_cursor or next_cursor == params["cursorMark"]:
                break
            params["cursorMark"] = next_cursor
        return out
