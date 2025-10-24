from .Source import Source

class Aggregator:
    def __init__(self, sources:list[Source]):
        self.sources = sources

    def fetch_all(self, *, day:str, nextDay:str, **kwargs) -> list[dict]:
        piles=[]
        for s in self.sources:
            try:
                piles.append(s.Fetch(day=day, nextDay=nextDay, **kwargs.get(s.name, {})))
            except Exception as e:
                print(f"[Aggregator] {s.name} error:", e)
        # 去重
        seen=set(); merged=[]
        def key_of(x):
            if x.get("doi"): return "doi:"+x["doi"].lower()
            if x.get("id"):  return x["id"]
            return "t:"+x.get("title","")[:120].lower()+"|d:"+x.get("date","")
        for lst in piles:
            for it in lst:
                k=key_of(it)
                if k in seen: continue
                seen.add(k); merged.append(it)
        return merged
