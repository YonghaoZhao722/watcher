#!/usr/bin/env python3
"""Single-run poll of a public Binance Smart Money trader's open positions."""
import json
import os
import sys
import urllib.request
from email.header import Header
from pathlib import Path

TID = "5193051957037235200"
BASE = "https://api.kopyon.com/v5/binance-smart-money/"
STATE = Path(os.environ.get("STATE_PATH", "state.json"))


def header_value(s: str) -> str:
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return Header(s, "utf-8").encode()


def get(ep, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    req = urllib.request.Request(
        BASE + ep + "?" + qs,
        headers={"X-API-KEY": os.environ["KOPYON_KEY"]},
    )
    return json.load(urllib.request.urlopen(req, timeout=30))["data"]


def snap():
    s = {}
    for m in ("UM", "CM"):
        d = get("openPositions", traderId=TID, marketType=m)
        for p in d.get("positions", []):
            s[f'{m}:{p["symbol"]}:{p["side"]}'] = {
                k: p.get(k)
                for k in (
                    "symbol",
                    "side",
                    "size",
                    "entryPrice",
                    "markPrice",
                    "leverage",
                    "unrealizedPnl",
                    "pnlCurrency",
                    "liquidationPrice",
                    "roi",
                )
            } | {"market": m}
    return s


def diff(old, new):
    ev = []
    for k, p in new.items():
        if k not in old:
            ev.append({"type": "OPENED", **p})
        elif abs((p["size"] or 0) - (old[k]["size"] or 0)) > 1e-9:
            ev.append(
                {
                    "type": "INCREASED" if p["size"] > old[k]["size"] else "DECREASED",
                    "prev_size": old[k]["size"],
                    **p,
                }
            )
    for k, p in old.items():
        if k not in new:
            ev.append({"type": "CLOSED", **p})
    return ev


def fmt(e):
    t = {"OPENED": "开仓", "INCREASED": "加仓", "DECREASED": "减仓", "CLOSED": "平仓"}[e["type"]]
    side = "多" if e["side"] == "LONG" else "空"
    return (
        f'{t} {e["symbol"]} {side} {e.get("leverage")}x\n'
        f'开仓价 {e.get("entryPrice")} 现价 {e.get("markPrice")}\n'
        f'仓位 {e.get("prev_size", "")}{"→" if "prev_size" in e else ""}{e.get("size")}'
        f'  浮盈亏 {round(e.get("unrealizedPnl") or 0, 4)} {e.get("pnlCurrency", "")}\n'
        f'强平 {e.get("liquidationPrice")}'
    )


def ntfy(title, body, priority="high"):
    topic = os.environ["NTFY_TOPIC"]
    req = urllib.request.Request(
        "https://ntfy.sh/" + topic,
        data=body.encode(),
        headers={
            "Title": header_value(title),
            "Priority": priority,
            "Tags": "chart_with_upwards_trend",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except Exception as e:
        # Avoid logging the topic, which is in the request URL.
        print(f"ntfy fail {type(e).__name__}", file=sys.stderr)
        sys.exit(1)


def main():
    if not os.environ.get("KOPYON_KEY") or not os.environ.get("NTFY_TOPIC"):
        print("missing required env", file=sys.stderr)
        sys.exit(1)
    new = snap()
    print(f"ok {len(new)} positions")
    old = json.loads(STATE.read_text()) if STATE.exists() else None
    if old is None:
        print("seed state, no notify")
    else:
        ev = diff(old, new)
        if ev:
            print(f"{len(ev)} events: " + ",".join(e["type"] for e in ev))
            ntfy("DianYuGe trade", "\n\n".join(fmt(e) for e in ev))
            print("ntfy ok")
    STATE.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n")
    if os.environ.get("SEND_TEST") == "1":
        ntfy(
            "GitHub Actions 监控已上线",
            "云端监控已开始运行，之后仓位变化会推送到这里。",
        )
        print("test ntfy ok")


if __name__ == "__main__":
    main()
