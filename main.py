import os
import time
import pandas as pd

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager


# Configure headless browser
chrome_options = Options()
chrome_options.add_argument("--headless=new")

driver = None

try:
    # Automatically manage ChromeDriver
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    driver.get("https://coinmarketcap.com/")

    print("Collecting cryptocurrency data...")

    # Wait for dynamic webpage loading
    time.sleep(2)

    rows = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "table tbody tr")
        )
    )

    crypto_data = []

    # Collect top 10 cryptocurrencies
    for row in rows:

        cells = row.find_elements(By.TAG_NAME, "td")

        if len(cells) >= 8:

            rank = cells[1].text.strip()

            if rank.isdigit():

                coin_name = cells[2].text.split("\n")[0]
                price = cells[3].text
                change_24h = cells[5].text
                market_cap = cells[7].text

                crypto_data.append([
                    coin_name,
                    price,
                    change_24h,
                    market_cap
                ])

        if len(crypto_data) == 10:
            break

    if len(crypto_data) != 10:
        raise Exception(
            "Could not collect 10 cryptocurrencies."
        )

    # Create Pandas DataFrame
    columns = [
        "Coin Name",
        "Current Price",
        "24h Change",
        "Market Capitalization"
    ]

    df = pd.DataFrame(
        crypto_data,
        columns=columns
    )

    # Save current cryptocurrency data
    df.to_csv(
        "crypto_data.csv",
        index=False,
        encoding="utf-8"
    )

    # Historical data logging
    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    history_df = df.copy()

    history_df.insert(
        0,
        "Date and Time",
        current_time
    )

    history_file = "crypto_history.csv"

    history_df.to_csv(
        history_file,
        mode="a",
        header=(
            not os.path.exists(history_file)
            or os.path.getsize(history_file) == 0
        ),
        index=False,
        encoding="utf-8"
    )

    print("\nCurrent data saved successfully!")
    print("Historical data saved successfully!")

    # Filtering options
    print("\nFILTERING OPTIONS")
    print("1. Price above $100")
    print("2. Positive 24h change")
    print("3. Both filters")

    choice = input(
        "Enter your choice (1, 2 or 3): "
    )

    filtered_data = []

    for coin in crypto_data:

        try:
            price_value = float(
                coin[1].replace("$", "").replace(",", "")
            )

            change_value = float(
                coin[2].replace("%", "").replace(",", "")
            )

            if choice == "1" and price_value > 100:
                filtered_data.append(coin)

            elif choice == "2" and change_value > 0:
                filtered_data.append(coin)

            elif (
                choice == "3"
                and price_value > 100
                and change_value > 0
            ):
                filtered_data.append(coin)

        except ValueError:
            continue

    # Display filtered results
    if choice not in ["1", "2", "3"]:

        print(
            "Invalid choice. Please select 1, 2 or 3."
        )

    else:

        print("\nFILTERED CRYPTOCURRENCY DETAILS")

        if filtered_data:

            for coin in filtered_data:
                print(coin)

            print(
                "\nTotal filtered coins:",
                len(filtered_data)
            )

        else:
            print(
                "No cryptocurrencies match the selected filter."
            )

    # TREND ANALYSIS
    print("\n" + "=" * 45)
    print("CRYPTOCURRENCY TREND ANALYSIS")
    print("=" * 45)

    if os.path.exists(history_file):

        historical_df = pd.read_csv(history_file)

        if not historical_df.empty:

            # Convert timestamps into datetime format
            historical_df["Date and Time"] = pd.to_datetime(
                historical_df["Date and Time"],
                errors="coerce"
            )

            # Convert prices into numeric values
            historical_df["Price Value"] = (
                historical_df["Current Price"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )

            historical_df["Price Value"] = pd.to_numeric(
                historical_df["Price Value"],
                errors="coerce"
            )

            # Remove invalid records
            historical_df = historical_df.dropna(
                subset=[
                    "Date and Time",
                    "Price Value"
                ]
            )

            if not historical_df.empty:

                # Sort records by timestamp
                historical_df = historical_df.sort_values(
                    by="Date and Time"
                )

                # Analyze each cryptocurrency
                for coin_name in historical_df["Coin Name"].unique():

                    coin_history = historical_df[
                        historical_df["Coin Name"] == coin_name
                    ].sort_values(
                        by="Date and Time"
                    )

                    if len(coin_history) < 2:
                        print("\nCoin:", coin_name)
                        print(
                            "Not enough historical records for comparison."
                        )
                        continue

                    first_price = coin_history[
                        "Price Value"
                    ].iloc[0]

                    latest_price = coin_history[
                        "Price Value"
                    ].iloc[-1]

                    difference = latest_price - first_price

                    print("\nCoin:", coin_name)

                    print(
                        "Previous Price: $",
                        round(first_price, 4)
                    )

                    print(
                        "Latest Price: $",
                        round(latest_price, 4)
                    )

                    print(
                        "Price Difference: $",
                        round(difference, 4)
                    )

                    if difference > 0:
                        print("Trend: Increased")

                    elif difference < 0:
                        print("Trend: Decreased")

                    else:
                        print("Trend: No Change")

            else:
                print("No valid historical price records.")

        else:
            print("No historical records available.")

    else:
        print("Historical file not found.")

    print("\nTrend analysis completed successfully!")

except Exception as error:

    print("\nError:", error)

finally:

    if driver is not None:
        driver.quit()

    print("\nHeadless browser closed successfully!")