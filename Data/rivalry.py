from bs4 import BeautifulSoup
import requests
from yearlyMatches import get_matches
import pandas as pd
import streamlit as st


base_url = "https://www.espncricinfo.com"

team1 = input("Enter First Team: ").strip()
team2 = input("Enter Second Team: ").strip()

urls = get_matches(team1, team2)

playerStats = {}
def normalize_overs(overs):
    """
    Normalize overs bowled in cricket where every 0.6 equals the next whole number.
    """
    whole, fractional = divmod(overs, 1)
    fractional = round(fractional * 10)  # Get the fractional part as an integer
    if fractional > 5:  # If fractional part is >=6, increment the whole number
        whole += 1
        fractional = 0
    return whole + fractional / 10



def process_match(url):
    global playerStats
    try:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'lxml')

        innings = soup.find_all(
            'div',
            class_='ds-w-full ds-bg-fill-content-prime ds-overflow-hidden ds-rounded-xl ds-border ds-border-line ds-mb-4',
            limit=4
        )

        if not innings:
            print(f"No innings data found for {url}")
            return

        batsmenHtml = []
        bowlTable = []
        batTable = []

        for inn in innings:
            check = inn.select('table')
            if len(check) > 1:
                batTable.append(check[0])
                bowlTable.append(check[1])

        batterHtml = []
        bowlerHtml = []

        for tables in bowlTable:
            rows = tables.find_all('tr')[::2]
            bowlerHtml.extend(rows)

        for tables in batTable:
            rows = tables.find_all('tr')
            for row in rows:
                name_element = row.find('a')
                if not name_element or 'title' not in name_element.attrs:
                    continue  # Skip invalid rows
                name = name_element['title']
                if not name.isalpha() and ' ' not in name:
                    continue
                if name == 'Extras' :
                    break
            batterHtml.extend(rows)

        for row in batterHtml:
            try:
                name_element = row.find('a')
                if not name_element or 'title' not in name_element.attrs:
                    continue  # Skip invalid rows
                name = name_element['title']
                if not name.isalpha() and ' ' not in name:
                    continue
                
                runs = row.find('td', class_='ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-text-right ds-text-typo')
                runs = int(runs.text) if runs and runs.text.isdigit() else 0

                ballsFaced = row.find('td', class_='ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-text-right')
                ballsFaced = int(ballsFaced.text) if ballsFaced and ballsFaced.text.isdigit() else 0

                if name not in playerStats:
                    playerStats[name] = [runs, ballsFaced, 0, 0]
                else:
                    playerStats[name][0] += runs
                    playerStats[name][1] += ballsFaced
            except Exception as e:
                print(f"Error processing batter row: {e}")


        for row in bowlerHtml:
            try:
                name_element = row.find('a')
                if not name_element or not name_element.text.strip():
                    continue  # Skip invalid rows
                name = name_element.text.strip()

                # Extract wickets
                wickets_element = row.find('td', class_='ds-w-0 ds-whitespace-nowrap ds-text-right')
                wickets = int(wickets_element.text.strip()) if wickets_element and wickets_element.text.isdigit() else 0

                # Extract overs bowled
                overs_element = row.find('td', class_='ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-text-right')
                oversBowled = float(overs_element.text.strip()) if overs_element and overs_element.text.replace('.', '', 1).isdigit() else 0
                oversBowled = normalize_overs(oversBowled)  # Normalize overs using cricket rules

                # Update player stats
                if name not in playerStats:
                    playerStats[name] = [0, 0, wickets, oversBowled]
                else:
                    playerStats[name][2] += wickets  # Update wickets
                    total_overs = playerStats[name][3] + oversBowled
                    playerStats[name][3] = normalize_overs(total_overs)  # Normalize total overs
            except Exception as e:
                print(f"Error processing bowler row: {e}")





    except Exception as e:
        print(f"Error processing match {url}: {e}")

def save_to_files():
    # Convert dictionaries to DataFrame
    player_df = pd.DataFrame.from_dict(playerStats, orient='index', columns=['Runs', 'BallsFaced', 'Wickets', 'OversBowled'])
    player_df.index.name = 'PlayerName'  # Include player names as a column

    # Reset the index to make 'PlayerName' a regular column
    player_df.reset_index(inplace=True)

    # Save to JSON
    player_df.to_json('playerStats.json', orient='records', indent=4)
    print("Data has been saved to playerStats.json")

    # Save to Excel
    player_df.to_excel('playerStats.xlsx', sheet_name='PlayerStats', index=False)
    print("Data has been saved to playerStats.xlsx")


def main():
    for url in urls:
        full_url = base_url + url
        print(f"Processing match: {full_url}")
        process_match(full_url)

    print("Player Stats:", playerStats)

    # Save to Excel
    save_to_files()

if __name__ == "__main__":
    main()
