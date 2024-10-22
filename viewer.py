import json
import webbrowser
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import signal
import sys
from datetime import datetime, timezone

def format_date(date_string):
    date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    return date.strftime('%Y-%m-%d %I:%M %p %Z')

def calculate_profit_and_payout(arb, wager):
    total_implied_prob = sum(1/odd for odd in arb['best_odds'].values())
    profit_margin = (1 / total_implied_prob - 1)
    profit = wager * profit_margin
    payout = wager + profit
    return profit, payout

def generate_html(data):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Arbitrage Opportunities Viewer</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
            }}
            .summary {{
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .opportunity {{
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
            }}
            .opportunity h2 {{
                color: #2980b9;
                margin-top: 0;
            }}
            .odds {{
                display: flex;
                justify-content: space-between;
            }}
            .odds div {{
                flex: 1;
                padding: 10px;
                background-color: #e8f6fe;
                margin: 5px;
                border-radius: 3px;
            }}
            #wager-input {{
                margin-bottom: 20px;
                padding: 10px;
                background-color: #e8f6fe;
                border-radius: 5px;
            }}
            #wager-input input {{
                margin-left: 10px;
                padding: 5px;
            }}
            #wager-input button {{
                margin-left: 10px;
                padding: 5px 10px;
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }}
            .profit-payout {{
                margin-top: 10px;
                font-weight: bold;
            }}
        </style>
        <script>
            function updateProfits() {{
                const wager = parseFloat(document.getElementById('wager').value);
                if (isNaN(wager) || wager <= 0) {{
                    alert('Please enter a valid wager amount.');
                    return;
                }}
                const opportunities = document.getElementsByClassName('opportunity');
                for (let opp of opportunities) {{
                    const profitMargin = parseFloat(opp.getAttribute('data-profit-margin')) / 100;
                    const profit = wager * profitMargin;
                    const payout = wager + profit;
                    opp.querySelector('.profit').textContent = profit.toFixed(2);
                    opp.querySelector('.payout').textContent = payout.toFixed(2);
                    
                    const bets = opp.querySelectorAll('.bet-amount');
                    const totalImpliedProb = parseFloat(opp.getAttribute('data-total-implied-prob'));
                    bets.forEach(bet => {{
                        const impliedProb = parseFloat(bet.getAttribute('data-implied-prob'));
                        const betAmount = (wager * impliedProb / totalImpliedProb).toFixed(2);
                        bet.textContent = betAmount;
                    }});
                }}
            }}
            
            // Initial update
            updateProfits();
        </script>
    </head>
    <body>
        <h1>Arbitrage Opportunities Viewer</h1>
        <div id="wager-input">
            <label for="wager">Enter wager amount: $</label>
            <input type="number" id="wager" min="0" step="0.01" value="100">
            <button onclick="updateProfits()">Update Profits</button>
        </div>
        <div class="summary">
            <h2>Summary</h2>
            <p>Total events analyzed: {total_events}</p>
            <p>Total arbitrage opportunities found: {total_arbs}</p>
        </div>
        <div id="opportunities">
            {opportunities}
        </div>
    </body>
    </html>
    """

    # Sort arbitrage opportunities by profit margin in descending order
    sorted_arbs = sorted(data['arbitrage_opportunities'], key=lambda x: x['profit_margin'], reverse=True)

    opportunities_html = ""
    for arb in sorted_arbs:
        total_implied_prob = sum(1/odd for odd in arb['best_odds'].values())
        opportunities_html += f"""
        <div class="opportunity" data-profit-margin="{arb['profit_margin']}" data-total-implied-prob="{total_implied_prob}">
            <h2>{arb['event']}</h2>
            <p>Profit Margin: {arb['profit_margin']:.2f}%</p>
            <p>Date: {format_date(arb['commence_time'])}</p>
            <p>Market: {arb.get('market', 'N/A')}</p>
            <p>Total Points: {arb.get('total_points', 'N/A')}</p>
            <div class="odds">
        """
        for outcome, odd in arb['best_odds'].items():
            bookmaker = arb['bookmakers'][outcome]
            implied_prob = 1 / odd
            opportunities_html += f"""
                <div>
                    <h3>{outcome}</h3>
                    <p>Odds: {odd:.2f}</p>
                    <p>Bookmaker: {bookmaker}</p>
                    <p>Bet Amount: $<span class="bet-amount" data-implied-prob="{implied_prob}">0.00</span></p>
                </div>
            """
        opportunities_html += """
            </div>
            <div class="profit-payout">
                <p>Profit: $<span class="profit">0.00</span></p>
                <p>Payout: $<span class="payout">0.00</span></p>
            </div>
        </div>
        """

    return html_template.format(
        total_events=data['total_events'],
        total_arbs=data['total_arbitrage_opportunities'],
        opportunities=opportunities_html
    )

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server running on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.shutdown()

def signal_handler(sig, frame):
    print("\nExiting the viewer. Goodbye!")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    with open('arbitrage_results.json', 'r') as f:
        data = json.load(f)

    html_content = generate_html(data)
    
    with open('arbitrage_viewer.html', 'w') as f:
        f.write(html_content)

    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Open the default web browser
    webbrowser.open('http://localhost:8000/arbitrage_viewer.html')

    print("Press Ctrl+C to stop the server and exit.")
    try:
        # Keep the main thread alive
        while True:
            signal.pause()
    except KeyboardInterrupt:
        print("\nExiting the viewer. Goodbye!")

if __name__ == "__main__":
    main()
