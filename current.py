import argparse
import os

import finnhub
from dotenv import load_dotenv

load_dotenv()


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Get current market data for a ticker")
    parser.add_argument(
        "ticker", type=str, help="Stock ticker symbol (e.g., AAPL, MSFT)"
    )

    # Parse arguments
    args = parser.parse_args()
    ticker = args.ticker.upper()

    # Initialize Finnhub client
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])

    # Get current market data
    quote = finnhub_client.quote(ticker)

    quote_msg = f"""
Current price: ${quote.get("c", 0):.2f}
Change: ${quote.get("d", 0):.2f}
Percent change: {quote.get("dp", 0):.2f}%
High price of the day: ${quote.get("h", 0):.2f}
Low price of the day: ${quote.get("l", 0):.2f}
Open price of the day: ${quote.get("o", 0):.2f}
Previous close price: ${quote.get("pc", 0):.2f}
"""

    print(quote_msg)


if __name__ == "__main__":
    main()
