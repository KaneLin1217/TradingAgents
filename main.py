import argparse
from datetime import datetime

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Trading Agents - Analyze stock ticker for a specific date"
    )
    parser.add_argument(
        "--ticker",
        "-t",
        type=str,
        default="NVDA",
        help="Stock ticker symbol (default: NVDA)",
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        default="2025-08-02",
        help="Date in YYYY-MM-DD format (default: 2025-08-02)",
    )

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.error(f"Invalid date format: {args.date}. Please use YYYY-MM-DD format.")

    return args


# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "deepseek"  # Use a different model
config["backend_url"] = "https://api.deepseek.com/v1"  # Use a different backend
config["deep_think_llm"] = "deepseek-reasoner"  # Use a different model
config["quick_think_llm"] = "deepseek-chat"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Increase debate rounds

# Parse command line arguments
args = parse_arguments()

# Initialize with custom config
ta = TradingAgentsGraph(
    debug=True, config=config, selected_analysts=["market", "news", "fundamentals"]
)

# forward propagate
print(f"Analyzing {args.ticker} for date {args.date}")
_, decision = ta.propagate(args.ticker, args.date)
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
