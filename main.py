import argparse
import json
from arbitrage_finder import ArbitrageFinder
from config import Config

def main():
    parser = argparse.ArgumentParser(description="Sports Betting Arbitrage Finder")
    parser.add_argument("-r", "--region", choices=["eu", "us", "uk", "au"], default="us", help="Region for bookmakers")
    parser.add_argument("-u", "--unformatted", action="store_true", help="Skip interactive UI and only output JSON data")
    parser.add_argument("-c", "--cutoff", type=float, default=0, help="Minimum profit margin percentage")
    parser.add_argument("--api-key", type=str, help="API key for The Odds API")
    parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive betting calculator")
    parser.add_argument("-s", "--save", type=str, help="Save API response to a file")
    parser.add_argument("-o", "--offline", type=str, help="Use offline data from a file instead of making API calls")
    parser.add_argument("--market", choices=["h2h", "spreads", "totals", "outrights", "h2h_lay", "outrights_lay"], default="h2h", help="Betting market to analyze")
    args = parser.parse_args()

    config = Config(args.region, args.unformatted, args.cutoff, args.api_key, args.interactive, args.save, args.offline, args.market)
    arbitrage_finder = ArbitrageFinder(config)
    results = arbitrage_finder.find_arbitrage()

    # Always write results to arbitrage_results.json
    with open('arbitrage_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results have been written to arbitrage_results.json")
    print(f"Detailed logs can be found in arbitrage_finder.log")

    if not config.unformatted:
        # Display interactive UI or other formatted output here
        print("Displaying interactive UI or formatted output...")
        # You can add more code here to handle the interactive UI
    else:
        print("Skipping interactive UI due to -u flag.")

if __name__ == "__main__":
    main()
