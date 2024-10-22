from odds_api import OddsAPI
import json
from datetime import datetime
from collections import defaultdict

class ArbitrageFinder:
    def __init__(self, config):
        self.config = config
        self.odds_api = OddsAPI(config)

    def find_arbitrage(self):
        sports = self.odds_api.get_sports()
        print(f"Analyzing {len(sports)} in-season sports...")
        
        total_events = 0
        total_arbs = 0
        all_arbs = []
        
        for sport in sports:
            odds = self.odds_api.get_odds(sport['key'])
            if self.odds_api.api_limit_reached:
                print("API limit reached. Stopping analysis.")
                break
            if odds:
                total_events += len(odds)
                arbs = self.calculate_arbitrage(odds)
                total_arbs += len(arbs)
                all_arbs.extend(arbs)
                if not self.config.unformatted and arbs:
                    self.output_results(arbs, sport['title'])

        print(f"\nSummary:")
        print(f"Total events analyzed: {total_events}")
        print(f"Total arbitrage opportunities found: {total_arbs}")
        
        if not self.config.offline_file:
            print("\nAPI Usage:")
            print(f"Remaining requests: {self.odds_api.remaining_requests}")
            print(f"Used requests: {self.odds_api.used_requests}")

        return {
            "total_events": total_events,
            "total_arbitrage_opportunities": total_arbs,
            "arbitrage_opportunities": all_arbs,
            "api_usage": {
                "remaining_requests": self.odds_api.remaining_requests,
                "used_requests": self.odds_api.used_requests
            } if not self.config.offline_file else None
        }

    def calculate_arbitrage(self, odds):
        arbs = []
        for event in odds:
            best_odds_list = self.get_best_odds(event)
            for best_odds, bookmakers, total_points in best_odds_list:
                if best_odds:
                    implied_prob = 1/best_odds['Over'] + 1/best_odds['Under']
                    
                    if implied_prob < 1:
                        profit_margin = (1 / implied_prob - 1) * 100
                        if profit_margin >= self.config.cutoff:
                            arbs.append({
                                'event': event['home_team'] + ' vs ' + event['away_team'],
                                'profit_margin': profit_margin,
                                'best_odds': best_odds,
                                'bookmakers': bookmakers,
                                'commence_time': event['commence_time'],
                                'total_points': total_points
                            })
        return arbs

    def get_best_odds(self, event):
        odds_by_points = defaultdict(lambda: {'Over': 0, 'Under': 0})
        bookmakers_by_points = defaultdict(lambda: {'Over': '', 'Under': ''})
        
        if 'bookmakers' in event and isinstance(event['bookmakers'], list):
            for bookmaker in event['bookmakers']:
                if 'markets' in bookmaker and isinstance(bookmaker['markets'], list):
                    for market in bookmaker['markets']:
                        if market['key'] == self.config.market:
                            for outcome in market['outcomes']:
                                total_points = outcome.get('point')
                                if total_points is not None:
                                    if outcome['name'] == 'Over' and outcome['price'] > odds_by_points[total_points]['Over']:
                                        odds_by_points[total_points]['Over'] = outcome['price']
                                        bookmakers_by_points[total_points]['Over'] = bookmaker['title']
                                    elif outcome['name'] == 'Under' and outcome['price'] > odds_by_points[total_points]['Under']:
                                        odds_by_points[total_points]['Under'] = outcome['price']
                                        bookmakers_by_points[total_points]['Under'] = bookmaker['title']
        
        best_odds_list = []
        for total_points, odds in odds_by_points.items():
            if odds['Over'] > 0 and odds['Under'] > 0:
                best_odds_list.append((odds, bookmakers_by_points[total_points], total_points))
        
        return best_odds_list

    def output_results(self, arbs, sport_title):
        if arbs:
            print(f"\nArbitrage opportunities for {sport_title}:")
            for arb in arbs:
                print(f"  Event: {arb['event']}")
                print(f"  Date: {self.format_date(arb['commence_time'])}")
                print(f"  Profit Margin: {arb['profit_margin']:.2f}%")
                print(f"  Total Points: {arb['total_points']}")
                print("  Best Odds and Bookmakers:")
                for outcome, odd in arb['best_odds'].items():
                    bookmaker = arb['bookmakers'][outcome]
                    print(f"    {outcome} {arb['total_points']}: {odd:.2f} ({bookmaker})")
                
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
        for outcome, bet in bets.items():
            print(f"  {arb['bookmakers'][outcome]}: ${bet:.2f} on {outcome} {arb['total_points']} @ {arb['best_odds'][outcome]:.2f}")

        print(f"\nTotal stake: ${total_stake:.2f}")
        for outcome, ret in returns.items():
            print(f"Return if {outcome} {arb['total_points']}: ${ret:.2f}")
        
        profit = min(returns.values()) - total_stake
        print(f"\nGuaranteed profit: ${profit:.2f} ({(profit/total_stake)*100:.2f}%)")

    def calculate_bets(self, arb, bet_amount, rounding):
        odds = arb['best_odds']
        implied_probs = {team: 1/odd for team, odd in odds.items()}
        total_implied_prob = sum(implied_probs.values())
        
        # Calculate the actual profit margin
        profit_margin = 1 - total_implied_prob
        
        # Scale bets to the user's input amount
        bets = {team: bet_amount * (prob / total_implied_prob) for team, prob in implied_probs.items()}
        
        if rounding:
            bets = {team: round(bet / rounding) * rounding for team, bet in bets.items()}
        
        total_stake = sum(bets.values())
        returns = {team: bets[team] * odds[team] for team in odds.keys()}

        return total_stake, bets, returns

    def format_date(self, date_string):
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date.strftime('%Y-%m-%d %H:%M:%S %Z')
