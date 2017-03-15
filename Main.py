import requests
from bs4 import BeautifulSoup

"""
This script was developed for a small project done on CBS.
@author Kasper Johansen
@co-author Jakob Stein Bügel
"""

'''This is used to avoid being stopped in Boliga firewall/haproxy etc.'''
headers = {
    'User-agent': 'Mozilla/5.0',
}

def connector(url):
    '''
    Connect to url and retrieve markup content.
    :param url:
    :return: markup code.
    '''
    return requests.get(url, headers=headers)


def boliga_spider(max_pages):
    '''
    Main Spider for Boliga. Specially tailored to extract only a few fields.
    :param max_pages: amount of properties to loop trough.
    :return: Output print with data regarding sales figures for the property.
    '''
    page = 1
    while page <= max_pages:
        url = 'http://www.boliga.dk/bolig/' + str(page)
        plain_text = connector(url).content
        print("Title: " + (BeautifulSoup(plain_text, "html5lib").find('title')).string)
        get_opslag(plain_text)
        page += 1


def get_opslag(plain_txt):
    '''

    :param plain_txt:
    :return:
    '''
    soup = BeautifulSoup(plain_txt, "html5lib")
    divs = soup.find_all('div',  {'class': "row row-1 rowLine"})
    for opslag in divs:
        print('-----------------')
        for i in [x for x in opslag.find_all('h4')]:
            print(str(i.getText().strip()))
        for j in [y for y in opslag.find_all('h6')]:
            print(j.getText().strip())


if __name__ == '__main__':
    boliga_spider(1)
