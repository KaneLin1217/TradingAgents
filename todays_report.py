import argparse
import os
from datetime import datetime
from pathlib import Path

import finnhub
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()


def save_trade_decision(decision, ticker, date):
    """
    Save the trading decision to the reports folder.

    Args:
        decision (dict): The trading decision dictionary
        ticker (str): Stock ticker symbol
        date (str): Date in YYYY-MM-DD format
    """
    # Create the directory path
    reports_dir = Path(f"results/{ticker}/{date}/reports")

    # Ensure the directory exists
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Save the new trading decision
    decision_file = reports_dir / "today_trade_decision.md"

    # Format the decision content
    decision_content = f"""# Today's Trading Decision for {ticker} - {date}

## Market Data
{decision["market_data"]}

## Today's Trading Decision
{decision["new_decision"]}
"""

    try:
        decision_file.write_text(decision_content)
        print(f"✓ Trading decision saved to: {decision_file}")
    except Exception as e:
        print(f"Error saving trading decision: {e}")


def get_trading_decision(ticker, date, current_price=None):
    """
    Trading agent that takes current price and other information as input
    and outputs a trading decision.

    Args:
        ticker (str): Stock ticker symbol
        date (str): Date in YYYY-MM-DD format
        current_price (float, optional): Current price. If None, will fetch from API

    Returns:
        dict: Trading decision with recommendation and rationale
    """

    # Initialize Finnhub client
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])

    # Get current market data
    try:
        quote = finnhub_client.quote(ticker)

        # Use provided current_price or fetch from API
        if current_price is None:
            current_price = quote.get("c", 0)

        quote_msg = f"""
Current price: ${current_price:.2f}

Change: ${quote.get("d", 0):.2f}

Percent change: {quote.get("dp", 0):.2f}%

High price of the day: ${quote.get("h", 0):.2f}

Low price of the day: ${quote.get("l", 0):.2f}

Open price of the day: ${quote.get("o", 0):.2f}

Previous close price: ${quote.get("pc", 0):.2f}

"""
    except Exception as e:
        print(f"Error fetching market data: {e}")
        quote_msg = f"Ticker: {ticker}\nCurrent price: ${current_price:.2f if current_price else 0:.2f}\n"

    # Initialize LLM
    llm = ChatDeepSeek(model="deepseek-reasoner")

    # Read the previous trade decision
    trade_decision_path = Path(
        f"results/{ticker}/{date}/reports/final_trade_decision.md"
    )
    trade_decision = ""

    try:
        trade_decision = trade_decision_path.read_text()
    except FileNotFoundError:
        print(f"Error: No previous trading decision found at {trade_decision_path}")
        print("Exiting: Previous trading decision is required to proceed.")
        exit(1)
    except Exception as e:
        print(f"Error reading trade decision file: {e}")
        print("Exiting: Cannot read previous trading decision.")
        exit(1)

    context = {
        "role": "user",
        "content": f"""Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {ticker}.
This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment.
Use this plan as a foundation for evaluating today's trading decision.

Current Market Data:
{quote_msg}

Previous Trade Decision Analysis:
{trade_decision}

Leverage these insights to make an informed and strategic decision for today's trading.""",
    }

    messages = [
        {
            "role": "system",
            "content": """You are a trading agent analyzing market data to make investment decisions.
Based on your analysis, provide a specific recommendation to buy, sell, or hold.
End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation.

Your response should include:
1. Analysis of current market conditions
2. Comparison with previous trade decision
3. Risk assessment
4. Specific entry/exit points if applicable
5. Clear final recommendation""",
        },
        context,
    ]

    try:
        result = llm.invoke(messages)

        return {
            "ticker": ticker,
            "date": date,
            "market_data": quote_msg,
            "new_decision": result.content,
        }

    except Exception as e:
        print(f"Error getting trading decision: {e}")
        return {
            "ticker": ticker,
            "date": date,
            "market_data": quote_msg,
            "new_decision": f"Error generating trading decision: {e}",
        }


def main():
    """Main function to run the trading agent"""
    ticker = "NVDA"
    date = datetime.now().strftime("%Y-%m-%d")  # Use today's date

    print("=== Trading Agent Decision ===")
    print(f"Analyzing {ticker} for {date}")
    print()

    # Get trading decision
    decision = get_trading_decision(ticker, date)

    # Save the trading decision
    save_trade_decision(decision, ticker, date)

    # Print results
    print("Market Data:")
    print(decision["market_data"])
    print()

    print("New Trading Decision:")
    print(decision["new_decision"])
    print()

    return decision


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Trading Agent - Analyze and make trading decisions for a given ticker and date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python today.py NVDA                    # Analyze NVDA for today
  python today.py AAPL 2024-01-15         # Analyze AAPL for specific date
  python today.py --ticker TSLA --date 2024-01-20  # Using named arguments
        """,
    )

    parser.add_argument(
        "ticker", nargs="?", default="NVDA", help="Stock ticker symbol (default: NVDA)"
    )

    parser.add_argument(
        "date",
        nargs="?",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date in YYYY-MM-DD format (default: today)",
    )

    # Alternative named arguments
    parser.add_argument(
        "--ticker",
        dest="ticker_alt",
        help="Stock ticker symbol (alternative to positional argument)",
    )

    parser.add_argument(
        "--date",
        dest="date_alt",
        help="Date in YYYY-MM-DD format (alternative to positional argument)",
    )

    args = parser.parse_args()

    # Use named arguments if provided, otherwise use positional arguments
    ticker = args.ticker_alt.upper() if args.ticker_alt else args.ticker.upper()
    date = args.date_alt if args.date_alt else args.date

    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format '{date}'. Please use YYYY-MM-DD format.")
        exit(1)

    # Validate ticker format (basic validation)
    if not ticker.isalpha():
        print(f"Error: Invalid ticker '{ticker}'. Ticker should contain only letters.")
        exit(1)

    # Update the main function to accept parameters
    def run_trading_agent(ticker, date):
        print("=== Trading Agent Decision ===")
        print(f"Analyzing {ticker} for {date}")
        print()

        # Get trading decision
        decision = get_trading_decision(ticker, date)

        # Save the trading decision
        save_trade_decision(decision, ticker, date)

        # Print results
        print("Market Data:")
        print(decision["market_data"])
        print()

        print("New Trading Decision:")
        print(decision["new_decision"])
        print()

        return decision

    run_trading_agent(ticker, date)
