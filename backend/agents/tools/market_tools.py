"""
market_tools.py  –  CrewAI @tool wrappers for market intelligence
"""

from crewai.tools import tool


@tool("Analyze Market Sentiment")
def analyze_sentiment(symbols_csv: str) -> str:
    """
    Return a sentiment score (-1 to +1) for each comma-separated
    stock symbol, with a brief justification per symbol.
    """
    return (
        f"Analysing sentiment for: {symbols_csv}\n"
        "[Tool placeholder – returns per-symbol sentiment scores.]"
    )


@tool("Identify Market Trends")
def identify_trends(symbol: str) -> str:
    """
    Identify the current technical trend (up / down / neutral)
    for a single stock symbol, including support/resistance levels.
    """
    return (
        f"Identifying trends for {symbol}\n"
        "[Tool placeholder – returns trend direction and key levels.]"
    )


@tool("Generate Investment Recommendations")
def generate_recommendations(symbol: str, risk_profile: str) -> str:
    """
    Generate a Buy/Hold/Sell recommendation for *symbol* given
    the investor's risk profile (conservative / moderate / aggressive).
    """
    return (
        f"Generating recommendation for {symbol} "
        f"(risk profile: {risk_profile})\n"
        "[Tool placeholder – returns recommendation with targets.]"
    )
