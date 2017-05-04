#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import xlsxwriter
import datetime
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

mrd = "jan feb mar apr maj jun jul aug sep okt nov dec"
rowcount = 0


def get_xlsx_file():
    global rowcount
    rowcount = 0
    xlsxbook = xlsxwriter.Workbook('xlsxbook-{}.xlsx'.format(str(datetime.datetime.now()).replace(':', '.')))
    xlsxsheet = xlsxbook.add_worksheet()
    return xlsxsheet, xlsxbook


def close_xlsx_file(book_to_close):
    book_to_close.close()


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
    xlsxsheet, xlsxbook = get_xlsx_file()
    try:
        while page <= max_pages:
            # Here we reload a new xlsxbook and xlsxsheet when we have reached x rows in the xlsx. Max is 65000
            if rowcount > 40:
                close_xlsx_file(xlsxbook)
                xlsxsheet, xlsxbook = get_xlsx_file()
            url = 'http://www.boliga.dk/bolig/' + str(page)
            plain_text = connector(url).content
            title = BeautifulSoup(plain_text, "html5lib").find('title').string
            print("Title: " + title)
            get_opslag(plain_text, title, xlsxsheet)
            page += 1
    except Exception as ex:
        print (ex)
        pass

    close_xlsx_file(xlsxbook)


def make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype, xlsxsheet):
    xlsxsheet.write(rowcount, columncount, oldval.encode('utf-8').decode('utf-8'))
    columncount += 1
    xlsxsheet.write(rowcount, columncount, prisogtype.encode('utf-8').decode('utf-8'))
    return columncount

def get_opslag(plain_txt, title, xlsxsheet):
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
                    columncount = make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype, xlsxsheet)
                elif "Solgt: Ukendt" in prisogtype:
                    columncount = make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype, xlsxsheet)
                elif "Prisændring" in prisogtype:
                    columncount = make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype, xlsxsheet)
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
    boliga_spider(12)
