from bs4 import BeautifulSoup
import requests
from yearlyMatches import get_matches

base_url = "https://www.espncricinfo.com"

team1 = input("Enter First Team: ").strip()
team2 = input("Enter Second Team: ").strip()

urls = get_matches(team1,team2)

batsmenStats = {}
bowlerStats = {}

def process_match(url):
    global batsmenStats, bowlerStats
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

        for inn in innings:
            check = inn.select('table')
            if len(check) > 1:
                bowlTable.append(check[1])

        for inning in innings:
            batsmenHtml.append(inning.find_all(
                'td',
                class_=[
                    'ds-w-0 ds-whitespace-nowrap ds-min-w-max',
                    'ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-border-line-primary ci-scorecard-player-notout'
                ]
            ))

        batsmen = []
        bowler = []
        idiot = []  # List for bowler HTML elements

        for tables in bowlTable:
            check = tables.find_all('div', class_='ds-popper-wrapper ds-inline')
            idiot.extend(check)

        for names in idiot:
            bowler.append(names.text)

        for inns in batsmenHtml:
            for bats in inns:
                batsmen.append(bats.text.strip())

        scoresHtml = []
        wicketsHtml = []

        for inning in innings:
            scores = inning.find_all(
                'td',
                class_='ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-text-right ds-text-typo'
            )
            scoresHtml.extend(scores)

            wickets = inning.find_all(
                'td',
                class_='ds-w-0 ds-whitespace-nowrap ds-text-right'
            )
            wicketsHtml.extend(wickets)

        # Extract scores and wickets
        scores = [int(s.text.strip()) for s in scoresHtml if s.text.strip().isdigit()]
        wickets = [int(w.text.strip()) for w in wicketsHtml if w.text.strip().isdigit()]

        # Update batsmen stats
        for i, player in enumerate(batsmen):
            if i < len(scores):
                batsmenStats[player] = batsmenStats.get(player, 0) + scores[i]

        # Update bowler stats
        for j, player in enumerate(bowler):
            if j < len(wickets):
                bowlerStats[player] = bowlerStats.get(player, 0) + wickets[j]

    except Exception as e:
        print(f"Error processing match {url}: {e}")

def main():
    for url in urls:
        full_url = base_url + url
        print(f"Processing match: {full_url}")
        process_match(full_url)

    print("Batsmen Stats:", batsmenStats)
    print("Bowler Stats:", bowlerStats)

if __name__ == "__main__":
    main()
