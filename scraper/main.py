import json
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def load_websites_config():
    """Load websites configuration from a JSON file."""
    try:
        # Check if config file exists, if not create a default one
        config_path = "websites.json"
        if not os.path.exists(config_path):
            # Create default config
            # Each website needs:
            # - url: The URL of the product page
            # - selector: CSS selector to locate the price element
            # - regex: Regular expression to extract the price (optional)
            # - headers: Custom headers for the request (optional)
            default_config = [
                {
                    "name": "Amazon Example",
                    "url": "https://www.amazon.com/example-product",
                    "selector": "span.a-offscreen",
                    "regex": r"\$([0-9]+\.[0-9]{2})",
                },
                {
                    "name": "Walmart Example",
                    "url": "https://www.walmart.com/example-product",
                    "selector": "span.price-characteristic",
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                },
            ]
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config file at {config_path}")

        # Load config from file
        with open(config_path, "r") as f:
            websites = json.load(f)

        return websites
    except Exception as e:
        print(f"Error loading websites configuration: {str(e)}")
        sys.exit(1)


def scrape_price(website):
    """Scrape the price from a website."""
    try:
        headers = website.get(
            "headers",
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )

        response = requests.get(website["url"], headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.select_one(website["selector"])

        if not price_element:
            return None

        price_text = price_element.text.strip()

        # Extract price using regex if provided
        if "regex" in website:
            match = re.search(website["regex"], price_text)
            if match:
                price = float(match.group(1))
            else:
                # Try to extract numeric value from the text
                price = float(re.sub(r"[^\d.]", "", price_text))
        else:
            # Try to extract numeric value from the text
            price = float(re.sub(r"[^\d.]", "", price_text))

        return price
    except Exception as e:
        print(f"Error scraping {website['name']}: {str(e)}")
        return None


def main():
    # Load websites configuration
    websites = load_websites_config()

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")

    # Scrape prices for all websites
    results = {}
    for website in websites:
        price = scrape_price(website)
        if price is not None:
            results[website["name"]] = price

    # Check if we have any valid results
    if not results:
        print("No prices were successfully scraped.")
        sys.exit(1)

    # Save today's results to a new file
    filename = f"data/{today}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved prices for {today} to {filename}")

    # Update the combined data file with all historical data
    update_combined_data()


def update_combined_data():
    """Update the combined data file with all historical data."""
    all_data = {}

    # Read all JSON files in the data directory
    for filename in sorted(os.listdir("data")):
        if filename.endswith(".json") and filename != "combined.json":
            date = filename.replace(".json", "")
            with open(f"data/{filename}", "r") as f:
                data = json.load(f)
                all_data[date] = data

    # Save combined data
    with open("data/combined.json", "w") as f:
        json.dump(all_data, f, indent=2)

    print("Updated combined data file.")


if __name__ == "__main__":
    main()
