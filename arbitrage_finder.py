from odds_api import OddsAPI
import json
from datetime import datetime

class ArbitrageFinder:
    def __init__(self, config):
        self.config = config
        self.odds_api = OddsAPI(config)

    def find_arbitrage(self):
        sports = self.odds_api.get_sports()
        print(f"Analyzing {len(sports)} in-season sports...")
        
        total_events = 0
        total_arbs = 0
        
        for sport in sports:
            odds = self.odds_api.get_odds(sport['key'])
            if self.odds_api.api_limit_reached:
                print("API limit reached. Stopping analysis.")
                break
            if odds:
                total_events += len(odds)
                arbs = self.calculate_arbitrage(odds)
                total_arbs += len(arbs)
                self.output_results(arbs, sport['title'])

        print(f"\nSummary:")
        print(f"Total events analyzed: {total_events}")
        print(f"Total arbitrage opportunities found: {total_arbs}")
        
        if not self.config.offline_file:
            print("\nAPI Usage:")
            print(f"Remaining requests: {self.odds_api.remaining_requests}")
            print(f"Used requests: {self.odds_api.used_requests}")

    def calculate_arbitrage(self, odds):
        arbs = []
        for event in odds:
            best_odds, bookmakers = self.get_best_odds(event)
            if best_odds:
                implied_prob = sum(1 / odd for odd in best_odds.values())
                if implied_prob < 1:
                    profit_margin = (1 / implied_prob - 1) * 100
                    if profit_margin >= self.config.cutoff:
                        arbs.append({
                            'event': event['home_team'] + ' vs ' + event['away_team'],
                            'profit_margin': profit_margin,
                            'best_odds': best_odds,
                            'bookmakers': bookmakers,
                            'commence_time': event['commence_time']
                        })
        return arbs

    def get_best_odds(self, event):
        best_odds = {}
        bookmakers = {}
        if 'bookmakers' in event and isinstance(event['bookmakers'], list):
            for bookmaker in event['bookmakers']:
                if 'markets' in bookmaker and isinstance(bookmaker['markets'], list):
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] not in best_odds or outcome['price'] > best_odds[outcome['name']]:
                                    best_odds[outcome['name']] = outcome['price']
                                    bookmakers[outcome['name']] = bookmaker['title']
        return (best_odds, bookmakers) if len(best_odds) > 1 else (None, None)

    def output_results(self, arbs, sport_title):
        if arbs:
            print(f"\nArbitrage opportunities for {sport_title}:")
            for arb in arbs:
                print(f"  Event: {arb['event']}")
                print(f"  Date: {self.format_date(arb['commence_time'])}")
                print(f"  Profit Margin: {arb['profit_margin']:.2f}%")
                print("  Best Odds and Bookmakers:")
                for team, odd in arb['best_odds'].items():
                    bookmaker = arb['bookmakers'][team]
                    print(f"    {team}: {odd:.2f} ({bookmaker})")
                
                if self.config.interactive:
                    self.interactive_calculator(arb)
                print()

    def interactive_calculator(self, arb):
        print("\nBetting Calculator:")
        rounding_options = {
            '1': "Don't round",
            '2': "Round to nearest $1",
            '3': "Round to nearest $5",
            '4': "Round to nearest $10"
        }
        
        for key, value in rounding_options.items():
            print(f"{key}. {value}")
        
        rounding_choice = input("Choose rounding option (1-4): ")
        rounding = int(rounding_options[rounding_choice].split('$')[-1]) if rounding_choice != '1' else 0

        bet_amount = float(input("Enter total stake amount: $"))

        total_stake, bets, returns = self.calculate_bets(arb, bet_amount, rounding)

        print("\nOptimal bets:")
        for team, bet in bets.items():
            print(f"  {arb['bookmakers'][team]}: ${bet:.2f} on {team} @ {arb['best_odds'][team]:.2f}")

        print(f"\nTotal stake: ${total_stake:.2f}")
        for team, ret in returns.items():
            print(f"Return if {team} wins: ${ret:.2f}")
        
        profit = min(returns.values()) - total_stake
        print(f"\nGuaranteed profit: ${profit:.2f} ({(profit/total_stake)*100:.2f}%)")

    def calculate_bets(self, arb, bet_amount, rounding):
        odds = arb['best_odds']
        implied_probs = {team: 1/odd for team, odd in odds.items()}
        total_implied_prob = sum(implied_probs.values())
        
        # Scale bets to the user's input amount
        scale_factor = bet_amount / (1 - total_implied_prob)
        bets = {team: scale_factor * prob for team, prob in implied_probs.items()}
        
        if rounding:
            bets = {team: round(bet / rounding) * rounding for team, bet in bets.items()}
        
        total_stake = sum(bets.values())
        returns = {team: bets[team] * odds[team] for team in odds.keys()}

        return total_stake, bets, returns

    def format_date(self, date_string):
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date.strftime('%Y-%m-%d %H:%M:%S %Z')
