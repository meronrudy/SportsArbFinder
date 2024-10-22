import json
import webbrowser
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

def generate_html(data):
    html = """
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
        </style>
    </head>
    <body>
        <h1>Arbitrage Opportunities Viewer</h1>
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

    opportunities_html = ""
    for arb in data['arbitrage_opportunities']:
        opportunities_html += f"""
        <div class="opportunity">
            <h2>{arb['event']}</h2>
            <p>Profit Margin: {arb['profit_margin']:.2f}%</p>
            <p>Date: {arb['commence_time']}</p>
            <div class="odds">
        """
        for team, odd in arb['best_odds'].items():
            bookmaker = arb['bookmakers'][team]
            opportunities_html += f"""
                <div>
                    <h3>{team}</h3>
                    <p>Odds: {odd:.2f}</p>
                    <p>Bookmaker: {bookmaker}</p>
                </div>
            """
        opportunities_html += """
            </div>
        </div>
        """

    return html.format(
        total_events=data['total_events'],
        total_arbs=data['total_arbitrage_opportunities'],
        opportunities=opportunities_html
    )

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server running on http://localhost:{port}")
    httpd.serve_forever()

def main():
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
        server_thread.join()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
