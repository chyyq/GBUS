from __future__ import annotations

import json
import math
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "docs" / "data" / "latest.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
YAHOO_SEARCH = "https://query1.finance.yahoo.com/v1/finance/search"
NASDAQ_SCREENER = "https://api.nasdaq.com/api/screener/stocks"
X_PROFILE_URL = "https://x.com/aleabitoreddit"

MARKET_SYMBOLS = [
    "SPY",
    "QQQ",
    "^VIX",
    "SMH",
    "IGV",
    "CIBR",
    "HACK",
    "XBI",
    "XLK",
    "XLY",
    "XLV",
    "XLF",
    "XLE",
    "IWM",
]

UNIVERSE = [
    {"symbol": "AAPL", "name": "Apple", "sector": "Technology", "theme": "Mega-cap platform", "proxy": "QQQ"},
    {"symbol": "MSFT", "name": "Microsoft", "sector": "Technology", "theme": "Cloud and AI", "proxy": "QQQ"},
    {"symbol": "NVDA", "name": "NVIDIA", "sector": "Technology", "theme": "AI infrastructure", "proxy": "SMH"},
    {"symbol": "AVGO", "name": "Broadcom", "sector": "Technology", "theme": "Semiconductors", "proxy": "SMH"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology", "theme": "Semiconductors", "proxy": "SMH"},
    {"symbol": "QCOM", "name": "Qualcomm", "sector": "Technology", "theme": "Semiconductors", "proxy": "SMH"},
    {"symbol": "TSM", "name": "Taiwan Semiconductor", "sector": "Technology", "theme": "Semiconductors", "proxy": "SMH"},
    {"symbol": "ASML", "name": "ASML", "sector": "Technology", "theme": "Semiconductor equipment", "proxy": "SMH"},
    {"symbol": "AMAT", "name": "Applied Materials", "sector": "Technology", "theme": "Semiconductor equipment", "proxy": "SMH"},
    {"symbol": "LRCX", "name": "Lam Research", "sector": "Technology", "theme": "Semiconductor equipment", "proxy": "SMH"},
    {"symbol": "KLAC", "name": "KLA", "sector": "Technology", "theme": "Semiconductor equipment", "proxy": "SMH"},
    {"symbol": "MU", "name": "Micron", "sector": "Technology", "theme": "Memory", "proxy": "SMH"},
    {"symbol": "MRVL", "name": "Marvell", "sector": "Technology", "theme": "AI networking", "proxy": "SMH"},
    {"symbol": "ARM", "name": "Arm", "sector": "Technology", "theme": "Semiconductors", "proxy": "SMH"},
    {"symbol": "SMCI", "name": "Super Micro Computer", "sector": "Technology", "theme": "AI servers", "proxy": "SMH"},
    {"symbol": "ANET", "name": "Arista Networks", "sector": "Technology", "theme": "AI networking", "proxy": "QQQ"},
    {"symbol": "ORCL", "name": "Oracle", "sector": "Technology", "theme": "Cloud software", "proxy": "IGV"},
    {"symbol": "CRM", "name": "Salesforce", "sector": "Technology", "theme": "Enterprise software", "proxy": "IGV"},
    {"symbol": "NOW", "name": "ServiceNow", "sector": "Technology", "theme": "Enterprise software", "proxy": "IGV"},
    {"symbol": "ADBE", "name": "Adobe", "sector": "Technology", "theme": "Software", "proxy": "IGV"},
    {"symbol": "PANW", "name": "Palo Alto Networks", "sector": "Technology", "theme": "Cybersecurity", "proxy": "CIBR"},
    {"symbol": "CRWD", "name": "CrowdStrike", "sector": "Technology", "theme": "Cybersecurity", "proxy": "CIBR"},
    {"symbol": "ZS", "name": "Zscaler", "sector": "Technology", "theme": "Cybersecurity", "proxy": "CIBR"},
    {"symbol": "NET", "name": "Cloudflare", "sector": "Technology", "theme": "Cloud infrastructure", "proxy": "IGV"},
    {"symbol": "DDOG", "name": "Datadog", "sector": "Technology", "theme": "Cloud monitoring", "proxy": "IGV"},
    {"symbol": "SNOW", "name": "Snowflake", "sector": "Technology", "theme": "Data cloud", "proxy": "IGV"},
    {"symbol": "PLTR", "name": "Palantir", "sector": "Technology", "theme": "AI software", "proxy": "IGV"},
    {"symbol": "APP", "name": "AppLovin", "sector": "Technology", "theme": "AI advertising", "proxy": "IGV"},
    {"symbol": "INTU", "name": "Intuit", "sector": "Technology", "theme": "Software", "proxy": "IGV"},
    {"symbol": "SHOP", "name": "Shopify", "sector": "Technology", "theme": "Commerce software", "proxy": "IGV"},
    {"symbol": "GOOGL", "name": "Alphabet", "sector": "Communication Services", "theme": "AI platform", "proxy": "QQQ"},
    {"symbol": "META", "name": "Meta Platforms", "sector": "Communication Services", "theme": "AI platform", "proxy": "QQQ"},
    {"symbol": "NFLX", "name": "Netflix", "sector": "Communication Services", "theme": "Streaming", "proxy": "XLY"},
    {"symbol": "DIS", "name": "Disney", "sector": "Communication Services", "theme": "Media", "proxy": "XLY"},
    {"symbol": "RDDT", "name": "Reddit", "sector": "Communication Services", "theme": "Social media", "proxy": "QQQ"},
    {"symbol": "AMZN", "name": "Amazon", "sector": "Consumer Discretionary", "theme": "Cloud and retail", "proxy": "XLY"},
    {"symbol": "TSLA", "name": "Tesla", "sector": "Consumer Discretionary", "theme": "EV and autonomy", "proxy": "XLY"},
    {"symbol": "UBER", "name": "Uber", "sector": "Consumer Discretionary", "theme": "Mobility platform", "proxy": "XLY"},
    {"symbol": "ABNB", "name": "Airbnb", "sector": "Consumer Discretionary", "theme": "Travel platform", "proxy": "XLY"},
    {"symbol": "BKNG", "name": "Booking Holdings", "sector": "Consumer Discretionary", "theme": "Travel", "proxy": "XLY"},
    {"symbol": "MELI", "name": "MercadoLibre", "sector": "Consumer Discretionary", "theme": "E-commerce", "proxy": "XLY"},
    {"symbol": "COST", "name": "Costco", "sector": "Consumer Staples", "theme": "Quality retail", "proxy": "XLY"},
    {"symbol": "HD", "name": "Home Depot", "sector": "Consumer Discretionary", "theme": "Retail", "proxy": "XLY"},
    {"symbol": "MCD", "name": "McDonald's", "sector": "Consumer Discretionary", "theme": "Restaurants", "proxy": "XLY"},
    {"symbol": "SBUX", "name": "Starbucks", "sector": "Consumer Discretionary", "theme": "Restaurants", "proxy": "XLY"},
    {"symbol": "CMG", "name": "Chipotle", "sector": "Consumer Discretionary", "theme": "Restaurants", "proxy": "XLY"},
    {"symbol": "LULU", "name": "Lululemon", "sector": "Consumer Discretionary", "theme": "Premium retail", "proxy": "XLY"},
    {"symbol": "NKE", "name": "Nike", "sector": "Consumer Discretionary", "theme": "Apparel", "proxy": "XLY"},
    {"symbol": "V", "name": "Visa", "sector": "Financials", "theme": "Payments", "proxy": "XLF"},
    {"symbol": "MA", "name": "Mastercard", "sector": "Financials", "theme": "Payments", "proxy": "XLF"},
    {"symbol": "AXP", "name": "American Express", "sector": "Financials", "theme": "Payments", "proxy": "XLF"},
    {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Financials", "theme": "Banks", "proxy": "XLF"},
    {"symbol": "BAC", "name": "Bank of America", "sector": "Financials", "theme": "Banks", "proxy": "XLF"},
    {"symbol": "GS", "name": "Goldman Sachs", "sector": "Financials", "theme": "Capital markets", "proxy": "XLF"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "Financials", "theme": "Capital markets", "proxy": "XLF"},
    {"symbol": "BLK", "name": "BlackRock", "sector": "Financials", "theme": "Asset management", "proxy": "XLF"},
    {"symbol": "COIN", "name": "Coinbase", "sector": "Financials", "theme": "Digital assets", "proxy": "XLF"},
    {"symbol": "HOOD", "name": "Robinhood", "sector": "Financials", "theme": "Brokerage", "proxy": "XLF"},
    {"symbol": "LLY", "name": "Eli Lilly", "sector": "Health Care", "theme": "Pharma growth", "proxy": "XLV"},
    {"symbol": "UNH", "name": "UnitedHealth", "sector": "Health Care", "theme": "Managed care", "proxy": "XLV"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Health Care", "theme": "Defensive health care", "proxy": "XLV"},
    {"symbol": "MRK", "name": "Merck", "sector": "Health Care", "theme": "Pharma", "proxy": "XLV"},
    {"symbol": "ABBV", "name": "AbbVie", "sector": "Health Care", "theme": "Pharma", "proxy": "XLV"},
    {"symbol": "TMO", "name": "Thermo Fisher", "sector": "Health Care", "theme": "Life sciences", "proxy": "XLV"},
    {"symbol": "ISRG", "name": "Intuitive Surgical", "sector": "Health Care", "theme": "Medtech", "proxy": "XLV"},
    {"symbol": "VRTX", "name": "Vertex", "sector": "Health Care", "theme": "Biotech", "proxy": "XBI"},
    {"symbol": "REGN", "name": "Regeneron", "sector": "Health Care", "theme": "Biotech", "proxy": "XBI"},
    {"symbol": "MRNA", "name": "Moderna", "sector": "Health Care", "theme": "Biotech", "proxy": "XBI"},
    {"symbol": "GE", "name": "GE Aerospace", "sector": "Industrials", "theme": "Aerospace", "proxy": "IWM"},
    {"symbol": "CAT", "name": "Caterpillar", "sector": "Industrials", "theme": "Machinery", "proxy": "IWM"},
    {"symbol": "DE", "name": "Deere", "sector": "Industrials", "theme": "Machinery", "proxy": "IWM"},
    {"symbol": "BA", "name": "Boeing", "sector": "Industrials", "theme": "Aerospace", "proxy": "IWM"},
    {"symbol": "RTX", "name": "RTX", "sector": "Industrials", "theme": "Defense", "proxy": "IWM"},
    {"symbol": "HON", "name": "Honeywell", "sector": "Industrials", "theme": "Industrial tech", "proxy": "IWM"},
    {"symbol": "XOM", "name": "Exxon Mobil", "sector": "Energy", "theme": "Energy", "proxy": "XLE"},
    {"symbol": "CVX", "name": "Chevron", "sector": "Energy", "theme": "Energy", "proxy": "XLE"},
    {"symbol": "SLB", "name": "SLB", "sector": "Energy", "theme": "Oil services", "proxy": "XLE"},
    {"symbol": "LIN", "name": "Linde", "sector": "Materials", "theme": "Industrial gases", "proxy": "IWM"},
    {"symbol": "FCX", "name": "Freeport-McMoRan", "sector": "Materials", "theme": "Copper", "proxy": "IWM"},
    {"symbol": "NEM", "name": "Newmont", "sector": "Materials", "theme": "Gold", "proxy": "IWM"},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def req_json(url: str, headers: dict[str, str] | None = None, attempts: int = 3) -> dict:
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        request_headers.update(headers)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(req, timeout=25) as response:
                body = response.read().decode("utf-8", "ignore")
            return json.loads(body)
        except Exception as exc:  # noqa: BLE001 - intentionally surfaced in data file.
            last_error = exc
            time.sleep(0.45 * (attempt + 1))
    raise last_error or RuntimeError("unknown request error")


def safe_num(value):
    if value is None:
        return None
    try:
        result = float(value)
        if math.isfinite(result):
            return result
    except (TypeError, ValueError):
        return None
    return None


def round_num(value, digits=2):
    value = safe_num(value)
    return round(value, digits) if value is not None else None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def parse_market_cap(value: str | None):
    if not value:
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    return safe_num(text)


def get_chart(symbol: str) -> dict:
    encoded = urllib.parse.quote(symbol, safe="")
    url = f"{YAHOO_CHART}/{encoded}?range=1y&interval=1d&includePrePost=false&events=div%2Csplits"
    data = req_json(url)
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result or not result.get("timestamp"):
        raise RuntimeError(f"no chart data for {symbol}")
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    adjusted = ((result.get("indicators", {}).get("adjclose") or [{}])[0]).get("adjclose") or []
    bars = []
    for idx, timestamp in enumerate(result["timestamp"]):
        close = safe_num(adjusted[idx] if idx < len(adjusted) else None)
        if close is None:
            close = safe_num((quote.get("close") or [None])[idx])
        bar = {
            "date": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
            "open": safe_num((quote.get("open") or [None])[idx]),
            "high": safe_num((quote.get("high") or [None])[idx]),
            "low": safe_num((quote.get("low") or [None])[idx]),
            "close": close,
            "volume": safe_num((quote.get("volume") or [0])[idx]) or 0,
        }
        if all(bar[k] is not None for k in ("open", "high", "low", "close")):
            bars.append(bar)
    if len(bars) < 40:
        raise RuntimeError(f"too few bars for {symbol}")
    return {"symbol": symbol, "bars": bars, "meta": result.get("meta") or {}}


def get_nasdaq_meta(symbols: set[str], errors: list[str]) -> dict[str, dict]:
    meta: dict[str, dict] = {}
    headers = {
        "Origin": "https://www.nasdaq.com",
        "Referer": "https://www.nasdaq.com/market-activity/stocks/screener",
    }
    for exchange in ("NASDAQ", "NYSE", "AMEX"):
        url = f"{NASDAQ_SCREENER}?tableonly=true&limit=8000&exchange={exchange}"
        try:
            data = req_json(url, headers=headers, attempts=2)
            rows = data.get("data", {}).get("table", {}).get("rows") or []
            for row in rows:
                symbol = str(row.get("symbol", "")).upper()
                if symbol in symbols:
                    meta[symbol] = {
                        "name": row.get("name"),
                        "marketCap": parse_market_cap(row.get("marketCap")),
                        "lastSale": parse_market_cap(row.get("lastsale")),
                        "exchange": exchange,
                    }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Nasdaq {exchange} metadata failed: {exc}")
    return meta


def get_news(query: str, count: int = 5) -> list[dict]:
    url = f"{YAHOO_SEARCH}?q={urllib.parse.quote(query)}&quotesCount=0&newsCount={count}"
    data = req_json(url, attempts=2)
    news = []
    for item in (data.get("news") or [])[:count]:
        timestamp = item.get("providerPublishTime")
        news.append(
            {
                "title": item.get("title"),
                "publisher": item.get("publisher") or "Yahoo Finance",
                "link": item.get("link"),
                "publishedAt": datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")
                if timestamp
                else None,
                "relatedTickers": item.get("relatedTickers") or [],
            }
        )
    return news


def get_serenity_summary() -> dict:
    token = os.environ.get("X_BEARER_TOKEN")
    if not token:
        return {
            "status": "needs_token",
            "source": "X API v2",
            "profileUrl": X_PROFILE_URL,
            "updatedAt": now_iso(),
            "summary": [
                "GitHub Actions 未配置 X_BEARER_TOKEN，无法稳定读取 X 登录内容。",
                "配置仓库 Secret 后，脚本会每日拉取 @aleabitoreddit 最新推文并生成摘要。",
            ],
            "posts": [],
        }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        user = req_json(
            "https://api.twitter.com/2/users/by/username/aleabitoreddit?user.fields=description,verified",
            headers=headers,
            attempts=2,
        )
        user_id = user.get("data", {}).get("id")
        if not user_id:
            raise RuntimeError("X user not found")
        timeline = req_json(
            f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=10&tweet.fields=created_at,public_metrics&exclude=replies,retweets",
            headers=headers,
            attempts=2,
        )
        posts = []
        for tweet in (timeline.get("data") or [])[:6]:
            posts.append(
                {
                    "id": tweet.get("id"),
                    "text": tweet.get("text"),
                    "createdAt": tweet.get("created_at"),
                    "url": f"https://x.com/aleabitoreddit/status/{tweet.get('id')}",
                    "metrics": tweet.get("public_metrics") or {},
                }
            )
        return {
            "status": "ok",
            "source": "X API v2",
            "profileUrl": X_PROFILE_URL,
            "updatedAt": now_iso(),
            "summary": summarize_posts([p["text"] for p in posts if p.get("text")]),
            "posts": posts,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "source": "X API v2",
            "profileUrl": X_PROFILE_URL,
            "updatedAt": now_iso(),
            "summary": [f"X 更新失败：{exc}"],
            "posts": [],
        }


def summarize_posts(texts: list[str]) -> list[str]:
    if not texts:
        return ["暂无可摘要内容。"]
    joined = " ".join(texts)
    tickers = []
    for token in joined.replace("\n", " ").split(" "):
        if token.startswith("$") and 2 <= len(token) <= 7 and token[1:].isalpha():
            ticker = token.upper().strip(".,;:!?")
            if ticker not in tickers:
                tickers.append(ticker)
    keywords = [
        word
        for word in ["AI", "NVDA", "semiconductor", "earnings", "breakout", "market", "risk", "rate", "Bitcoin", "crypto"]
        if word.lower() in joined.lower()
    ]
    bullets = []
    if tickers:
        bullets.append(f"最新内容重点提到 {', '.join(tickers[:8])}。")
    if keywords:
        bullets.append(f"高频主题包括 {', '.join(keywords[:6])}。")
    bullets.append(texts[0][:180] + ("..." if len(texts[0]) > 180 else ""))
    return bullets


def values(bars: list[dict], key: str) -> list[float]:
    return [bar[key] for bar in bars if safe_num(bar.get(key)) is not None]


def sma(series: list[float], period: int, end_idx: int | None = None):
    if end_idx is None:
        end_idx = len(series) - 1
    if end_idx + 1 < period:
        return None
    segment = series[end_idx - period + 1 : end_idx + 1]
    return statistics.fmean(segment) if len(segment) == period else None


def pct_return(closes: list[float], days: int):
    if len(closes) <= days:
        return None
    base = closes[-days - 1]
    return closes[-1] / base - 1 if base else None


def avg(series: list[float]):
    clean = [x for x in series if safe_num(x) is not None]
    return statistics.fmean(clean) if clean else None


def max_last(series: list[float], period: int, exclude_last=False):
    end = len(series) - 1 if exclude_last else len(series)
    segment = [x for x in series[max(0, end - period) : end] if safe_num(x) is not None]
    return max(segment) if segment else None


def min_last(series: list[float], period: int):
    segment = [x for x in series[-period:] if safe_num(x) is not None]
    return min(segment) if segment else None


def atr(bars: list[dict], period: int = 14):
    if len(bars) <= period:
        return None
    ranges = []
    for idx in range(max(1, len(bars) - period), len(bars)):
        bar = bars[idx]
        prev = bars[idx - 1]["close"]
        ranges.append(max(bar["high"] - bar["low"], abs(bar["high"] - prev), abs(bar["low"] - prev)))
    return avg(ranges)


def rsi(closes: list[float], period: int = 14):
    if len(closes) <= period:
        return None
    gains = 0.0
    losses = 0.0
    for idx in range(len(closes) - period, len(closes)):
        delta = closes[idx] - closes[idx - 1]
        if delta >= 0:
            gains += delta
        else:
            losses += abs(delta)
    if losses == 0:
        return 100.0
    rs = (gains / period) / (losses / period)
    return 100 - 100 / (1 + rs)


def estimate_beta(stock_bars: list[dict], bench_bars: list[dict], days: int = 126):
    stock = values(stock_bars, "close")
    bench = values(bench_bars or [], "close")
    count = min(days, len(stock) - 1, len(bench) - 1)
    if count < 40:
        return None
    stock_returns = []
    bench_returns = []
    for idx in range(count):
        si = len(stock) - count + idx
        bi = len(bench) - count + idx
        stock_returns.append(stock[si] / stock[si - 1] - 1)
        bench_returns.append(bench[bi] / bench[bi - 1] - 1)
    stock_avg = avg(stock_returns)
    bench_avg = avg(bench_returns)
    covariance = sum((stock_returns[i] - stock_avg) * (bench_returns[i] - bench_avg) for i in range(count))
    variance = sum((bench_returns[i] - bench_avg) ** 2 for i in range(count))
    return covariance / variance if variance else None


def percentile(value, series: list[float]):
    clean = sorted([x for x in series if safe_num(x) is not None])
    if safe_num(value) is None or not clean:
        return 50.0
    less_equal = sum(1 for x in clean if x <= value)
    return clamp(less_equal / len(clean) * 100, 0, 100)


def days_until(date_text: str | None):
    if not date_text:
        return None
    try:
        target = datetime.fromisoformat(date_text[:10]).date()
    except ValueError:
        return None
    return (target - datetime.now(timezone.utc).date()).days


def add_business_days(date_text: str, days: int) -> str:
    cursor = datetime.fromisoformat(date_text).date()
    added = 0
    while added < days:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            added += 1
    return cursor.isoformat()


def build_metric(base: dict, chart: dict, meta: dict, benchmarks: dict) -> dict | None:
    bars = chart.get("bars") or []
    if len(bars) < 80:
        return None
    closes = values(bars, "close")
    highs = values(bars, "high")
    lows = values(bars, "low")
    volumes = values(bars, "volume")
    last = bars[-1]
    prev = bars[-2]
    ma20 = sma(closes, 20)
    ma50 = sma(closes, 50)
    ma150 = sma(closes, 150)
    ma200 = sma(closes, 200)
    ma50_past = sma(closes, 50, len(closes) - 21) if len(closes) >= 70 else None
    avg_volume20 = avg(volumes[-20:])
    avg_dollar20 = avg([bar["close"] * bar["volume"] for bar in bars[-20:]])
    atr14 = atr(bars)
    ret1m = pct_return(closes, 21)
    ret3m = pct_return(closes, 63)
    ret6m = pct_return(closes, 126)
    spy_closes = values((benchmarks.get("SPY") or {}).get("bars") or [], "close")
    qqq_closes = values((benchmarks.get("QQQ") or {}).get("bars") or [], "close")
    spy_ret3m = pct_return(spy_closes, 63)
    spy_ret6m = pct_return(spy_closes, 126)
    qqq_ret1m = pct_return(qqq_closes, 21)
    qqq_ret3m = pct_return(qqq_closes, 63)
    beta = estimate_beta(bars, (benchmarks.get("SPY") or {}).get("bars") or [])
    return {
        "symbol": base["symbol"],
        "name": meta.get("name") or base["name"],
        "sector": base["sector"],
        "industry": None,
        "theme": base["theme"],
        "proxy": base["proxy"],
        "exchange": meta.get("exchange"),
        "sourceUrl": f"https://finance.yahoo.com/quote/{urllib.parse.quote(base['symbol'])}",
        "bars": bars,
        "close": last["close"],
        "open": last["open"],
        "high": last["high"],
        "low": last["low"],
        "previousClose": prev["close"],
        "volume": last["volume"],
        "avgVolume20": avg_volume20,
        "dollarVolumeToday": last["close"] * last["volume"],
        "avgDollarVolume20": avg_dollar20,
        "marketCap": meta.get("marketCap"),
        "beta": beta,
        "ma20": ma20,
        "ma50": ma50,
        "ma150": ma150,
        "ma200": ma200,
        "ma50Slope20d": ma50 / ma50_past - 1 if ma50 and ma50_past else None,
        "atr14": atr14,
        "atrPct": atr14 / last["close"] if atr14 else None,
        "rsi14": rsi(closes),
        "high20Prev": max_last(highs, 20, True),
        "high60Prev": max_last(highs, 60, True),
        "high52w": max_last(highs, 252),
        "low52w": min_last(lows, 252),
        "volumeRatio20": last["volume"] / avg_volume20 if avg_volume20 else None,
        "ret1m": ret1m,
        "ret3m": ret3m,
        "ret6m": ret6m,
        "dailyGain": last["close"] / last["open"] - 1 if last["open"] else None,
        "gapUp": last["open"] / prev["close"] - 1 if prev["close"] else None,
        "rs1mQqq": ret1m - qqq_ret1m if ret1m is not None and qqq_ret1m is not None else None,
        "rs3mQqq": ret3m - qqq_ret3m if ret3m is not None and qqq_ret3m is not None else None,
        "rs6mSpy": ret6m - spy_ret6m if ret6m is not None and spy_ret6m is not None else None,
        "rs3mSpy": ret3m - spy_ret3m if ret3m is not None and spy_ret3m is not None else None,
        "revenueGrowth": None,
        "epsGrowth": None,
        "debtToEquity": None,
        "earningsDate": None,
    }


def theme_heat(metric, metrics):
    peer_scores = [m["rs1mQqq"] for m in metrics if m["proxy"] == metric["proxy"] and m.get("rs1mQqq") is not None]
    return clamp(50 + (avg(peer_scores) or 0) * 350, 0, 100) if peer_scores else 50


def sector_momentum(metric, metrics):
    peer_returns = [m["ret1m"] for m in metrics if m["sector"] == metric["sector"] and m.get("ret1m") is not None]
    return clamp(50 + (avg(peer_returns) or 0) * 500, 0, 100) if peer_returns else 50


def catalyst_score(metric):
    if (metric.get("volumeRatio20") or 0) >= 1.8:
        return 70
    if (metric.get("breakoutScore") or 0) >= 80:
        return 65
    return 45


def score_metrics(metrics: list[dict]) -> list[dict]:
    arrays = {
        "ret6m": [m.get("ret6m") for m in metrics],
        "ret3m": [m.get("ret3m") for m in metrics],
        "ret1m": [m.get("ret1m") for m in metrics],
        "rs3mQqq": [m.get("rs3mQqq") for m in metrics],
        "rs1mQqq": [m.get("rs1mQqq") for m in metrics],
        "distanceMa200": [m["close"] / m["ma200"] - 1 if m.get("ma200") else None for m in metrics],
        "liquidity": [m.get("avgDollarVolume20") for m in metrics],
        "beta": [m.get("beta") for m in metrics],
        "atrPct": [m.get("atrPct") for m in metrics],
        "volumeRatio20": [m.get("volumeRatio20") for m in metrics],
    }
    for metric in metrics:
        drawdown = metric["close"] / metric["high52w"] - 1 if metric.get("high52w") else None
        distance_ma200 = metric["close"] / metric["ma200"] - 1 if metric.get("ma200") else None
        trend_penalty = (
            (5 if drawdown is not None and drawdown < -0.2 else 0)
            + (3 if (metric.get("atrPct") or 0) > 0.05 else 0)
            + (10 if metric.get("ma50") and metric["close"] < metric["ma50"] else 0)
        )
        elastic_penalty = (8 if (metric.get("atrPct") or 0) > 0.09 else 0) + (
            10 if metric.get("ma50") and metric["close"] < metric["ma50"] else 0
        )
        close_above_ma20 = metric["close"] / metric["ma20"] - 1 if metric.get("ma20") else 0
        chase_penalty = (
            (10 if (metric.get("dailyGain") or 0) > 0.12 else 0)
            + (10 if (metric.get("rsi14") or 0) > 78 else 0)
            + (10 if close_above_ma20 > 0.12 else 0)
            + (10 if (metric.get("atrPct") or 0) > 0.1 else 0)
        )
        metric["trendRiskPenalty"] = trend_penalty
        metric["elasticRiskPenalty"] = elastic_penalty
        metric["chaseRiskPenalty"] = chase_penalty
        metric["trendScore"] = clamp(
            0.25 * percentile(metric.get("ret6m"), arrays["ret6m"])
            + 0.2 * percentile(metric.get("ret3m"), arrays["ret3m"])
            + 0.15 * percentile(metric.get("rs3mQqq"), arrays["rs3mQqq"])
            + 0.15 * percentile(distance_ma200, arrays["distanceMa200"])
            + 0.1 * 50
            + 0.1 * 50
            + 0.05 * percentile(metric.get("avgDollarVolume20"), arrays["liquidity"])
            - trend_penalty,
            0,
            100,
        )
        metric["elasticScore"] = clamp(
            0.2 * percentile(metric.get("ret1m"), arrays["ret1m"])
            + 0.2 * percentile(metric.get("ret3m"), arrays["ret3m"])
            + 0.15 * percentile(metric.get("beta"), arrays["beta"])
            + 0.15 * percentile(metric.get("atrPct"), arrays["atrPct"])
            + 0.15 * 50
            + 0.1 * percentile(metric.get("volumeRatio20"), arrays["volumeRatio20"])
            + 0.05 * theme_heat(metric, metrics)
            - elastic_penalty,
            0,
            100,
        )
        breakout = 100 if metric.get("high60Prev") and metric["close"] > metric["high60Prev"] else 80 if metric.get("high20Prev") and metric["close"] > metric["high20Prev"] else 60 if metric["close"] > metric["previousClose"] and metric.get("ma20") and metric["close"] > metric["ma20"] else 0
        volume_surge = clamp((metric.get("volumeRatio20") or 0) * 40, 0, 100)
        intraday = clamp(((metric["close"] - metric["low"]) / (metric["high"] - metric["low"])) * 100, 0, 100) if metric["high"] != metric["low"] else 50
        metric["breakoutScore"] = breakout
        metric["volumeSurgeScore"] = volume_surge
        metric["intradayStrengthScore"] = intraday
        metric["tradeScore"] = clamp(
            0.25 * breakout
            + 0.2 * volume_surge
            + 0.15 * intraday
            + 0.15 * percentile(metric.get("rs1mQqq"), arrays["rs1mQqq"])
            + 0.1 * catalyst_score(metric)
            + 0.1 * percentile(metric.get("avgDollarVolume20"), arrays["liquidity"])
            + 0.05 * sector_momentum(metric, metrics)
            - chase_penalty,
            0,
            100,
        )
    return metrics


def index_snapshot(symbol: str, chart: dict) -> dict:
    closes = values((chart or {}).get("bars") or [], "close")
    return {
        "symbol": symbol,
        "close": round_num(closes[-1] if closes else None),
        "ma50": round_num(sma(closes, 50)),
        "ma200": round_num(sma(closes, 200)),
        "ret20d": round_num((pct_return(closes, 20) or 0) * 100),
        "aboveMa200": closes[-1] > sma(closes, 200) if closes and sma(closes, 200) else None,
    }


def build_market(benchmarks: dict, metrics: list[dict]) -> dict:
    spy = index_snapshot("SPY", benchmarks.get("SPY"))
    qqq = index_snapshot("QQQ", benchmarks.get("QQQ"))
    vix = ((benchmarks.get("^VIX") or {}).get("bars") or [{}])[-1].get("close")
    above_ma50 = len([m for m in metrics if m.get("ma50") and m["close"] > m["ma50"]]) / len(metrics) if metrics else 0
    score = (
        (30 if spy.get("aboveMa200") else 0)
        + (20 if qqq.get("aboveMa200") else 0)
        + (15 if spy.get("ma50") and spy.get("ma200") and spy["ma50"] > spy["ma200"] else 0)
        + (15 if (qqq.get("ret20d") or 0) > 0 else 0)
        + (10 if vix and vix < 22 else 0)
        + (10 if above_ma50 > 0.5 else 0)
    )
    if score >= 75:
        label, tone, allocation = "强势市场", "positive", {"trend": 0.4, "elastic": 0.3, "shortTerm": 0.2, "cash": 0.1}
    elif score >= 55:
        label, tone, allocation = "震荡市场", "neutral", {"trend": 0.4, "elastic": 0.2, "shortTerm": 0.1, "cash": 0.3}
    else:
        label, tone, allocation = "弱势市场", "negative", {"trend": 0.2, "elastic": 0, "shortTerm": 0.07, "cash": 0.73}
    return {
        "marketScore": score,
        "regime": label,
        "tone": tone,
        "allocation": allocation,
        "spy": spy,
        "qqq": qqq,
        "vix": round_num(vix),
        "percentUniverseAboveMa50": round_num(above_ma50 * 100, 1),
        "rules": [
            "MarketScore >= 75：A/B/C/D 按 40/30/20/10 执行。",
            "55 <= MarketScore < 75：高弹性仓与短线仓降权，现金提高到 30%。",
            "MarketScore < 55：暂停高弹性新开仓，短线仅保留极高分机会。",
        ],
    }


def is_tradable(metric):
    return metric["close"] >= 10 and (metric.get("avgDollarVolume20") or 0) >= 100_000_000 and len(metric["bars"]) >= 120


def cap_ok(value, minimum, maximum=math.inf):
    return True if value is None else minimum <= value <= maximum


def trend_pool(metric):
    return (
        is_tradable(metric)
        and cap_ok(metric.get("marketCap"), 50_000_000_000)
        and (metric.get("avgDollarVolume20") or 0) >= 300_000_000
        and metric.get("ma50")
        and metric.get("ma150")
        and metric.get("ma200")
        and metric["close"] > metric["ma50"] > metric["ma150"] > metric["ma200"]
        and (metric.get("ma50Slope20d") or 0) > 0
        and metric.get("high52w")
        and metric["close"] >= 0.85 * metric["high52w"]
        and (metric.get("rs3mQqq") or 0) > 0
        and (metric.get("rs6mSpy") or 0) > 0
    )


def elastic_pool(metric):
    return (
        is_tradable(metric)
        and cap_ok(metric.get("marketCap"), 5_000_000_000, 80_000_000_000)
        and (metric.get("avgDollarVolume20") or 0) >= 150_000_000
        and (metric.get("beta") or 1.3) >= 1.3
        and 0.03 <= (metric.get("atrPct") or 0) <= 0.09
        and metric.get("ma50")
        and metric.get("ma200")
        and metric["close"] > metric["ma50"]
        and metric["close"] > metric["ma200"]
        and (metric.get("ret1m") or 0) > 0.05
        and (metric.get("ret3m") or 0) > 0.1
        and (metric.get("rs1mQqq") or 0) > 0
    )


def short_pool(metric):
    upper_close = metric["close"] >= metric["high"] * 0.75 + metric["low"] * 0.25 if metric["high"] != metric["low"] else True
    breakout = (metric.get("high20Prev") and metric["close"] > metric["high20Prev"]) or (metric.get("gapUp") or 0) >= 0.03
    return (
        metric["close"] >= 15
        and (metric.get("avgDollarVolume20") or 0) >= 300_000_000
        and metric["dollarVolumeToday"] >= 1.5 * (metric.get("avgDollarVolume20") or math.inf)
        and 0.03 <= (metric.get("dailyGain") or 0) <= 0.12
        and metric["close"] > metric["open"]
        and upper_close
        and breakout
        and 55 <= (metric.get("rsi14") or 0) <= 75
    )


def module_position_size(allocation, max_positions, entry, stop, cap=0.1):
    distance = max(0.001, (entry - stop) / entry) if entry and stop else 0.08
    risk_weight = 0.006 / distance
    bucket_weight = allocation / max_positions if max_positions else 0
    return round_num(clamp(min(risk_weight, bucket_weight, cap), 0.01, cap) * 100, 1)


def risk_flags(metric, bucket):
    flags = []
    if metric.get("marketCap") is None:
        flags.append("市值数据缺失")
    if metric.get("revenueGrowth") is None and bucket != "shortTerm":
        flags.append("财务增速缺失")
    if (metric.get("atrPct") or 0) > 0.07:
        flags.append("波动率偏高")
    if bucket == "shortTerm" and (metric.get("chaseRiskPenalty") or 0) >= 20:
        flags.append("追高风险")
    return flags


def reasons(metric, bucket):
    if bucket == "trend":
        return [
            label
            for label, ok in [
                ("收盘价站上 MA50", metric.get("ma50") and metric["close"] > metric["ma50"]),
                ("均线多头排列", metric.get("ma50") and metric.get("ma150") and metric.get("ma200") and metric["ma50"] > metric["ma150"] > metric["ma200"]),
                ("3个月相对 QQQ 强势", (metric.get("rs3mQqq") or 0) > 0),
                ("距离 52 周高点不远", metric.get("high52w") and metric["close"] >= 0.85 * metric["high52w"]),
            ]
            if ok
        ]
    if bucket == "elastic":
        return [
            label
            for label, ok in [
                ("Beta 高弹性", (metric.get("beta") or 0) >= 1.3),
                ("ATR 波动足够", (metric.get("atrPct") or 0) >= 0.03),
                ("1个月动量为正", (metric.get("ret1m") or 0) > 0.05),
                ("成交量放大", (metric.get("volumeRatio20") or 0) >= 1.2),
            ]
            if ok
        ]
    return [
        label
        for label, ok in [
            ("突破 20/60 日平台", (metric.get("breakoutScore") or 0) >= 80),
            ("成交额显著放大", (metric.get("volumeRatio20") or 0) >= 1.5),
            ("收在日内强区", (metric.get("intradayStrengthScore") or 0) >= 70),
            ("短期相对 QQQ 强势", (metric.get("rs1mQqq") or 0) > 0),
        ]
        if ok
    ]


def plan(metric, bucket, allocation, trading_date):
    if bucket == "trend":
        breakout = metric.get("high20Prev") and metric["close"] > metric["high20Prev"]
        entry = metric["close"] if breakout else max(metric.get("ma20") or metric["close"], metric["close"] * 0.985)
        stop = entry - 2.5 * (metric.get("atr14") or entry * 0.04)
        return {
            "entry": {"price": round_num(entry), "zoneLow": round_num(entry * 0.985), "zoneHigh": round_num(entry * 1.015), "note": "20日新高确认后分批买入" if breakout else "回踩 MA20/强势区间低吸"},
            "sell": {"target1": round_num(entry * 1.12), "target2": round_num(entry * 1.2), "timeWindow": "2-12周", "earliestDate": add_business_days(trading_date, 10), "latestDate": add_business_days(trading_date, 60), "note": "盈利超过 20% 后，保护线抬到 MA50 或 Entry + 1*ATR。"},
            "stop": {"price": round_num(stop), "trendStop": round_num(metric.get("ma50")), "timeWindow": "触发即执行", "reviewDate": add_business_days(trading_date, 2), "note": "硬止损为 Entry - 2.5*ATR；连续两日收破 MA50 也退出。"},
            "positionSizePct": module_position_size(allocation, 6, entry, stop, 0.1),
        }
    if bucket == "elastic":
        entry = metric["close"]
        stop = max(entry * 0.93, entry - 2 * (metric.get("atr14") or entry * 0.04))
        return {
            "entry": {"price": round_num(entry), "zoneLow": round_num(entry * 0.985), "zoneHigh": round_num(entry * 1.02), "note": "放量站稳后先建 3%，3-5 日继续突破再加仓。"},
            "sell": {"target1": round_num(entry * 1.15), "target2": round_num(entry * 1.27), "timeWindow": "1-6周", "earliestDate": add_business_days(trading_date, 5), "latestDate": add_business_days(trading_date, 30), "note": "15% 先卖 1/3，25%-30% 再卖 1/3，剩余用 MA20/2.5*ATR 跟踪。"},
            "stop": {"price": round_num(stop), "timeWindow": "触发即执行", "reviewDate": add_business_days(trading_date, 10), "note": "止损取 -7% 或 Entry - 2*ATR 中更近者。"},
            "positionSizePct": module_position_size(allocation, 7, entry, stop, 0.06),
        }
    entry = metric.get("high20Prev") if metric.get("high20Prev") and metric["close"] > metric["high20Prev"] else metric["close"]
    stop = max(entry * 0.965, entry - 1.2 * (metric.get("atr14") or entry * 0.025))
    return {
        "entry": {"price": round_num(entry), "zoneLow": round_num(entry * 0.995), "zoneHigh": round_num(entry * 1.015), "note": "突破位回踩不破或 VWAP 上方横盘再突破。"},
        "sell": {"target1": round_num(entry * 1.06), "target2": round_num(entry * 1.085), "timeWindow": "1-10个交易日", "earliestDate": add_business_days(trading_date, 1), "latestDate": add_business_days(trading_date, 10), "note": "6%-8% 卖出 1/2，剩余用 5日均线或 Entry + 0.5*ATR 保护。"},
        "stop": {"price": round_num(stop), "timeWindow": "当日或次日触发即执行", "reviewDate": add_business_days(trading_date, 1), "note": "跌回突破位/VWAP 下方，收盘前退出。"},
        "positionSizePct": module_position_size(allocation, 4, entry, stop, 0.05),
    }


def recommendation(metric, bucket, market, trading_date):
    score_name = {"trend": "trendScore", "elastic": "elasticScore", "shortTerm": "tradeScore"}[bucket]
    score_label = {"trend": "TrendScore", "elastic": "ElasticScore", "shortTerm": "TradeScore"}[bucket]
    score = round_num(metric[score_name], 1)
    threshold = {"trend": 75, "elastic": 78, "shortTerm": 80}[bucket]
    action = "BUY" if score is not None and score >= threshold else "WATCH"
    if bucket == "elastic" and market["regime"] == "弱势市场":
        action = "PAUSE"
    if bucket == "shortTerm" and market["regime"] == "弱势市场" and (score or 0) < 90:
        action = "WATCH"
    p = plan(metric, bucket, market["allocation"][bucket], trading_date)
    return {
        "symbol": metric["symbol"],
        "name": metric["name"],
        "sector": metric["sector"],
        "theme": metric["theme"],
        "action": action,
        "score": score,
        "scoreLabel": score_label,
        "currentPrice": round_num(metric["close"]),
        "changeFromOpenPct": round_num((metric.get("dailyGain") or 0) * 100),
        "marketCap": metric.get("marketCap"),
        "beta": round_num(metric.get("beta"), 2),
        "atrPct": round_num((metric.get("atrPct") or 0) * 100),
        "volumeRatio20": round_num(metric.get("volumeRatio20"), 2),
        "revenueGrowthPct": None,
        "epsGrowthPct": None,
        "earningsDate": None,
        "entry": p["entry"],
        "sell": p["sell"],
        "stop": p["stop"],
        "positionSizePct": p["positionSizePct"],
        "reasonCodes": reasons(metric, bucket),
        "riskFlags": risk_flags(metric, bucket),
        "sourceUrl": metric["sourceUrl"],
    }


def build_modules(metrics, market, trading_date):
    trend = [recommendation(m, "trend", market, trading_date) for m in sorted(filter(trend_pool, metrics), key=lambda x: x["trendScore"], reverse=True)[:8]]
    elastic = [recommendation(m, "elastic", market, trading_date) for m in sorted(filter(elastic_pool, metrics), key=lambda x: x["elasticScore"], reverse=True)[:10]]
    short = [recommendation(m, "shortTerm", market, trading_date) for m in sorted(filter(short_pool, metrics), key=lambda x: x["tradeScore"], reverse=True)[:8]]
    return {
        "trend": {"key": "trend", "title": "A 趋势放大仓", "allocationPct": round_num(market["allocation"]["trend"] * 100, 1), "objective": "中大型强趋势股，跟随主升段。", "recommendations": trend},
        "elastic": {"key": "elastic", "title": "B 高弹性仓", "allocationPct": round_num(market["allocation"]["elastic"] * 100, 1), "objective": "强主题里的高 beta 成长股，用小仓位博高弹性。", "recommendations": elastic},
        "shortTerm": {"key": "shortTerm", "title": "C 短线交易仓", "allocationPct": round_num(market["allocation"]["shortTerm"] * 100, 1), "objective": "高流动性、放量、明确催化和突破。", "recommendations": short},
        "cash": {
            "key": "cash",
            "title": "D 现金机动仓",
            "allocationPct": round_num(market["allocation"]["cash"] * 100, 1),
            "objective": "防守、补仓和极高确定性机会资金。",
            "recommendations": [],
            "rules": [
                "强势市场现金约 10%，震荡市场约 30%，弱势市场 60%-75%。",
                "只在核心趋势票回踩未破、SPY/QQQ 恐慌后反包、短线仓出现极高分机会时动用。",
                "禁止用现金摊平亏损票，除非原趋势逻辑仍成立且未触发止损。",
            ],
        },
    }


def build_charts(metrics, benchmarks, modules):
    selected = {"SPY", "QQQ", "^VIX"}
    selected.update(metric["symbol"] for metric in metrics)
    source = {m["symbol"]: m for m in metrics}
    source.update({symbol: chart for symbol, chart in benchmarks.items() if chart})
    charts = {}
    for symbol in selected:
        item = source.get(symbol)
        if not item or not item.get("bars"):
            continue
        closes = values(item["bars"], "close")
        recent = item["bars"][-180:]
        offset = len(item["bars"]) - len(recent)
        charts[symbol] = {
            "symbol": symbol,
            "name": item.get("name") or symbol,
            "bars": [
                {
                    "date": bar["date"],
                    "close": round_num(bar["close"]),
                    "volume": bar["volume"],
                    "ma20": round_num(sma(closes, 20, offset + idx)),
                    "ma50": round_num(sma(closes, 50, offset + idx)),
                }
                for idx, bar in enumerate(recent)
            ],
        }
    return charts


def fallback(error: str) -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    market = {
        "marketScore": 0,
        "regime": "数据不可用",
        "tone": "negative",
        "allocation": {"trend": 0, "elastic": 0, "shortTerm": 0, "cash": 1},
        "spy": {},
        "qqq": {},
        "vix": None,
        "percentUniverseAboveMa50": None,
        "rules": [],
    }
    return {
        "schemaVersion": 1,
        "generatedAt": now_iso(),
        "tradingDate": today,
        "status": "fallback",
        "errors": [error],
        "sources": [],
        "strategy": {"name": "美股四仓量化策略", "warning": "数据生成失败，当前文件仅用于让页面可打开。请检查 GitHub Action 日志。"},
        "market": market,
        "modules": build_modules([], market, today),
        "news": {"market": [], "bySymbol": {}},
        "serenity": {"status": "needs_token", "source": "X API v2", "profileUrl": X_PROFILE_URL, "updatedAt": now_iso(), "summary": ["等待每日数据生成。"], "posts": []},
        "charts": {},
    }


def main():
    errors: list[str] = []
    symbols = sorted(set(MARKET_SYMBOLS + [item["symbol"] for item in UNIVERSE]))
    universe_symbols = {item["symbol"] for item in UNIVERSE}

    charts: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(get_chart, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                charts[symbol] = future.result()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Chart {symbol}: {exc}")

    if "SPY" not in charts or "QQQ" not in charts:
        raise RuntimeError("SPY/QQQ chart data unavailable; cannot calculate MarketScore.")

    nasdaq_meta = get_nasdaq_meta(universe_symbols, errors)
    benchmarks = {symbol: charts.get(symbol) for symbol in MARKET_SYMBOLS}

    metrics = []
    for base in UNIVERSE:
        chart = charts.get(base["symbol"])
        if not chart:
            continue
        metric = build_metric(base, chart, nasdaq_meta.get(base["symbol"], {}), benchmarks)
        if metric:
            metrics.append(metric)
    score_metrics(metrics)

    market = build_market(benchmarks, metrics)
    trading_date = charts["SPY"]["bars"][-1]["date"]
    modules = build_modules(metrics, market, trading_date)
    rec_symbols = []
    for module in modules.values():
        for item in module.get("recommendations") or []:
            if item["symbol"] not in rec_symbols:
                rec_symbols.append(item["symbol"])

    try:
        market_news = get_news("stock market SPY QQQ", 8)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Market news failed: {exc}")
        market_news = []

    by_symbol = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(get_news, f"{symbol} stock", 3): symbol for symbol in rec_symbols[:18]}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                by_symbol[symbol] = future.result()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"News {symbol}: {exc}")

    data = {
        "schemaVersion": 1,
        "generatedAt": now_iso(),
        "tradingDate": trading_date,
        "status": "partial" if errors else "ok",
        "errors": errors,
        "sources": [
            {"name": "Yahoo Finance Chart", "url": "https://finance.yahoo.com/", "usage": "真实日线 OHLCV、SPY/QQQ/VIX、技术指标"},
            {"name": "Nasdaq Stock Screener", "url": "https://www.nasdaq.com/market-activity/stocks/screener", "usage": "市值、上市交易所和股票名称"},
            {"name": "Yahoo Finance Search", "url": "https://finance.yahoo.com/", "usage": "每日资讯新闻"},
            {"name": "X API v2", "url": X_PROFILE_URL, "usage": "Serenity 最新讯息，需要仓库 Secret：X_BEARER_TOKEN"},
        ],
        "strategy": {
            "name": "美股四仓量化策略",
            "sourceDocument": "美股持仓完整量化逻辑.docx",
            "notes": [
                "先由 MarketScore 决定总仓位，再对个股做 A/B/C 仓评分。",
                "用户未在页面输入买入价时，提醒系统会跳过该标的。",
            ],
        },
        "market": market,
        "modules": modules,
        "news": {"market": market_news, "bySymbol": by_symbol},
        "serenity": get_serenity_summary(),
        "charts": build_charts(metrics, benchmarks, modules),
        "universeStats": {
            "totalConfigured": len(UNIVERSE),
            "metricsReady": len(metrics),
            "tradableAfterBaseFilter": len([m for m in metrics if is_tradable(m)]),
        },
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_FILE}")
    print(f"Trading date: {trading_date}; status={data['status']}; errors={len(errors)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(json.dumps(fallback(str(exc)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
