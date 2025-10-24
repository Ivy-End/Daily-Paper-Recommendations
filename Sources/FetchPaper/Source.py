from abc import ABC, abstractmethod

class Source(ABC):
    name: str = "base"

    @abstractmethod
    def Fetch(self, *, day:str, nextDay:str, **kwargs) -> list[dict]:
        ...

    def _norm(self, item:dict) -> dict:
        return {
            "id": item.get("id",""),
            "title": (item.get("title") or "").strip(),
            "abstract": (item.get("abstract") or "").strip(),
            "doi": item.get("doi",""),
            "url": item.get("url",""),
            "venue": item.get("venue",""),
            "date": item.get("date",""),
            "source": item.get("source", self.name),
        }
