import subprocess
import sys
import time
import signal

def get_user_input(prompt, choices=None):
    while True:
        user_input = input(prompt).strip()
        if choices is None or user_input in choices:
            return user_input
        print("Invalid input. Please try again.")

def signal_handler(sig, frame):
    print("\nExiting the program. Goodbye!")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("Welcome to the Sports Betting Arbitrage Finder Easy Run!")
    print("Let's configure your run:")

    # Region
    region = get_user_input("Choose a region (eu/us/uk/au) [default: us]: ", ["", "eu", "us", "uk", "au"]) or "us"

    # Betting Market
    market_options = {
        "1": "h2h",
        "2": "spreads",
        "3": "totals",
        "4": "outrights",
        "5": "h2h_lay",
        "6": "outrights_lay"
    }
    print("\nChoose a betting market:")
    for key, value in market_options.items():
        print(f"{key}. {value}")
    market_choice = get_user_input("Enter your choice (1-6) [default: 1]: ", ["", "1", "2", "3", "4", "5", "6"]) or "1"
    market = market_options[market_choice]

    # Cutoff
    cutoff = get_user_input("Enter minimum profit margin percentage [default: 0]: ") or "0"

    # Interactive mode
    interactive = get_user_input("Enable interactive betting calculator? (y/n) [default: n]: ", ["", "y", "n", "Y", "N"]) or "n"
    interactive = interactive.lower() == "y"

    # Offline mode
    offline = get_user_input("Use offline data? (y/n) [default: n]: ", ["", "y", "n", "Y", "N"]) or "n"
    if offline.lower() == "y":
        offline_file = get_user_input("Enter the name of the offline data file [default: response_data.json]: ") or "response_data.json"
    else:
        offline_file = None

    # Build the command
    command = [sys.executable, "main.py", "-r", region, "-c", cutoff, "-s", "response_data.json", "--market", market]
    if interactive:
        command.append("-i")
    if offline_file:
        command.extend(["-o", offline_file])

    # Run the command
    print("\nRunning the arbitrage finder...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print("An error occurred while running the arbitrage finder.")
        return
    except KeyboardInterrupt:
        print("\nArbitrage finder interrupted. Exiting.")
        return

    # Wait for a moment to ensure the JSON file is written
    time.sleep(2)

    # Run the viewer
    print("\nLaunching the arbitrage opportunities viewer...")
    try:
        subprocess.run([sys.executable, "viewer.py"], check=True)
    except subprocess.CalledProcessError:
        print("An error occurred while running the viewer.")
    except KeyboardInterrupt:
        print("\nViewer interrupted. Exiting.")

if __name__ == "__main__":
    main()
