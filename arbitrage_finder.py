from odds_api import OddsAPI
import json

class ArbitrageFinder:
    def __init__(self, config):
        self.config = config
        self.odds_api = OddsAPI(config)

    def find_arbitrage(self):
        sports = self.odds_api.get_sports()
        for sport in sports:
            odds = self.odds_api.get_odds(sport['key'])
            if isinstance(odds, list):
                arbs = self.calculate_arbitrage(odds)
                self.output_results(arbs)
            else:
                print(f"Error fetching odds for {sport['key']}: {odds}")

    def calculate_arbitrage(self, odds):
        arbs = []
        for event in odds:
            if isinstance(event, dict):
                best_odds = self.get_best_odds(event)
                if best_odds:
                    implied_prob = sum(1 / odd for odd in best_odds.values())
                    if implied_prob < 1:
                        profit_margin = (1 - implied_prob) * 100
                        if profit_margin >= self.config.cutoff:
                            total_stake = 100  # Assuming a total stake of $100
                            stakes = {team: total_stake / odd for team, odd in best_odds.items()}
                            expected_profit = min(stake * odd for stake, odd in zip(stakes.values(), best_odds.values())) - total_stake
                            arbs.append({
                                'event': event['home_team'] + ' vs ' + event['away_team'],
                                'profit_margin': profit_margin,
                                'best_odds': best_odds,
                                'stakes': stakes,
                                'expected_profit': expected_profit
                            })
            else:
                print(f"Skipping invalid event data: {event}")
        return arbs

    def get_best_odds(self, event):
        best_odds = {}
        if 'bookmakers' in event and isinstance(event['bookmakers'], list):
            for bookmaker in event['bookmakers']:
                if 'markets' in bookmaker and isinstance(bookmaker['markets'], list):
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] not in best_odds or outcome['price'] > best_odds[outcome['name']]:
                                    best_odds[outcome['name']] = outcome['price']
        return best_odds if len(best_odds) > 1 else None

    def output_results(self, arbs):
        if self.config.unformatted:
            print(json.dumps(arbs))
        else:
            for arb in arbs:
                print(f"Event: {arb['event']}")
                print(f"Profit Margin: {arb['profit_margin']:.2f}%")
                print(f"Expected Profit: ${arb['expected_profit']:.2f}")
                print("Best Odds and Stakes:")
                for team, odd in arb['best_odds'].items():
                    stake = arb['stakes'][team]
                    print(f"  {team}: {odd} (Stake: ${stake:.2f})")
                print()
