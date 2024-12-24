from bs4 import BeautifulSoup
import requests


def get_years():
    html=requests.get('https://www.espncricinfo.com/records/list-of-match-results-by-year-307847').text
    soup=BeautifulSoup(html,'lxml')

    year_list=soup.find('div',class_='ds-p-4')

    year_links=year_list.find_all('a')

    links=[]

    for item in year_links:
        links.append(item['href'])

    return links

if __name__ == "__main__":
    print(get_years())