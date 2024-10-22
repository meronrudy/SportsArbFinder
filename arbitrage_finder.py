from odds_api import OddsAPI
import json
from datetime import datetime
from collections import defaultdict
import logging
from difflib import get_close_matches

class ArbitrageFinder:
    def __init__(self, config):
        self.config = config
        self.odds_api = OddsAPI(config)
        self.setup_logging()
        self.team_name_cache = {}  # Cache for standardized team names

    def setup_logging(self):
        logging.basicConfig(filename='arbitrage_finder.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def find_arbitrage(self):
        try:
            sports = self.odds_api.get_sports()
            if not sports:
                logging.error("Failed to fetch sports data")
                return self.create_empty_result()

            logging.info(f"Analyzing {len(sports)} in-season sports...")
            
            total_events = 0
            total_arbs = 0
            all_arbs = []
            
            for sport in sports:
                try:
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
                except Exception as e:
                    logging.error(f"Error processing sport {sport['key']}: {str(e)}")
                    continue

            return {
                "total_events": total_events,
                "total_arbitrage_opportunities": total_arbs,
                "arbitrage_opportunities": all_arbs,
                "api_usage": {
                    "remaining_requests": self.odds_api.remaining_requests,
                    "used_requests": self.odds_api.used_requests
                } if not self.config.offline_file else None
            }
        except Exception as e:
            logging.error(f"Fatal error in find_arbitrage: {str(e)}")
            return self.create_empty_result()

    def create_empty_result(self):
        return {
            "total_events": 0,
            "total_arbitrage_opportunities": 0,
            "arbitrage_opportunities": [],
            "api_usage": None
        }

    def calculate_arbitrage(self, odds):
        arbs = []
        for event in odds:
            best_odds, bookmakers, points = self.get_best_odds(event)
            if best_odds:
                if self.config.market == 'h2h':
                    implied_prob = sum(1 / odd for odd in best_odds.values())
                elif self.config.market == 'spreads':
                    # Filter out the 'spread' key for implied probability calculation
                    odds_without_spread = {k: v for k, v in best_odds.items() if k != 'spread'}
                    implied_prob = sum(1 / odd for odd in odds_without_spread.values())
                elif self.config.market == 'totals':
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
                        if points is not None:
                            arb['points'] = points
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

    def standardize_team_name(self, team_name, event_teams):
        """
        Standardize team names using fuzzy matching.
        Cache results to improve performance.
        """
        if not team_name:
            return None
            
        cache_key = (team_name.lower(), tuple(sorted(event_teams)))
        if cache_key in self.team_name_cache:
            return self.team_name_cache[cache_key]

        matches = get_close_matches(team_name.lower(), [t.lower() for t in event_teams], n=1, cutoff=0.6)
        if matches:
            standardized = next(t for t in event_teams if t.lower() == matches[0])
            self.team_name_cache[cache_key] = standardized
            return standardized
        
        logging.warning(f"No match found for team name: {team_name}")
        return None

    def get_best_odds_spreads(self, event):
        event_teams = [event['home_team'], event['away_team']]
        odds_by_points = defaultdict(lambda: {'Favorite': {'odds': 0, 'team': None}, 
                                            'Underdog': {'odds': 0, 'team': None},
                                            'Even': {'odds': 0, 'team': None}})
        bookmakers_by_points = defaultdict(lambda: {'Favorite': '', 'Underdog': '', 'Even': ''})
        
        if 'bookmakers' in event and isinstance(event['bookmakers'], list):
            for bookmaker in event['bookmakers']:
                if 'markets' in bookmaker and isinstance(bookmaker['markets'], list):
                    for market in bookmaker['markets']:
                        if market['key'] == 'spreads':
                            for outcome in market['outcomes']:
                                point = outcome.get('point')
                                if point is not None:
                                    # Standardize team name
                                    team_name = self.standardize_team_name(outcome['name'], event_teams)
                                    if not team_name:
                                        continue

                                    point_key = point  # Keep the actual point value
                                    
                                    # Determine side based on point value
                                    if point < 0:
                                        side = 'Favorite'
                                    elif point > 0:
                                        side = 'Underdog'
                                    else:  # point == 0
                                        side = 'Even'

                                    if outcome['price'] > odds_by_points[point_key][side]['odds']:
                                        odds_by_points[point_key][side] = {
                                            'odds': outcome['price'],
                                            'team': team_name
                                        }
                                        bookmakers_by_points[point_key][side] = bookmaker['title']
        
        # Find the best arbitrage opportunity across all point spreads
        best_odds = None
        best_bookmakers = None
        best_points = None
        best_implied_prob = float('inf')

        for point, sides in odds_by_points.items():
            if point == 0:  # Handle pick'em games
                if sides['Even']['odds'] > 0:
                    implied_prob = 2 / sides['Even']['odds']  # Both sides have same odds
                    if implied_prob < best_implied_prob:
                        best_implied_prob = implied_prob
                        best_odds = {
                            event['home_team']: sides['Even']['odds'],
                            event['away_team']: sides['Even']['odds']
                        }
                        best_bookmakers = {
                            event['home_team']: bookmakers_by_points[point]['Even'],
                            event['away_team']: bookmakers_by_points[point]['Even']
                        }
                        best_points = 0
            else:
                if (sides['Favorite']['odds'] > 0 and sides['Underdog']['odds'] > 0 and
                    sides['Favorite']['team'] and sides['Underdog']['team']):
                    implied_prob = 1/sides['Favorite']['odds'] + 1/sides['Underdog']['odds']
                    if implied_prob < best_implied_prob:
                        best_implied_prob = implied_prob
                        best_odds = {
                            sides['Favorite']['team']: sides['Favorite']['odds'],
                            sides['Underdog']['team']: sides['Underdog']['odds']
                        }
                        best_bookmakers = {
                            sides['Favorite']['team']: bookmakers_by_points[point]['Favorite'],
                            sides['Underdog']['team']: bookmakers_by_points[point]['Underdog']
                        }
                        best_points = point

        if best_odds:
            # Add spread information to best_odds
            best_odds['spread'] = best_points
            return best_odds, best_bookmakers, best_points
        else:
            return None, None, None

    def output_results(self, arbs, sport_title):
        if arbs:
            logging.info(f"\nArbitrage opportunities for {sport_title}:")
            for arb in arbs:
                try:
                    logging.info(f"  Event: {arb['event']}")
                    logging.info(f"  Date: {self.format_date(arb['commence_time'])}")
                    logging.info(f"  Profit Margin: {arb['profit_margin']:.2f}%")
                    logging.info(f"  Market: {arb['market']}")
                    if 'points' in arb:
                        logging.info(f"  Points Spread: {arb['points']}")
                    logging.info("  Best Odds and Bookmakers:")
                    
                    for outcome, odd in arb['best_odds'].items():
                        if outcome != 'spread':  # Skip the spread key when displaying odds
                            bookmaker = arb['bookmakers'][outcome]
                            if arb['market'] == 'totals':
                                points = arb.get('points', 'N/A')
                                logging.info(f"    {outcome} {points}: {odd:.2f} ({bookmaker})")
                            elif arb['market'] == 'spreads':
                                spread = f"+{arb['points']}" if outcome == 'Underdog' else f"-{arb['points']}"
                                logging.info(f"    {outcome} ({spread}): {odd:.2f} ({bookmaker})")
                            else:
                                logging.info(f"    {outcome}: {odd:.2f} ({bookmaker})")
                    
                    if self.config.interactive:
                        self.interactive_calculator(arb)
                    logging.info("")
                
                except KeyError as e:
                    logging.error(f"Missing key in arbitrage data: {str(e)}")
                    continue
                except Exception as e:
                    logging.error(f"Error displaying arbitrage opportunity: {str(e)}")
                    continue

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
            logging.info(f"  {arb['bookmakers'][outcome]}: ${bet:.2f} on {outcome} {arb['points']} @ {arb['best_odds'][outcome]:.2f}")

        logging.info(f"\nTotal stake: ${total_stake:.2f}")
        for outcome, ret in returns.items():
            logging.info(f"Return if {outcome} {arb['points']}: ${ret:.2f}")
        
        profit = min(returns.values()) - total_stake
        logging.info(f"\nGuaranteed profit: ${profit:.2f} ({(profit/total_stake)*100:.2f}%)")

    def calculate_bets(self, arb, bet_amount, rounding):
        try:
            odds = arb['best_odds']
            implied_probs = {team: 1/odd for team, odd in odds.items()}
            total_implied_prob = sum(implied_probs.values())
            
            # Calculate the actual profit margin
            profit_margin = (1 / total_implied_prob) - 1
            
            # Calculate initial bets
            bets = {team: bet_amount * (prob / total_implied_prob) for team, prob in implied_probs.items()}
            
            if rounding:
                # Round bets while maintaining total stake
                rounded_bets = {}
                remaining_stake = bet_amount
                teams = list(bets.keys())
                
                # Check if rounding unit is too large for the bet amount
                if rounding > bet_amount:
                    logging.error(f"Rounding unit (${rounding}) is larger than bet amount (${bet_amount})")
                    return bet_amount, bets, {team: bet * odds[team] for team, bet in bets.items()}
                
                # Round all but the last bet
                for team in teams[:-1]:
                    rounded_bet = round(bets[team] / rounding) * rounding
                    rounded_bets[team] = rounded_bet
                    remaining_stake -= rounded_bet
                
                # Handle the last bet carefully
                if remaining_stake < rounding / 2:
                    # Redistribute the small remainder across other bets
                    logging.warning(f"Remaining stake (${remaining_stake:.2f}) is too small to round. Redistributing...")
                    adjustment = remaining_stake / (len(teams) - 1)
                    for team in teams[:-1]:
                        rounded_bets[team] += adjustment
                    rounded_bets[teams[-1]] = 0
                else:
                    # Round the remaining stake normally
                    rounded_bets[teams[-1]] = round(remaining_stake / rounding) * rounding
                
                # Verify the rounded bets
                total_rounded = sum(rounded_bets.values())
                if abs(total_rounded - bet_amount) > 0.01:  # Allow for small floating-point differences
                    logging.warning(f"Rounding resulted in stake mismatch. Original: ${bet_amount:.2f}, Rounded: ${total_rounded:.2f}")
                
                bets = rounded_bets
            
            total_stake = sum(bets.values())
            returns = {team: bets[team] * odds[team] for team in odds.keys()}
            
            # Verify the arbitrage still exists after rounding
            min_return = min(returns.values())
            max_return = max(returns.values())
            if min_return < total_stake:
                logging.error(f"Warning: Rounding has eliminated the arbitrage. Minimum return (${min_return:.2f}) is less than stake (${total_stake:.2f})")
            if max_return - min_return > 0.01:
                logging.warning(f"Returns are not perfectly balanced. Variation: ${max_return - min_return:.2f}")

            return total_stake, bets, returns
        
        except KeyError as e:
            logging.error(f"Missing key in arbitrage data: {str(e)}")
            print(f"Error: Invalid arbitrage data structure. Check the logs for details.")
            return 0, {}, {}
        except ZeroDivisionError:
            logging.error("Invalid odds (zero or negative) encountered")
            print("Error: Invalid odds encountered. Check the logs for details.")
            return 0, {}, {}
        except Exception as e:
            logging.error(f"Unexpected error calculating bets: {str(e)}")
            print("Error: An unexpected error occurred. Check the logs for details.")
            return 0, {}, {}

    def format_date(self, date_string):
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date.strftime('%Y-%m-%d %H:%M:%S %Z')

