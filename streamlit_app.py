import time
import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(layout="wide")

polygon_key = st.secrets["polygon_key"]

# --- HTTP session (connection pooling) ---
@st.cache_resource
def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s

# --- Cache Nasdaq traded symbols (does NOT need to refresh every second) ---
@st.cache_data(ttl=2 * 60 * 60)  # 24 hours
def load_nasdaq_symbol_set() -> set[str]:
    url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    df = pd.read_csv(url, sep="|", dtype=str)
    # Using a set makes membership checks O(1) instead of O(n)
    return set(df["Symbol"].dropna().astype(str))

# --- Cache Polygon snapshot briefly to reduce load / rate-limit issues ---
@st.cache_data(ttl=2)  # adjust: 1–10 seconds depending on how “live” you want it
def fetch_polygon_tickers(api_key: str) -> list[dict]:
    url = (
        "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
        f"?include_otc=true&apiKey={api_key}"
    )
    r = get_session().get(url, timeout=15)
    r.raise_for_status()
    payload = r.json()
    return payload.get("tickers", [])

def build_tables(tickers: list[dict], nasdaq_symbols: set[str]):
    cont_list = {"Q", "D"}
    rows = []

    for item in tickers:
        try:
            ticker = item.get("ticker")
            if not ticker:
                continue

            # Your existing filters:
            if len(ticker) == 5 and (ticker[-1] not in cont_list) and ticker != "DTREF":
                continue
            if "." in ticker or ticker != ticker.upper():
                continue

            pct = item.get("todaysChangePerc")
            day = item.get("day") or {}
            last_trade = item.get("lastTrade") or {}

            v = day.get("v")
            vw = day.get("vw")
            price = last_trade.get("p")

            # Skip tickers with missing trading data (common for OTC)
            if pct is None or v is None or vw is None or price is None:
                continue

            pct = float(pct)
            v = int(v)
            vw = float(vw)
            price = float(price)

            dollar_vol = int(v * vw)
            venue = "listed" if ticker in nasdaq_symbols else "otc"

            rows.append([ticker, price, vw, pct, v, dollar_vol, venue])
        except Exception:
            # Skip malformed ticker entries rather than blowing up the whole refresh
            continue

    cols = ["Ticker", "Price", "VWAP", "% Change", "Volume", "$ Volume", "Venue"]
    df = pd.DataFrame(rows, columns=cols)

    if df.empty:
        empty_cols = ["Ticker", "Price", "VWAP", "% Change", "Volume", "$ Volume"]
        empty = pd.DataFrame(columns=empty_cols)
        return empty, empty, empty, empty

    df = df.sort_values(by="% Change", ascending=False)
    df["% Change"] = df["% Change"].round(2).map(lambda x: f"{x:+.2f}%")

    listed_df = (
        df[df["Venue"] == "listed"]
        .copy()
        .query("Price < 100")
        .head(75)
        .drop(columns=["Venue"])
    )

    otc_df = (
        df[df["Venue"] == "otc"]
        .copy()
        .query("`$ Volume` > 5000")
        .drop(columns=["Venue"])
    )

    triple_zero_df = otc_df[otc_df["Price"] < 0.001].head(50)
    sub_penny_df = otc_df[(otc_df["Price"] >= 0.001) & (otc_df["Price"] <= 0.01)].head(50)
    penny_plus_df = otc_df[otc_df["Price"] > 0.01].head(50)

    return listed_df, triple_zero_df, sub_penny_df, penny_plus_df


# --- Layout (placeholders) ---
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Listed**")
    listed_slot = st.empty()
with col2:
    st.markdown("**Triple Zero**")
    triple_slot = st.empty()

col3, col4 = st.columns(2)
with col3:
    st.markdown("**Sub Penny**")
    sub_slot = st.empty()
with col4:
    st.markdown("**Penny +**")
    penny_slot = st.empty()

status_slot = st.empty()

column_cfg = {
    "Volume": st.column_config.NumberColumn(format="localized"),
    "$ Volume": st.column_config.NumberColumn(format="localized"),
}

# --- Auto-refresh fragment (instead of while True) ---
@st.fragment(run_every="1s")
def refresh_tables():
    try:
        nasdaq_symbols = load_nasdaq_symbol_set()
        tickers = fetch_polygon_tickers(polygon_key)

        df1, df2, df3, df4 = build_tables(tickers, nasdaq_symbols)

        listed_slot.dataframe(df1, hide_index=True, column_config=column_cfg)
        triple_slot.dataframe(df2, hide_index=True, column_config=column_cfg)
        sub_slot.dataframe(df3, hide_index=True, column_config=column_cfg)
        penny_slot.dataframe(df4, hide_index=True, column_config=column_cfg)

        ny = ZoneInfo("America/New_York")
        status_slot.caption(
        "Last updated (New York): " + datetime.now(ny).strftime("%Y-%m-%d %I:%M:%S %p %Z")
        )
    except Exception as e:
        # Visible error instead of silently looping forever
        status_slot.error(f"Refresh failed: {e!r}")

refresh_tables()
