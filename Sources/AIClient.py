import json, requests, re

class GeminiClient:
    def __init__(self, ZOTERO_KEY:str, model:str):
        self.key = ZOTERO_KEY
        self.model = model
        self.base = "https://generativelanguage.googleapis.com/v1beta"

    def _call(self, prompt:str, temperature=0.2) -> str:
        url = f"{self.base}/{self.model}:generateContent?key={self.key}"
        body = {"contents":[{"role":"user","parts":[{"text":prompt}]}],
                "generationConfig":{"temperature":temperature}}
        r = requests.post(url, json=body, timeout=180)
        r.raise_for_status()
        data = r.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return ""

    def summarize_batch(self, items, personasNote:str, temperature=0.2):
        """items: list[dict{title, abstract, cluster_name}] -> fill summary/reason"""
        if not self.key: return items
        chunk = items  # 最小版就整批发
        papers="\n".join([f"{i+1}. title: {x['title']}\nabstract: {x.get('abstract','')[:1000]}"
                          for i,x in enumerate(chunk)])
        prompt=(f"You are a scholarly assistant.\nUser profile:\n{personasNote[:1000]}\n\n"
                f"For each paper, write a concise 2-3 sentence summary and one personalized reason in Chinese.\n"
                f"Return STRICT JSON array with keys: summary, reason. Order preserved.\n\nPAPERS:\n{papers}")
        txt=self._call(prompt, temperature=temperature)
        try:
            arr=json.loads(txt)
            for i,x in enumerate(chunk):
                if i<len(arr):
                    x["summary"]=(arr[i].get("summary","") or "")[:800]
                    x["reason"]=arr[i].get("reason","") or "Relevant to your profile"
        except Exception:
            # fallback: 保留原有摘要截断
            pass
        return items
