import time
import requests
from datetime import datetime, timezone
from .Source import Source

def _to_epoch_ms(date_str: str) -> int:
    # date_str: 'YYYY-MM-DD' (UTC)
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def _from_epoch_ms(ms: int) -> str:
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date().isoformat()
    except Exception:
        return ""

class OpenReviewSource(Source):
    """OpenReview REST fetcher.

    Primary endpoint: https://api.openreview.net/notes
    - Supports pagination via 'limit' and 'offset'.
    - We'll attempt server-side time window using ('mintcdate','maxtcdate') or ('mindate','maxdate'),
      and fall back to client-side filtering by 'cdate' (creation time in ms).
    Optional kwargs:
      invitations: list[str]  # filter specific venues/invitations (e.g., 'ICLR.cc/2025/Conference/-/Submission')
      query: str              # free text (best-effort; used with /notes/search if available)
      page_size: int          # default 100
      max_pages: int          # default 10
      details: str            # e.g., 'replyCount' or 'forumContent'; default ''
    Output fields: id/title/abstract/doi/url/venue/date/source
    """
    name = "OpenReview"

    BASE = "https://api.openreview.net"

    def _server_window_params(self, day: str, nextDay: str) -> list[dict]:
        """Try multiple param styles for time-window. Return candidates in order."""
        start_ms = _to_epoch_ms(day)
        end_ms   = _to_epoch_ms(nextDay)
        return [
            {"mintcdate": start_ms, "maxtcdate": end_ms},  # tcdate (creation)
            {"mindate": start_ms,   "maxdate": end_ms},    # older alias on some deployments
        ]

    def _in_range(self, cdate_ms: int, day: str, nextDay: str) -> bool:
        if not isinstance(cdate_ms, (int, float)):
            return False
        d = _from_epoch_ms(int(cdate_ms))
        return bool(d and (day <= d < nextDay))

    def _extract_fields(self, note: dict) -> dict:
        content = note.get("content") or {}
        title = (content.get("title") or content.get("paper_title") or content.get("name") or "").strip()
        abstract = (content.get("abstract") or content.get("TL;DR") or content.get("summary") or "").strip()
        venue = (note.get("venue") or note.get("venueid") or note.get("invitation") or "OpenReview")
        url = ""
        forum = note.get("forum") or note.get("id")
        if forum:
            url = f"https://openreview.net/forum?id={forum}"
        date = _from_epoch_ms(note.get("cdate") or 0)
        return {
            "id": note.get("id") or (title[:40] if title else ""),
            "title": title,
            "abstract": abstract,
            "doi": "",  # OpenReview typically doesn't assign DOI at note level
            "url": url,
            "venue": venue,
            "date": date,
        }

    def Fetch(self, *, day: str, nextDay: str, **kwargs) -> list[dict]:
        invitations = kwargs.get("invitations") or []
        if isinstance(invitations, str):
            invitations = [invitations]
        query = kwargs.get("query") or ""
        page_size = int(kwargs.get("page_size", 100))
        max_pages = int(kwargs.get("max_pages", 10))
        details = kwargs.get("details", "")

        out: list[dict] = []

        # Strategy 1: If query is provided, prefer /notes/search (best-effort).
        # If endpoint not available, fall back to /notes.
        def _try_search(params_extra: dict) -> tuple[bool, list[dict]]:
            base = f"{self.BASE}/notes/search"
            params = {"limit": page_size, "offset": 0, "term": query}
            params.update(params_extra)
            if details:
                params["details"] = details
            collected: list[dict] = []
            for _ in range(max_pages):
                r = requests.get(base, params=params, timeout=60)
                if r.status_code != 200:
                    return False, []
                js = r.json()
                notes = js.get("notes") or js.get("results") or []
                if not notes:
                    break
                for n in notes:
                    if not self._in_range(n.get("cdate") or 0, day, nextDay):
                        continue
                    if invitations:
                        inv = (n.get("invitation") or "")
                        if inv not in invitations:
                            continue
                    f = self._extract_fields(n)
                    collected.append(self._norm({**f, "source": self.name}))
                if len(notes) < page_size:
                    break
                params["offset"] = int(params["offset"]) + page_size
            return True, collected

        # Strategy 2: /notes with server-side window params; if rejected, fall back to client filter.
        def _try_notes(params_extra: dict) -> tuple[bool, list[dict]]:
            base = f"{self.BASE}/notes"
            params = {"limit": page_size, "offset": 0, "sort": "desc"}
            params.update(params_extra)
            if details:
                params["details"] = details
            collected: list[dict] = []
            for _ in range(max_pages):
                r = requests.get(base, params=params, timeout=60)
                if r.status_code != 200:
                    return False, []
                js = r.json()
                notes = js.get("notes") or js.get("results") or []
                if not notes:
                    break
                for n in notes:
                    # Client-side filter by time and invitation
                    if not self._in_range(n.get("cdate") or 0, day, nextDay):
                        continue
                    if invitations:
                        inv = (n.get("invitation") or "")
                        if inv not in invitations:
                            continue
                    f = self._extract_fields(n)
                    collected.append(self._norm({**f, "source": self.name}))
                if len(notes) < page_size:
                    break
                params["offset"] = int(params["offset"]) + page_size
            return True, collected

        # Try search if query provided
        if query:
            for win in self._server_window_params(day, nextDay):
                ok, items = _try_search(win)
                if ok and items:
                    out.extend(items)
                    return out

        # Try notes with server-side window
        for win in self._server_window_params(day, nextDay):
            ok, items = _try_notes(win)
            if ok and items:
                out.extend(items)
                return out

        # Fallback: paginate recent notes (no server window), filter locally
        ok, items = _try_notes({})
        if ok:
            out.extend(items)
        return out
