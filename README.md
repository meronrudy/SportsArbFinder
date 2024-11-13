# Sports Betting Arbitrage Finder

This project is an advanced arbitrage finder for sports betting. It identifies arbitrage opportunities across multiple bookmakers and calculates optimal bet amounts for each outcome to guarantee a profit. 

Uses The Odds API.

## Features

- Supports multiple regions (EU, US, UK, AU)
- Customizable profit margin cutoff
- Formatted and unformatted output options
- Utilizes The Odds API for real-time betting data
- Interactive betting calculator
- Offline mode for testing and development
- Ability to save API responses for later analysis
- Easy run script for quick setup and execution

## Installation

1. Clone this repository:   ```
   git clone https://github.com/carterlasalle/SportsArbFinder
   cd SportsArbFinder   ```

2. Install the required packages:   ```
   pip install -r requirements.txt   ```

3. Create a `.env` file in the project root and add your API key (get one [here](https://the-odds-api.com/)):   ```
   ODDS_API_KEY=your_api_key_here   ```

## Usage

### Easy Run (Recommended for most users)

1. Run the easy run script:   ```
   python easy_run.py   ```

2. Follow the prompts to configure your run:
   - Choose a region (eu/us/uk/au)
   - Set the minimum profit margin percentage
   - Enable or disable the interactive betting calculator
   - Choose to use offline data or fetch new data

3. The script will automatically run the arbitrage finder and launch the viewer in your default web browser.

### Advanced Usage

For more control over the execution, you can use the main script directly:

python main.py [options]


#### Command-line Options

- `-r`, `--region`: Specify the region for bookmakers (eu, us, uk, au). Default is "us".
- `-u`, `--unformatted`: Skip interactive UI and only output JSON data.
- `-c`, `--cutoff`: Set the minimum profit margin percentage. Default is 0.
- `--api-key`: Provide the API key for The Odds API (overrides the .env file).
- `-i`, `--interactive`: Enable the interactive betting calculator.
- `-s`, `--save`: Save the API response to a specified file.
- `-o`, `--offline`: Use offline data from a specified file instead of making API calls.
- `--includeLinks`: Include bookmaker links in the response.
- `--includeSids`: Include source ids in the response.
- `--includeBetLimits`: Include bet limits in the response.

#### Examples

1. Basic usage (US region):
   ```
   python main.py
   ```

2. Set region to UK and minimum profit margin to 2%:
   ```
   python main.py -r uk -c 2
   ```

3. Enable interactive betting calculator:
   ```
   python main.py -i
   ```

4. Save API response to a file:
   ```
   python main.py -s response_data.json
   ```

5. Use offline data:
   ```
   python main.py -o response_data.json
   ```

6. Include bookmaker links and source ids in the response:
   ```
   python main.py --includeLinks --includeSids
   ```

7. Include bet limits in the response:
   ```
   python main.py --includeBetLimits
   ```

## How It Works

1. The script fetches data for all in-season sports from The Odds API.
2. For each sport, it retrieves the latest odds from various bookmakers.
3. It calculates the best available odds for each outcome across all bookmakers.
4. If the combined implied probability is less than 100%, an arbitrage opportunity exists.
5. The script calculates the profit margin and, if it meets the cutoff, displays the opportunity.
6. In interactive mode, users can input a stake amount and see the optimal bet distribution.
7. Results are saved to `arbitrage_results.json`.
8. The viewer script generates an HTML page to display the results and launches it in the default web browser.

## Project Structure

- `main.py`: Entry point of the application, handles command-line arguments.
- `arbitrage_finder.py`: Contains the core logic for finding arbitrage opportunities.
- `odds_api.py`: Handles API requests to The Odds API.
- `config.py`: Stores configuration settings.
- `easy_run.py`: Provides a user-friendly interface for running the arbitrage finder.
- `viewer.py`: Generates an HTML viewer for the arbitrage results.

## Limitations

- The free tier of The Odds API has usage limits. Monitor your usage to avoid exceeding these limits.
- Arbitrage opportunities can disappear quickly. Always verify the odds before placing actual bets.
- This tool is for educational purposes only. Be aware of the legal status of sports betting in your jurisdiction.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

This tool is for educational purposes only. The authors are not responsible for any financial losses incurred from using this software. Always gamble responsibly and be aware of the risks involved in sports betting.
