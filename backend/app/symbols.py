"""Static stock symbol catalog used by backend metadata endpoints."""

from __future__ import annotations


STOCK_SYMBOLS = {
    "technology": [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Technology"},
        {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
        {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology"},
    ],
    "finance": [
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Finance"},
        {"symbol": "BAC", "name": "Bank of America", "sector": "Finance"},
        {"symbol": "WFC", "name": "Wells Fargo & Company", "sector": "Finance"},
        {"symbol": "GS", "name": "The Goldman Sachs Group", "sector": "Finance"},
        {"symbol": "MS", "name": "Morgan Stanley", "sector": "Finance"},
        {"symbol": "BLK", "name": "BlackRock Inc.", "sector": "Finance"},
    ],
    "healthcare": [
        {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
        {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare"},
        {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
        {"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare"},
        {"symbol": "MRK", "name": "Merck & Co., Inc.", "sector": "Healthcare"},
        {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare"},
    ],
    "consumer": [
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer"},
        {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer"},
        {"symbol": "COST", "name": "Costco Wholesale", "sector": "Consumer"},
        {"symbol": "MCD", "name": "McDonald's Corporation", "sector": "Consumer"},
        {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer"},
        {"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "Consumer"},
    ],
    "energy": [
        {"symbol": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy"},
        {"symbol": "CVX", "name": "Chevron Corporation", "sector": "Energy"},
        {"symbol": "COP", "name": "ConocoPhillips", "sector": "Energy"},
        {"symbol": "SLB", "name": "Schlumberger Limited", "sector": "Energy"},
    ],
    "industrials": [
        {"symbol": "BA", "name": "The Boeing Company", "sector": "Industrials"},
        {"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials"},
        {"symbol": "GE", "name": "General Electric Company", "sector": "Industrials"},
        {"symbol": "HON", "name": "Honeywell International", "sector": "Industrials"},
    ],
}

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA"]


def get_all_symbols() -> list[dict[str, str]]:
    symbols: list[dict[str, str]] = []
    for sector_symbols in STOCK_SYMBOLS.values():
        symbols.extend(sector_symbols)
    return sorted(symbols, key=lambda item: item["symbol"])


def get_symbols_by_sector() -> dict[str, list[dict[str, str]]]:
    return STOCK_SYMBOLS
