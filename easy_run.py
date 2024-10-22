import subprocess
import sys
import time

def get_user_input(prompt, choices=None):
    while True:
        user_input = input(prompt).strip()
        if choices is None or user_input in choices:
            return user_input
        print("Invalid input. Please try again.")

def main():
    print("Welcome to the Sports Betting Arbitrage Finder Easy Run!")
    print("Let's configure your run:")

    # Region
    region = get_user_input("Choose a region (eu/us/uk/au) [default: us]: ", ["", "eu", "us", "uk", "au"]) or "us"

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
    command = [sys.executable, "main.py", "-r", region, "-c", cutoff, "-s", "response_data.json"]
    if interactive:
        command.append("-i")
    if offline_file:
        command.extend(["-o", offline_file])

    # Run the command
    print("\nRunning the arbitrage finder...")
    subprocess.run(command)

    # Wait for a moment to ensure the JSON file is written
    time.sleep(2)

    # Run the viewer
    print("\nLaunching the arbitrage opportunities viewer...")
    subprocess.run([sys.executable, "viewer.py"])

if __name__ == "__main__":
    main()
