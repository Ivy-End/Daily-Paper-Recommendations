import requests
from .Source import Source

class CrossrefSource(Source):
    name = "Crossref"

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        """Fetch Crossref works in [day, nextDay)."""
        rows = int(kwargs.get("rows", 200))
        maxPages = int(kwargs.get("maxPages", 10))

        params = {
            "filter": f"from-pub-date:{day},until-pub-date:{nextDay}",
            "sort": "published",
            "order": "desc",
            "rows": rows,
            "cursor": "*",
        }
        out: list[dict] = []
        for _ in range(maxPages):
            r = requests.get("https://api.crossref.org/works", params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            items = (data.get("message") or {}).get("items", [])
            for it in items:
                doi = (it.get("DOI") or "").lower()
                url = it.get("URL") or (f"https://doi.org/{doi}" if doi else "")
                title = ""
                t = it.get("title")
                if isinstance(t, list) and t:
                    title = t[0]
                elif isinstance(t, str):
                    title = t
                abstract = (it.get("abstract") or "").replace("\n", " ").strip()
                # venue: container-title
                venue = ""
                ct = it.get("container-title")
                if isinstance(ct, list) and ct:
                    venue = ct[0]
                elif isinstance(ct, str):
                    venue = ct
                # date: choose published-print or published-online or issued
                date = ""
                for key in ("published-print", "published-online", "issued"):
                    d = it.get(key) or {}
                    parts = d.get("date-parts") or []
                    if parts and parts[0]:
                        # YYYY-MM-DD if available
                        dp = parts[0]
                        if len(dp) >= 3:
                            date = f"{dp[0]:04d}-{dp[1]:02d}-{dp[2]:02d}"
                        elif len(dp) == 2:
                            date = f"{dp[0]:04d}-{dp[1]:02d}-01"
                        else:
                            date = f"{dp[0]:04d}-01-01"
                        break

                out.append(self._norm({
                    "id": doi or url or title[:40],
                    "title": title or "",
                    "abstract": abstract or "",
                    "doi": doi,
                    "url": url,
                    "venue": venue,
                    "date": date,
                    "source": self.name,
                }))

            cur = (data.get("message") or {}).get("next-cursor")
            if not cur:
                break
            params["cursor"] = cur

        return out
