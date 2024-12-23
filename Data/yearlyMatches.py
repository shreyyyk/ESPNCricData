from bs4 import BeautifulSoup
import requests
from years import get_years

base_url = "https://www.espncricinfo.com"

def get_matches(team1, team2):
    all_matches = []
    year_urls = get_years()

    for year_url in year_urls:
        full_url = base_url + year_url
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'lxml')

            table = soup.select_one('table', class_='ds-w-full ds-table ds-table-xs ds-table-auto  ds-w-full ds-overflow-scroll ds-scrollbar-hide')

            if not table:
                continue

            rows = table.find_all('tr')

            need = [team1, team2]

            for row in rows:
                try:
                    team1_name = row.find('td', class_='ds-min-w-max').text
                    team2_name = row.find('td', class_='ds-min-w-max ds-text-right').text
                    if team1_name in need and team2_name in need:
                        links = row.find_all('a')
                        all_matches.append(links[1]['href'])
                except AttributeError:
                    # Skip rows with missing data
                    continue
        except requests.RequestException as e:
            print(f"Skipping URL {full_url} due to error: {e}")

    return all_matches

if __name__ == "__main__":
    team1 = input("Enter First Team: ").strip()
    team2 = input("Enter Second Team: ").strip()
    matches = get_matches(team1, team2)
    for match in matches:
        print(base_url + match)
