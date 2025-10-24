import requests
from .Source import Source

class PubMedSource(Source):
    name = "PubMed"

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        """Fetch PubMed records with publication date in [day, nextDay).

        Uses NCBI E-utilities (JSON): esearch (to get IDs) -> esummary (to get metadata).
        Docs: https://www.ncbi.nlm.nih.gov/books/NBK25499/
        """
        retmax = int(kwargs.get("retmax", 200))
        maxPages = int(kwargs.get("maxPages", 10))
        term = kwargs.get("term", "")  # optional term filter

        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        esearch_params = {
            "db": "pubmed",
            "retmode": "json",
            "sort": "pub+date",
            "datetype": "pdat",      # publication date
            "mindate": day,
            "maxdate": nextDay,
            "retmax": retmax,
            "retstart": 0,
        }
        if term:
            esearch_params["term"] = term

        all_ids: list[str] = []
        for _ in range(maxPages):
            r = requests.get(f"{base}/esearch.fcgi", params=esearch_params, timeout=60)
            r.raise_for_status()
            js = r.json()
            ids = (js.get("esearchresult", {}) or {}).get("idlist", [])
            if not ids:
                break
            all_ids.extend(ids)
            # pagination
            total = int((js.get("esearchresult", {}) or {}).get("count", "0"))
            esearch_params["retstart"] = int(esearch_params["retstart"]) + retmax
            if esearch_params["retstart"] >= total:
                break

        if not all_ids:
            return []

        out: list[dict] = []

        # Batch through esummary (up to ~500 IDs per call is OK)
        for i in range(0, len(all_ids), 50):
            chunk = all_ids[i : i + 50]
            summary_params = {
                "db": "pubmed",
                "retmode": "json",
                "id": ",".join(chunk),
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
            }
            r = requests.get(f"{base}/esummary.fcgi", params=summary_params, headers=headers, timeout=60)
            r.raise_for_status()
            js = r.json()
            result = js.get("result", {})
            uids = result.get("uids", [])
            for uid in uids:
                rec = result.get(uid, {})
                title = (rec.get("title") or "").strip()
                # Prefer ArticleIds for DOI
                doi = ""
                for aid in rec.get("articleids", []):
                    if (aid.get("idtype") or "").lower() == "doi":
                        doi = aid.get("value") or ""
                        break
                # URL: PubMed page
                url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
                # Venue / journal
                venue = (rec.get("fulljournalname") or rec.get("source") or "").strip()
                # Date
                date = (rec.get("pubdate") or "").strip()
                # Abstract is not in esummary; attempt short 'elocationid' or empty; users can follow URL
                abstract = rec.get("elocationid") or ""

                out.append(self._norm({
                    "id": uid,
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "venue": venue,
                    "date": date,
                    "source": self.name,
                }))

        return out
