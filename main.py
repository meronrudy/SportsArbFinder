import argparse
import json
from arbitrage_finder import ArbitrageFinder
from config import Config

def main():
    parser = argparse.ArgumentParser(description="Sports Betting Arbitrage Finder")
    parser.add_argument("-r", "--region", choices=["eu", "us", "uk", "au"], default="us", help="Region for bookmakers")
    parser.add_argument("-u", "--unformatted", action="store_true", help="Output unformatted JSON data")
    parser.add_argument("-c", "--cutoff", type=float, default=0, help="Minimum profit margin percentage")
    parser.add_argument("--api-key", type=str, help="API key for The Odds API")
    parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive betting calculator")
    parser.add_argument("-s", "--save", type=str, help="Save API response to a file")
    parser.add_argument("-o", "--offline", type=str, help="Use offline data from a file instead of making API calls")
    args = parser.parse_args()

    config = Config(args.region, args.unformatted, args.cutoff, args.api_key, args.interactive, args.save, args.offline)
    arbitrage_finder = ArbitrageFinder(config)
    results = arbitrage_finder.find_arbitrage()

    if config.unformatted:
        with open('arbitrage_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Unformatted results have been written to arbitrage_results.json")

if __name__ == "__main__":
    main()
