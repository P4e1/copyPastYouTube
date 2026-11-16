import json
from pathlib import Path

paths = [
    Path("/mnt/c/Users/P4EL/Downloads/chromewebdata.har"),
    Path("/mnt/c/Users/P4EL/Downloads") / "загрузка видео большого размера.har",
]
for path in paths:
    print("====", path.name, path.stat().st_size)
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["log"]["entries"]
    print("entries", len(entries))
    pages = data["log"].get("pages") or []
    for page in pages:
        print("page", page.get("title"), page.get("startedDateTime"))
    for entry in entries:
        req = entry["request"]
        res = entry["response"]
        url = req["url"]
        status = res["status"]
        method = req["method"]
        interesting = (
            status >= 400
            or status == 0
            or "moderat" in url.lower()
            or "complete" in url.lower()
            or "videos" in url.lower()
            or method == "PUT"
        )
        if not interesting:
            continue
        text = (res.get("content") or {}).get("text") or ""
        snippet = text.replace("\n", " ")[:240]
        print(f"{status} {method} {url[:220]}")
        if snippet:
            print("   ", snippet)
        if status == 0 or method == "PUT":
            timings = entry.get("timings") or {}
            print(
                "   time",
                entry.get("time"),
                "started",
                entry.get("startedDateTime"),
                "timings",
                {key: timings.get(key) for key in ("send", "wait", "receive", "blocked")},
            )
            post = req.get("postData") or {}
            print("   post", post.get("mimeType"), "text_len", len(post.get("text") or ""), "params", len(post.get("params") or []))
            print("   error", (res.get("_error") or entry.get("_error") or "")[:300])
