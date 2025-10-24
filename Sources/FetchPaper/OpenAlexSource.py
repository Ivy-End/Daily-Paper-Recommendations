import requests
from .Source import Source

class OpenAlexSource(Source):
    name = "OpenAlex"

    def Fetch(self, *, day:str, nextDay:str, **kwargs) -> list[dict]:
        perPage = kwargs.get("perPage", 200)
        maxPages = kwargs.get("maxPages", 6)
        params = {
            "filter"  : f"from_publication_date:{day}|{nextDay}",
            "sort"    : "publication_date:desc",
            "per-page": perPage,
            "cursor"  : "*",
        }

        items = []
        for _ in range(maxPages):
            r = requests.get("https://api.openalex.org/works", params = params, timeout = 60)
            r.raise_for_status()
            
            data=r.json()
            items += data.get("results", [])
            cur = (data.get("meta") or {}).get("next_cursor")
            if not cur: break
            params["cursor"] = cur

        out=[]
        for it in items:
            ab = it.get("abstract")
            if not ab:
                inv = it.get("abstract_inverted_index")
                if isinstance(inv, dict):
                    words=[]
                    for w, pos in inv.items():
                        words.extend([w]*len(pos))
                    ab = " ".join(words)
            doi=(it.get("doi") or "").replace("https://doi.org/","")
            url=f"https://doi.org/{doi}" if doi else (it.get("primary_location",{}).get("landing_page_url") or "")
            out.append(self._norm({
                "id": it.get("id",""),
                "title": it.get("title",""),
                "abstract": ab or "",
                "doi": doi,
                "url": url,
                "venue": (it.get("host_venue",{}) or {}).get("display_name",""),
                "date": it.get("publication_date",""),
                "source": self.name,
            }))
        return out
