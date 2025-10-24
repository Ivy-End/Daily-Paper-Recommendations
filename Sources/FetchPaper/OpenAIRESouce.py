import requests
from .Source import Source

class OpenAIRESouce(Source):
    """OpenAIRE publications search.

    Docs: https://api.openaire.eu/ (public)
    We'll use /search/publications with JSON output and date window.
    """
    name = "OpenAIRE"

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        base = "https://api.openaire.eu/search/publications"
        page_size = int(kwargs.get("page_size", 100))
        maxPages = int(kwargs.get("maxPages", 10))
        query = kwargs.get("query", "")  # free-text query

        params = {
            "format": "json",
            "fromDate": day,
            "toDate": nextDay,
            "size": page_size,
            "page": 1,
        }
        if query:
            params["title"] = query  # OpenAIRE supports fielded params; keep minimal

        out: list[dict] = []
        for _ in range(maxPages):
            r = requests.get(base, params=params, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            results = ((js.get("response") or {}).get("results") or {}).get("result") or []
            if not results:
                break
            for item in results:
                # Structure: item['metadata']['oaf:entity']['oaf:result']
                md = (item.get("metadata") or {}).get("oaf:entity") or {}
                res = md.get("oaf:result") or {}
                title = ""
                t = res.get("title") or {}
                if isinstance(t, dict):
                    title = (t.get("$") or "").strip()
                elif isinstance(t, str):
                    title = t.strip()

                abstract = ""
                desc = res.get("description") or {}
                if isinstance(desc, dict):
                    abstract = (desc.get("$") or "").strip()
                elif isinstance(desc, str):
                    abstract = desc.strip()

                doi = ""
                pid = res.get("pid") or []
                if isinstance(pid, dict):
                    pid = [pid]
                if isinstance(pid, list):
                    for p in pid:
                        if (p.get("@type") or "").lower() == "doi":
                            doi = (p.get("$") or "").strip()
                            break

                url = ""
                bestid = res.get("bestaccessright") or {}
                # try originalId as link
                original_ids = res.get("originalId") or []
                if isinstance(original_ids, dict):
                    original_ids = [original_ids]
                if isinstance(original_ids, list) and original_ids:
                    # choose the first URL-looking id
                    for oid in original_ids:
                        val = (oid.get("$") or "")
                        if isinstance(val, str) and val.startswith("http"):
                            url = val
                            break
                if not url and doi:
                    url = f"https://doi.org/{doi}"

                venue = ""
                pj = res.get("publisher") or res.get("journal") or ""
                if isinstance(pj, dict):
                    venue = pj.get("$") or ""
                elif isinstance(pj, str):
                    venue = pj

                date = ""
                for key in ("dateofacceptance", "publicationdate", "collectedfromdate"):
                    d = res.get(key) or {}
                    if isinstance(d, dict) and d.get("$"):
                        date = d["$"][:10]
                        break
                    if isinstance(d, str) and d:
                        date = d[:10]
                        break

                out.append(self._norm({
                    "id": doi or (title[:40] if title else ""),
                    "title": title or "",
                    "abstract": abstract or "",
                    "doi": doi,
                    "url": url or "",
                    "venue": (venue or "OpenAIRE").strip(),
                    "date": date,
                    "source": self.name,
                }))

            params["page"] = int(params["page"]) + 1

        return out
