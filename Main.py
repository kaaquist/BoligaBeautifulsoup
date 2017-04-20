#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import xlsxwriter
from bs4 import BeautifulSoup


'''
This script was developed for a small project done on CBS.
@author Kasper Johansen
@co-author Jakob Stein Bügel
'''

'''This is used to avoid being stopped in Boliga firewall/haproxy etc.'''
headers = {
    'User-agent': 'Mozilla/5.0',
}

xlsxbook = xlsxwriter.Workbook('demo.xlsx')
xlsxsheet = xlsxbook.add_worksheet()

mrd = "jan feb mar apr maj jun jul aug sep okt nov dec"
rowcount = 0

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
    try:
        while page <= max_pages:
            url = 'http://www.boliga.dk/bolig/' + str(page)
            plain_text = connector(url).content
            title = BeautifulSoup(plain_text, "html5lib").find('title').string
            print("Title: " + title)
            get_opslag(plain_text, title)
            page += 1
    except Exception as ex:
        print (ex)
        pass


def make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype):
    xlsxsheet.write(rowcount, columncount, oldval.encode('utf-8').decode('utf-8'))
    columncount += 1
    xlsxsheet.write(rowcount, columncount, prisogtype.encode('utf-8').decode('utf-8'))
    return columncount

def get_opslag(plain_txt, title):
    '''

    :param plain_txt:
    :return:
    '''
    global rowcount
    soup = BeautifulSoup(plain_txt, "html5lib")
    divs = soup.find_all('div',  {'class': "row row-1 rowLine"})
    dowrite = False
    for opslag in divs:
        print('-----------------')
        columncount = 0
        # This is the value that was stored in the last run below.
        oldval = ""
        for i in [x for x in opslag.find_all('h4')]:
            prisogtype = str(i.getText().strip())
            print (prisogtype.split('.')[0])
            if prisogtype.split('.')[0] in mrd:
                dowrite = True
                print ("Dowrite enabled")
            if dowrite:
                if columncount == 0:
                    xlsxsheet.write(rowcount, columncount, title)
                    columncount += 1
                if "Solgt: Alm." in prisogtype:
                    columncount = make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype)
                elif "Solgt: Ukendt" in prisogtype:
                    columncount = make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype)
                elif "Prisændring" in prisogtype:
                    columncount = make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype)
                elif "Prisændring" in oldval:
                    newprisogtype = prisogtype.split("\n")
                    for x in newprisogtype:
                        print (x)
                    xlsxsheet.write(rowcount, columncount + 2, newprisogtype[0].split(' ')[1])
                    xlsxsheet.write(rowcount, columncount + 3, newprisogtype[0].split(' ')[0])
                    xlsxsheet.write(rowcount, columncount + 4, newprisogtype[3].strip().split(' ')[0])
                else:
                    xlsxsheet.write(rowcount, columncount, prisogtype.encode('utf-8').decode('utf-8'))
                print (prisogtype)
                columncount += 1
                oldval = prisogtype
        for j in [y for y in opslag.find_all('h6')]:
            if dowrite:
                liggetid = str(j.getText().strip())
                xlsxsheet.write(rowcount, columncount, liggetid.encode('utf-8').decode('utf-8'))
                columncount += 1

        if dowrite:
            rowcount += 1


if __name__ == '__main__':
    boliga_spider(2)
    xlsxbook.close()
