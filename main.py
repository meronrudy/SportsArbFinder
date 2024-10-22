import argparse
from arbitrage_finder import ArbitrageFinder
from config import Config

def main():
    parser = argparse.ArgumentParser(description="Sports Betting Arbitrage Finder")
    parser.add_argument("-r", "--region", choices=["eu", "us", "uk", "au"], default="us", help="Region for bookmakers")
    parser.add_argument("-u", "--unformatted", action="store_true", help="Output unformatted JSON data")
    parser.add_argument("-c", "--cutoff", type=float, default=0, help="Minimum profit margin percentage")
    args = parser.parse_args()

    config = Config(args.region, args.unformatted, args.cutoff)
    arbitrage_finder = ArbitrageFinder(config)
    arbitrage_finder.find_arbitrage()

if __name__ == "__main__":
    main()
