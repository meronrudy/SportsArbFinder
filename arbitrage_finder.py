from odds_api import OddsAPI
import json
from datetime import datetime
from collections import defaultdict
import logging

class ArbitrageFinder:
    def __init__(self, config):
        self.config = config
        self.odds_api = OddsAPI(config)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(filename='arbitrage_finder.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def find_arbitrage(self):
        sports = self.odds_api.get_sports()
        logging.info(f"Analyzing {len(sports)} in-season sports...")
        
        total_events = 0
        total_arbs = 0
        all_arbs = []
        
        for sport in sports:
            odds = self.odds_api.get_odds(sport['key'])
            if self.odds_api.api_limit_reached:
                logging.warning("API limit reached. Stopping analysis.")
                break
            if odds:
                total_events += len(odds)
                arbs = self.calculate_arbitrage(odds)
                total_arbs += len(arbs)
                all_arbs.extend(arbs)
                if not self.config.unformatted and arbs:
                    self.output_results(arbs, sport['title'])

        logging.info(f"\nSummary:")
        logging.info(f"Total events analyzed: {total_events}")
        logging.info(f"Total arbitrage opportunities found: {total_arbs}")
        
        if not self.config.offline_file:
            logging.info("\nAPI Usage:")
            logging.info(f"Remaining requests: {self.odds_api.remaining_requests}")
            logging.info(f"Used requests: {self.odds_api.used_requests}")

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
            best_odds, bookmakers, total_points = self.get_best_odds(event)
            if best_odds:
                if self.config.market == 'h2h':
                    implied_prob = sum(1 / odd for odd in best_odds.values())
                elif self.config.market in ['totals', 'spreads']:
                    implied_prob = 1/best_odds['Over'] + 1/best_odds['Under']
                else:
                    logging.warning(f"Unsupported market: {self.config.market}")
                    continue

                logging.info(f"Event: {event['home_team']} vs {event['away_team']}, Implied Prob: {implied_prob}")
                
                if implied_prob < 1:
                    profit_margin = (1 / implied_prob - 1) * 100
                    logging.info(f"Potential arbitrage found! Profit Margin: {profit_margin}%")
                    if profit_margin >= self.config.cutoff:
                        arb = {
                            'event': event['home_team'] + ' vs ' + event['away_team'],
                            'profit_margin': profit_margin,
                            'best_odds': best_odds,
                            'bookmakers': bookmakers,
                            'commence_time': event['commence_time'],
                            'market': self.config.market
                        }
                        if total_points is not None:
                            arb['total_points'] = total_points
                        arbs.append(arb)
                    else:
                        logging.info(f"Profit margin {profit_margin}% below cutoff {self.config.cutoff}%")
                else:
                    logging.info("No arbitrage opportunity")
            else:
                logging.info(f"No valid odds for {event['home_team']} vs {event['away_team']}")
        return arbs

    def get_best_odds(self, event):
        if self.config.market == 'h2h':
            return self.get_best_odds_h2h(event)
        elif self.config.market == 'totals':
            return self.get_best_odds_totals(event)
        elif self.config.market == 'spreads':
            return self.get_best_odds_spreads(event)
        else:
            logging.warning(f"Unsupported market: {self.config.market}")
            return None, None, None

    def get_best_odds_h2h(self, event):
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
        return (best_odds, bookmakers, None) if len(best_odds) > 1 else (None, None, None)

    def get_best_odds_totals(self, event):
        odds_by_points = defaultdict(lambda: {'Over': 0, 'Under': 0})
        bookmakers_by_points = defaultdict(lambda: {'Over': '', 'Under': ''})
        
        if 'bookmakers' in event and isinstance(event['bookmakers'], list):
            for bookmaker in event['bookmakers']:
                if 'markets' in bookmaker and isinstance(bookmaker['markets'], list):
                    for market in bookmaker['markets']:
                        if market['key'] == 'totals':
                            for outcome in market['outcomes']:
                                total_points = outcome.get('point')
                                if total_points is not None:
                                    if outcome['name'] == 'Over' and outcome['price'] > odds_by_points[total_points]['Over']:
                                        odds_by_points[total_points]['Over'] = outcome['price']
                                        bookmakers_by_points[total_points]['Over'] = bookmaker['title']
                                    elif outcome['name'] == 'Under' and outcome['price'] > odds_by_points[total_points]['Under']:
                                        odds_by_points[total_points]['Under'] = outcome['price']
                                        bookmakers_by_points[total_points]['Under'] = bookmaker['title']
        
        best_odds = None
        best_bookmakers = None
        best_total_points = None
        best_implied_prob = float('inf')

        for total_points, odds in odds_by_points.items():
            if odds['Over'] > 0 and odds['Under'] > 0:
                implied_prob = 1/odds['Over'] + 1/odds['Under']
                if implied_prob < best_implied_prob:
                    best_implied_prob = implied_prob
                    best_odds = odds.copy()  # Create a copy to avoid modifying the original
                    best_bookmakers = bookmakers_by_points[total_points]
                    best_total_points = total_points

        if best_odds:
            return best_odds, best_bookmakers, best_total_points
        else:
            return None, None, None

    def get_best_odds_spreads(self, event):
        # Implement this method similar to get_best_odds_totals if needed
        # For now, return a placeholder
        return None, None, None

    def output_results(self, arbs, sport_title):
        if arbs:
            logging.info(f"\nArbitrage opportunities for {sport_title}:")
            for arb in arbs:
                logging.info(f"  Event: {arb['event']}")
                logging.info(f"  Date: {self.format_date(arb['commence_time'])}")
                logging.info(f"  Profit Margin: {arb['profit_margin']:.2f}%")
                logging.info(f"  Market: {arb['market']}")
                if 'total_points' in arb:
                    logging.info(f"  Total Points: {arb['total_points']}")
                logging.info("  Best Odds and Bookmakers:")
                for outcome, odd in arb['best_odds'].items():
                    if outcome != 'total_points':  # Skip 'total_points' when iterating over odds
                        bookmaker = arb['bookmakers'][outcome]
                        if arb['market'] == 'totals':
                            total_points = arb.get('total_points', 'N/A')
                            logging.info(f"    {outcome} {total_points}: {odd:.2f} ({bookmaker})")
                        else:
                            logging.info(f"    {outcome}: {odd:.2f} ({bookmaker})")
                
                if self.config.interactive:
                    self.interactive_calculator(arb)
                logging.info("")

    def interactive_calculator(self, arb):
        logging.info("\nBetting Calculator:")
        rounding_options = {
            '1': "Don't round",
            '2': "Round to nearest $1",
            '3': "Round to nearest $5",
            '4': "Round to nearest $10"
        }
        
        for key, value in rounding_options.items():
            logging.info(f"{key}. {value}")
        
        rounding_choice = input("Choose rounding option (1-4): ")
        rounding = int(rounding_options[rounding_choice].split('$')[-1]) if rounding_choice != '1' else 0

        bet_amount = float(input("Enter total stake amount: $"))

        total_stake, bets, returns = self.calculate_bets(arb, bet_amount, rounding)

        logging.info("\nOptimal bets:")
        for outcome, bet in bets.items():
            logging.info(f"  {arb['bookmakers'][outcome]}: ${bet:.2f} on {outcome} {arb['total_points']} @ {arb['best_odds'][outcome]:.2f}")

        logging.info(f"\nTotal stake: ${total_stake:.2f}")
        for outcome, ret in returns.items():
            logging.info(f"Return if {outcome} {arb['total_points']}: ${ret:.2f}")
        
        profit = min(returns.values()) - total_stake
        logging.info(f"\nGuaranteed profit: ${profit:.2f} ({(profit/total_stake)*100:.2f}%)")

    def calculate_bets(self, arb, bet_amount, rounding):
        odds = arb['best_odds']
        implied_probs = {team: 1/odd for team, odd in odds.items()}
        total_implied_prob = sum(implied_probs.values())
        
        # Calculate the actual profit margin
        profit_margin = (1 / total_implied_prob) - 1
        
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
