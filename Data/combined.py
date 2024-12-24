import requests
from bs4 import BeautifulSoup
import concurrent.futures
from pathlib import Path
import json
import time
from tqdm import tqdm
import os
from datetime import datetime, timedelta
import pickle

class CricketStatsCollector:
    def __init__(self):
        self.base_url = "https://www.espncricinfo.com"
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()  # Reuse TCP connections
        self.batsmenStats = {}
        self.bowlerStats = {}
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def get_cached_response(self, url, cache_duration_hours=24):
        
        cache_file = self.cache_dir / f"{hash(url)}.pickle"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                if datetime.now() - cached_data['timestamp'] < timedelta(hours=cache_duration_hours):
                    return cached_data['content']
                
        
        response = self.session.get(url).text
        cached_data = {
            'timestamp': datetime.now(),
            'content': response
        }
        with open(cache_file, 'wb') as f:
            pickle.dump(cached_data, f)
        return response

    def get_years(self):
        html = self.get_cached_response(
            'https://www.espncricinfo.com/records/list-of-match-results-by-year-307847'
        )
        soup = BeautifulSoup(html, 'lxml')
        year_list = soup.find('div', class_='ds-p-4')
        return [a['href'] for a in year_list.find_all('a')]

    def get_matches_for_year(self, year_url, teams):
        try:
            full_url = self.base_url + year_url
            html = self.get_cached_response(full_url)
            soup = BeautifulSoup(html, 'lxml')
            
            matches = []
            table = soup.select_one('table', class_='ds-w-full ds-table ds-table-xs ds-table-auto')
            if not table:
                return matches

            for row in table.find_all('tr'):
                team1 = row.find('td', class_='ds-min-w-max')
                team2 = row.find('td', class_='ds-min-w-max ds-text-right')
                if team1 and team2 and team1.text in teams and team2.text in teams:
                    links = row.find_all('a')
                    if len(links) > 1:
                        matches.append(links[1]['href'])
            return matches
        except Exception as e:
            print(f"Error processing year {year_url}: {str(e)}")
            return []

    def process_match(self, match_url):
        try:
            full_url = self.base_url + match_url
            html = self.get_cached_response(full_url)
            soup = BeautifulSoup(html, 'lxml')
            
            match_stats = {'batsmen': {}, 'bowlers': {}}
            
            innings = soup.find_all('div', class_='ds-w-full ds-bg-fill-content-prime ds-overflow-hidden ds-rounded-xl ds-border ds-border-line ds-mb-4', limit=4)
            
            # Process batting stats
            for inning in innings:
                batsmen = inning.find_all('td', class_=['ds-w-0 ds-whitespace-nowrap ds-min-w-max',
                                                      'ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-border-line-primary ci-scorecard-player-notout'])
                scores = inning.find_all('td', class_='ds-w-0 ds-whitespace-nowrap ds-min-w-max ds-text-right ds-text-typo')
                
                for batter, score in zip(batsmen, scores):
                    try:
                        runs = int(score.text)
                        match_stats['batsmen'][batter.text] = runs
                    except (ValueError, AttributeError):
                        continue

            # Process bowling stats
            for inning in innings:
                tables = inning.select('table', class_='ds-w-full ds-table ds-table-md ds-table-auto')
                if len(tables) > 1:
                    bowlers = tables[1].find_all('div', class_='ds-popper-wrapper ds-inline')
                    wickets = tables[1].find_all('td', class_='ds-w-0 ds-whitespace-nowrap ds-text-right')
                    
                    for bowler, wicket in zip(bowlers, wickets):
                        try:
                            wicket_count = int(wicket.text)
                            match_stats['bowlers'][bowler.text] = wicket_count
                        except (ValueError, AttributeError):
                            continue
                            
            return match_stats
        except Exception as e:
            print(f"Error processing match {match_url}: {str(e)}")
            return None

    def collect_stats(self, teams, max_workers=10):
        
        print("Fetching years...")
        years = self.get_years()
        
        
        print("Fetching matches...")
        all_matches = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_year = {executor.submit(self.get_matches_for_year, year, teams): year 
                            for year in years}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_year), 
                             total=len(years), desc="Processing years"):
                matches = future.result()
                all_matches.extend(matches)

        # Process matches using parallel processing
        print(f"\nProcessing {len(all_matches)} matches...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_match = {executor.submit(self.process_match, match): match 
                             for match in all_matches}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_match), 
                             total=len(all_matches), desc="Processing matches"):
                match_stats = future.result()
                if match_stats:
                    # Aggregate batting stats
                    for player, runs in match_stats['batsmen'].items():
                        self.batsmenStats[player] = self.batsmenStats.get(player, 0) + runs
                    
                    # Aggregate bowling stats
                    for player, wickets in match_stats['bowlers'].items():
                        self.bowlerStats[player] = self.bowlerStats.get(player, 0) + wickets

        # Save the aggregated stats to files
        self.save_stats_to_file()

    def save_stats_to_file(self):
        batsmen_file = self.output_dir / "batsmen_stats.json"
        bowler_file = self.output_dir / "bowler_stats.json"

        with open(batsmen_file, 'w') as bf:
            json.dump(self.batsmenStats, bf, indent=4)

        with open(bowler_file, 'w') as wf:
            json.dump(self.bowlerStats, wf, indent=4)

        print(f"Batsmen stats saved to {batsmen_file}")
        print(f"Bowler stats saved to {bowler_file}")

    def print_stats(self):
        print("\nBatsmen Stats (Top 10):")
        sorted_batsmen = sorted(self.batsmenStats.items(), key=lambda x: x[1], reverse=True)
        for player, runs in sorted_batsmen[:10]:
            print(f"{player}: {runs} runs")

        print("\nBowler Stats (Top 10):")
        sorted_bowlers = sorted(self.bowlerStats.items(), key=lambda x: x[1], reverse=True)
        for player, wickets in sorted_bowlers[:10]:
            print(f"{player}: {wickets} wickets")

def main():
    start_time = time.time()

    teams = input("Enter the team names (comma-separated, e.g., India, Australia): ").split(',')
    teams = [team.strip() for team in teams]
    
    collector = CricketStatsCollector()
    collector.collect_stats(teams)
    collector.print_stats()
    
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
