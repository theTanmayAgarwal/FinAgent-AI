import os

import pandas as pd
import requests
import streamlit as st

internal_api = os.getenv("FINAGENT_API_HOSTPORT")
API = (
    f"http://{internal_api}/api/v1"
    if internal_api
    else os.getenv("FINAGENT_API_URL", "http://localhost:8000/api/v1")
)
API_ROOT = API.removesuffix("/api/v1")
INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "Nifty 50 index": "^NSEI",
    "Custom ticker": "",
}

st.set_page_config(
    page_title="FinAgent AI | Indian Market Intelligence", page_icon="📈", layout="wide"
)
st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; max-width: 1300px;}
    [data-testid="stMetric"] {background: #111827; border: 1px solid #263244; padding: 16px; border-radius: 12px;}
    .finagent-hero {padding: 1.2rem 0 1rem;}
    .finagent-kicker {color:#22c55e; font-size:.8rem; letter-spacing:.13em; font-weight:700;}
    .finagent-hero h1 {font-size:3rem; margin:.2rem 0;}
    .finagent-hero p {color:#9ca3af; font-size:1.05rem;}
    </style>
    <div class="finagent-hero">
      <div class="finagent-kicker">INDIA-FIRST INVESTMENT RESEARCH</div>
      <h1>FinAgent AI</h1>
      <p>Twelve specialist agents. One explainable investment-committee decision.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

for key, default in {"token": "", "report": None, "pdf": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def api_call(method: str, path: str, **kwargs):
    """Call the API without exposing a raw Streamlit traceback to users."""
    try:
        response = requests.request(
            method, f"{API}{path}", timeout=kwargs.pop("timeout", 30), **kwargs
        )
        try:
            detail = response.json().get("detail") if not response.ok else None
        except ValueError:
            detail = response.text
        return response, detail
    except requests.RequestException:
        return (
            None,
            "FinAgent API is offline. Start it with ./scripts/start.sh and refresh this page.",
        )


try:
    api_online = requests.get(f"{API_ROOT}/health", timeout=1.5).ok
except requests.RequestException:
    api_online = False

with st.sidebar:
    st.header("Workspace")
    if api_online:
        st.success("● API online")
    else:
        st.error("● API offline")

    if st.session_state.token:
        st.success("Signed in")
        if st.button("Sign out", use_container_width=True):
            st.session_state.token = ""
            st.session_state.report = None
            st.rerun()
    else:
        st.caption("Create a local account or sign in to run research.")
        email = st.text_input("Email", value="analyst@example.com")
        password = st.text_input("Password", type="password", help="Minimum 12 characters")
        left, right = st.columns(2)
        if left.button("Sign in", use_container_width=True):
            response, error = api_call(
                "POST", "/auth/token", data={"username": email, "password": password}
            )
            if response and response.ok:
                st.session_state.token = response.json()["access_token"]
                st.rerun()
            else:
                st.error(error or "Sign-in failed")
        if right.button("Sign up", use_container_width=True):
            response, error = api_call(
                "POST", "/auth/signup", json={"email": email, "password": password}
            )
            if response and response.ok:
                st.session_state.token = response.json()["access_token"]
                st.rerun()
            else:
                st.error(error or "Sign-up failed")

    st.divider()
    st.caption("Market symbols")
    st.code("NSE: RELIANCE.NS\nBSE: RELIANCE.BO\nIndex: ^NSEI", language=None)

headers = {"Authorization": f"Bearer {st.session_state.token}"}
research_tab, portfolio_tab, reports_tab, about_tab = st.tabs(
    ["Research desk", "Portfolio lab", "Saved reports", "How it works"]
)

with research_tab:
    st.subheader("Indian equity research")
    st.caption("Select an NSE example or enter any Yahoo Finance-compatible NSE/BSE symbol.")
    c1, c2 = st.columns([1.4, 1])
    company = c1.selectbox("Quick select", list(INDIAN_STOCKS))
    suggested = INDIAN_STOCKS[company]
    ticker = c2.text_input("Ticker", value=suggested or "RELIANCE.NS").strip().upper()
    c3, c4, c5 = st.columns(3)
    risk = c3.selectbox("Risk profile", ["conservative", "moderate", "aggressive"], index=1)
    horizon = c4.slider("Investment horizon", 1, 10, 3, format="%d years")
    portfolio_value = c5.number_input(
        "Portfolio value (₹)", min_value=10_000, value=1_000_000, step=50_000
    )

    run_disabled = not st.session_state.token or not api_online
    if st.button(
        "Run 12-agent investment committee",
        type="primary",
        disabled=run_disabled,
        use_container_width=True,
    ):
        with st.spinner("Collecting evidence and convening the investment committee…"):
            response, error = api_call(
                "POST",
                "/research",
                json={
                    "ticker": ticker,
                    "risk_profile": risk,
                    "horizon_years": horizon,
                    "portfolio_value": portfolio_value,
                },
                headers=headers,
                timeout=180,
            )
        if response and response.ok:
            st.session_state.report = response.json()
            pdf_response, _ = api_call(
                "GET", f"/research/{response.json()['id']}/pdf", headers=headers, timeout=60
            )
            st.session_state.pdf = (
                pdf_response.content if pdf_response and pdf_response.ok else None
            )
        else:
            st.error(error or "Research failed. Check the API terminal for details.")

    if not st.session_state.token:
        st.info("Sign in or create a local account in the sidebar to enable research.")

    if st.session_state.report:
        d = st.session_state.report
        st.divider()
        st.caption(f"COMMITTEE REPORT · {ticker}")
        a, b, c, e = st.columns(4)
        a.metric("Decision", d["action"])
        b.metric("Committee score", f"{d['score']:.1f}/100")
        c.metric("Confidence", f"{d['confidence']:.0%}")
        e.metric("Suggested allocation", f"{d['allocation_pct']:.1f}%")
        st.subheader("Investment thesis")
        st.write(d["thesis"])
        bull, bear = st.columns(2)
        with bull:
            st.success("**Bull case**\n\n" + d["bull_case"])
        with bear:
            st.error("**Bear case**\n\n" + d["bear_case"])

        frame = pd.DataFrame(
            [
                {
                    "Agent": x["agent"].replace("_", " ").title(),
                    "Score": round(x["score"], 1),
                    "Confidence": f"{x['confidence']:.0%}",
                    "Finding": x["summary"],
                }
                for x in d["evidence"]
            ]
        )
        st.subheader("Explainability trail")
        st.bar_chart(frame.set_index("Agent")["Score"], horizontal=True)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        if st.session_state.pdf:
            st.download_button(
                "Download institutional PDF report",
                st.session_state.pdf,
                f"{ticker}-FinAgent.pdf",
                "application/pdf",
                use_container_width=True,
            )

with portfolio_tab:
    st.subheader("Portfolio risk lab")
    st.caption(
        "Backtest a weighted Indian portfolio and project outcomes with Monte Carlo simulation."
    )
    holdings = st.text_input(
        "Ticker:weight pairs",
        "RELIANCE.NS:0.30,TCS.NS:0.25,HDFCBANK.NS:0.25,INFY.NS:0.20",
        help="Weights must add to 1.00",
    )
    p1, p2, p3 = st.columns(3)
    years = p1.slider("Projection years", 1, 15, 5)
    sims = p2.slider("Monte Carlo paths", 1_000, 20_000, 5_000, 1_000)
    initial = p3.number_input("Starting value (₹)", min_value=10_000, value=1_000_000, step=50_000)
    if st.button(
        "Run portfolio simulation",
        disabled=not st.session_state.token or not api_online,
        use_container_width=True,
    ):
        try:
            assets = [
                {"ticker": pair.split(":")[0].strip(), "weight": float(pair.split(":")[1])}
                for pair in holdings.split(",")
            ]
            with st.spinner("Backtesting and simulating portfolio paths…"):
                response, error = api_call(
                    "POST",
                    "/portfolio/simulate",
                    json={
                        "assets": assets,
                        "years": years,
                        "simulations": sims,
                        "initial_value": initial,
                    },
                    headers=headers,
                    timeout=180,
                )
            if response and response.ok:
                result = response.json()
                bt, mc = result["backtest"], result["monte_carlo"]
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Historical return", f"{bt['total_return']:.1%}")
                r2.metric("Max drawdown", f"{bt['max_drawdown']:.1%}")
                r3.metric("Median projection", f"₹{mc['median_terminal_value']:,.0f}")
                r4.metric("Probability of loss", f"{mc['probability_of_loss']:.1%}")
                st.json(result, expanded=False)
            else:
                st.error(error or "Simulation failed")
        except (ValueError, IndexError):
            st.error("Use TICKER:WEIGHT pairs, for example RELIANCE.NS:0.5,TCS.NS:0.5")

with reports_tab:
    st.subheader("Saved research")
    if not st.session_state.token:
        st.info("Sign in to view your saved reports.")
    elif st.button("Refresh report history"):
        response, error = api_call("GET", "/research", headers=headers)
        if response and response.ok:
            history = pd.DataFrame(response.json())
            if history.empty:
                st.info("No reports yet.")
            else:
                st.dataframe(history, use_container_width=True, hide_index=True)
        else:
            st.error(error or "Could not load reports")

with about_tab:
    st.subheader("What FinAgent AI can do")
    st.markdown(
        """
        - **Fundamental analysis:** growth, profitability, leverage, cash flow and valuation scoring.
        - **Technical analysis:** RSI, MACD, Bollinger Bands, moving averages, VWAP and support/resistance.
        - **Risk analysis:** volatility, beta, VaR, Sharpe, Sortino and maximum drawdown.
        - **Committee debate:** dedicated bull and bear agents challenge the evidence before the judge decides.
        - **Portfolio intelligence:** allocation guidance, historical backtests and Monte Carlo projections.
        - **Explainability:** every conclusion includes its score, confidence, metrics, source category and risks.
        - **Reporting:** authenticated report history and downloadable PDF committee reports.

        **Current India-market boundary:** live NSE/BSE price and basic fundamental coverage comes from the
        configured Yahoo Finance adapter. News, transcripts, social sentiment, FII/DII flows and macro inputs
        remain demonstration signals until licensed India-specific providers are connected.
        """
    )

st.divider()
st.caption(
    "Educational research only—not investment advice. Verify all market data independently before making investment decisions."
)
