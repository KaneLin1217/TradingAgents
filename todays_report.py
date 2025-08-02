import argparse
import os
from datetime import datetime
from pathlib import Path

import finnhub
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()


def collect_ticker_and_date():
    """
    Collect ticker symbol and date from user input.

    Returns:
        tuple: (ticker, date) where ticker is str and date is str in YYYY-MM-DD format
    """
    print("\n=== Stock Information ===")

    # Collect ticker
    while True:
        ticker = input("Enter stock ticker symbol (e.g., NVDA, AAPL): ").strip().upper()
        if ticker.isalpha() and len(ticker) > 0:
            break
        print("Please enter a valid ticker symbol (letters only)")

    # Collect date
    while True:
        date_input = input(
            "Enter date (YYYY-MM-DD, or press Enter for today): "
        ).strip()
        if not date_input:
            date_input = datetime.now().strftime("%Y-%m-%d")

        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            break
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format")

    return ticker, date_input


def collect_position_info():
    """
    Collect position information from user input.

    Returns:
        dict: Position information or None if no position
    """
    print("\n=== Position Information ===")
    print("Do you have a current position in this stock?")

    while True:
        has_position = input("Enter 'y' for yes, 'n' for no: ").lower().strip()
        if has_position in ["y", "n"]:
            break
        print("Please enter 'y' or 'n'")

    if has_position == "n":
        return None

    position_info = {}

    print("\nPlease provide the following position details:")

    # Entry price
    while True:
        try:
            entry_price = float(input("Entry price per share: $"))
            if entry_price > 0:
                position_info["entry_price"] = entry_price
                break
            else:
                print("Entry price must be greater than 0")
        except ValueError:
            print("Please enter a valid number")

    # Position size
    while True:
        try:
            size = int(input("Number of shares: "))
            if size > 0:
                position_info["size"] = size
                break
            else:
                print("Position size must be greater than 0")
        except ValueError:
            print("Please enter a valid number")

    # Risk tolerance
    print("\nRisk tolerance level:")
    print("1. Conservative (low risk)")
    print("2. Medium (balanced)")
    print("3. Aggressive (high risk)")

    while True:
        try:
            risk_choice = int(input("Enter choice (1-3): "))
            if risk_choice in [1, 2, 3]:
                risk_levels = {1: "Conservative", 2: "Medium", 3: "Aggressive"}
                position_info["risk_tolerance"] = risk_levels[risk_choice]
                break
            else:
                print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a valid number")

    # Trading style
    print("\nTrading style:")
    print("1. Day Trading (intraday)")
    print("2. Swing Trading (days to weeks)")
    print("3. Position Trading (weeks to months)")
    print("4. Long-term Investing (months to years)")

    while True:
        try:
            style_choice = int(input("Enter choice (1-4): "))
            if style_choice in [1, 2, 3, 4]:
                styles = {
                    1: "Day Trading",
                    2: "Swing Trading",
                    3: "Position Trading",
                    4: "Long-term Investing",
                }
                position_info["trading_style"] = styles[style_choice]
                break
            else:
                print("Please enter 1, 2, 3, or 4")
        except ValueError:
            print("Please enter a valid number")

    return position_info


def build_position_info_from_args(args):
    """
    Build position information from command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        dict: Position information or None if no position data provided
    """
    # Check if any position-related arguments were provided
    if not any([args.entry_price, args.position_size]):
        return None

    # Validate that we have the minimum required information
    if not args.entry_price or not args.position_size:
        print(
            "Warning: Both --entry-price and --position-size are required for position analysis"
        )
        return None

    position_info = {
        "entry_price": args.entry_price,
        "size": args.position_size,
        "risk_tolerance": args.risk_tolerance,
        "trading_style": args.trading_style,
    }

    return position_info


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
    decision_file = reports_dir / "quantitative_trading_analysis.md"

    # Format the decision content
    decision_content = f"""# Quantitative Trading Analysis for {ticker} - {date}

## Market Data
{decision["market_data"]}

## Expert Trading Analysis
{decision["new_decision"]}

---
*Generated by Expert Quantitative Trading Advisor*
*Date: {date}*
*Ticker: {ticker}*
"""

    try:
        decision_file.write_text(decision_content)
        print(f"✓ Quantitative trading analysis saved to: {decision_file}")
    except Exception as e:
        print(f"Error saving trading analysis: {e}")


def get_trading_decision(ticker, date, current_price=None, position_info=None):
    """
    Expert quantitative trading advisor that analyzes market data and provides
    structured trading recommendations with specific price levels and risk controls.

    Args:
        ticker (str): Stock ticker symbol
        date (str): Date in YYYY-MM-DD format
        current_price (float, optional): Current price. If None, will fetch from API
        position_info (dict, optional): Position information including entry price, size, etc.

    Returns:
        dict: Quantitative trading analysis with structured recommendations
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

    # Prepare position data
    if position_info:
        position_data = f"""
```markdown
Entry Price: ${position_info.get("entry_price", 0):.2f}
Position Size: {position_info.get("size", 0)} shares
Current P&L: {((current_price - position_info.get("entry_price", 0)) / position_info.get("entry_price", 1) * 100):.2f}%
Unrealized P&L: ${(current_price - position_info.get("entry_price", 0)) * position_info.get("size", 0):.2f}
Risk Tolerance: {position_info.get("risk_tolerance", "Medium")}
Trading Style: {position_info.get("trading_style", "Balanced")}
```
"""
    else:
        position_data = """
```markdown
No current position
```
"""

    # Prepare real-time data
    real_time_data = f"""
```markdown
{quote_msg}
```
"""

    # Prepare trading decision report
    trading_decision_report = f"""
```markdown
{trade_decision}
```
"""

    context = {
        "role": "user",
        "content": f"""**Role:** Expert quantitative trading advisor

**Inputs:**

- Position:

{position_data}

- Real-time:

{real_time_data}

- Trading Decision Report:

{trading_decision_report}

**Output Structure:**

**1. Position Analysis**

- P&L: (Current-Entry)/Entry
- Health: Position size + P&L + report metrics

**2. Action Recommendations**

*If no position:*

- Mandatory buy limits:
    - Ideal range: [X.XX-Y.YY] (support/volatility-based)
    - Hard limit: Z.ZZ (no-buy threshold)
- If report positive: [N]-stage entry plan

*If positioned:*

- Add triggers:
    - Aggressive: A.AA (breakout signals)
    - Conservative: B.BB (value zone)
- Exit plan:
    - Stop-loss: C.CC (key support)
    - Profit-protect: D.DD (trailing)
- Hedging when {{delta}} volatility > [X]%

**3. Risk Controls**

- Max exposure: ≤ {{risk_tolerance}}%
- Stop/profit adjustment per {{trading_style}}
- Black swan protocol: [Specific actions]

**Mandatory Rules:**

① Flag report-reality conflicts with ⚠️

② Prices to 2 decimals

③ Long-term: Valuation focus | Short-term: Technical signals

④ State validity period (e.g., Intraday/T+2)

⑤ Always provide entry limits if no position

**Bias Adaptation:**

- Short-term: Prioritize technical levels & volatility tools
- Long-term: Emphasize valuation bands & phased entry""",
    }

    messages = [
        {
            "role": "system",
            "content": """You are an expert quantitative trading advisor. Analyze the provided data and provide structured trading recommendations following the exact output format specified in the user's prompt.

Focus on:
- Clear position analysis with P&L calculations
- Specific action recommendations with exact price levels
- Comprehensive risk controls
- Adherence to all mandatory rules
- Proper bias adaptation based on time horizon""",
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
    """Main function to run the quantitative trading advisor"""
    print("=== Expert Quantitative Trading Advisor ===")
    print("Welcome! Let's analyze a stock for you.")
    print()

    # Collect ticker and date from user
    ticker, date = collect_ticker_and_date()

    print(f"\nAnalyzing {ticker} for {date}")
    print()

    # Collect position information from user
    position_info = collect_position_info()

    # Get quantitative trading analysis
    decision = get_trading_decision(ticker, date, position_info=position_info)

    # Save the trading analysis
    save_trade_decision(decision, ticker, date)

    # Print results
    print("Market Data:")
    print(decision["market_data"])
    print()

    print("Expert Trading Analysis:")
    print(decision["new_decision"])
    print()

    return decision


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Expert Quantitative Trading Advisor - Analyze and provide structured trading recommendations for a given ticker and date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python today.py                         # Interactive mode (enter ticker, date, and position)
  python today.py --interactive           # Force interactive mode
  python today.py NVDA                    # Analyze NVDA for today (interactive position input)
  python today.py AAPL 2024-01-15         # Analyze AAPL for specific date
  python today.py --ticker TSLA --date 2024-01-20  # Using named arguments
  python today.py NVDA --entry-price 150.50 --position-size 100  # With position data
  python today.py AAPL --entry-price 175.25 --position-size 50 --risk-tolerance Aggressive
  python today.py TSLA --no-interactive   # Skip interactive input (no position analysis)
        """,
    )

    parser.add_argument(
        "ticker",
        nargs="?",
        help="Stock ticker symbol (optional if using interactive mode)",
    )

    parser.add_argument(
        "date",
        nargs="?",
        help="Date in YYYY-MM-DD format (optional if using interactive mode)",
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

    # Position information arguments
    parser.add_argument(
        "--entry-price",
        type=float,
        help="Entry price per share (if you have a position)",
    )

    parser.add_argument(
        "--position-size",
        type=int,
        help="Number of shares (if you have a position)",
    )

    parser.add_argument(
        "--risk-tolerance",
        choices=["Conservative", "Medium", "Aggressive"],
        default="Medium",
        help="Risk tolerance level (default: Medium)",
    )

    parser.add_argument(
        "--trading-style",
        choices=[
            "Day Trading",
            "Swing Trading",
            "Position Trading",
            "Long-term Investing",
        ],
        default="Swing Trading",
        help="Trading style (default: Swing Trading)",
    )

    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive input (use command line arguments only)",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Force interactive mode for ticker, date, and position input",
    )

    args = parser.parse_args()

    # Determine if we should use interactive mode
    use_interactive = args.interactive or (not args.ticker and not args.ticker_alt)

    if use_interactive:
        # Interactive mode - collect ticker and date from user
        ticker, date = collect_ticker_and_date()
    else:
        # Command line mode - use provided arguments
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
            print(
                f"Error: Invalid ticker '{ticker}'. Ticker should contain only letters."
            )
            exit(1)

    # Update the main function to accept parameters
    def run_trading_agent(ticker, date):
        print("=== Expert Quantitative Trading Advisor ===")
        print(f"Analyzing {ticker} for {date}")
        print()

        # Get position information
        position_info = None

        # First try to build from command line arguments
        if any([args.entry_price, args.position_size]):
            position_info = build_position_info_from_args(args)
            if position_info:
                print(
                    f"Using position data: {position_info['size']} shares at ${position_info['entry_price']:.2f}"
                )

        # If no command line position data and not --no-interactive, collect interactively
        if not position_info and not args.no_interactive:
            position_info = collect_position_info()

        # Get quantitative trading analysis
        decision = get_trading_decision(ticker, date, position_info=position_info)

        # Save the trading analysis
        save_trade_decision(decision, ticker, date)

        # Print results
        print("Market Data:")
        print(decision["market_data"])
        print()

        print("Expert Trading Analysis:")
        print(decision["new_decision"])
        print()

        return decision

    run_trading_agent(ticker, date)
