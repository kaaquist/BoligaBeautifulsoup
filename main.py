#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import xlsxwriter
import datetime
from bs4 import BeautifulSoup

MONTHS_DA = "jan feb mar apr maj jun jul aug sep okt nov dec"

HEADERS = {
    "User-agent": "Mozilla/5.0",
}


def get_xlsx_file(filename: str | None = None):
    if filename is None:
        filename = "xlsxbook-{}.xlsx".format(
            str(datetime.datetime.now()).replace(":", ".")
        )
    book = xlsxwriter.Workbook(filename)
    sheet = book.add_worksheet()
    return sheet, book


def close_xlsx_file(book):
    book.close()


def connector(url: str, headers: dict = HEADERS):
    return requests.get(url, headers=headers)


def make_row_and_add_oldval(rowcount, columncount, oldval, prisogtype, xlsxsheet):
    xlsxsheet.write(rowcount, columncount, oldval.encode("utf-8").decode("utf-8"))
    columncount += 1
    xlsxsheet.write(rowcount, columncount, prisogtype.encode("utf-8").decode("utf-8"))
    return columncount


def get_opslag(plain_txt, title, xlsxsheet, rowcount: int = 0) -> int:
    soup = BeautifulSoup(plain_txt, "html5lib")
    divs = soup.find_all("div", {"class": "row row-1 rowLine"})
    dowrite = False
    for opslag in divs:
        columncount = 0
        oldval = ""
        for i in opslag.find_all("h4"):
            prisogtype = str(i.getText().strip())
            if prisogtype.split(".")[0] in MONTHS_DA:
                dowrite = True
            if dowrite:
                if columncount == 0:
                    xlsxsheet.write(rowcount, columncount, title)
                    columncount += 1
                if "Solgt: Alm." in prisogtype:
                    columncount = make_row_and_add_oldval(
                        rowcount, columncount, oldval, prisogtype, xlsxsheet
                    )
                elif "Solgt: Ukendt" in prisogtype:
                    columncount = make_row_and_add_oldval(
                        rowcount, columncount, oldval, prisogtype, xlsxsheet
                    )
                elif "Prisændring" in prisogtype:
                    columncount = make_row_and_add_oldval(
                        rowcount, columncount, oldval, prisogtype, xlsxsheet
                    )
                elif "Prisændring" in oldval:
                    newprisogtype = prisogtype.split("\n")
                    xlsxsheet.write(rowcount, columncount + 2, newprisogtype[0].split(" ")[1])
                    xlsxsheet.write(rowcount, columncount + 3, newprisogtype[0].split(" ")[0])
                    xlsxsheet.write(rowcount, columncount + 4, newprisogtype[3].strip().split(" ")[0])
                else:
                    xlsxsheet.write(rowcount, columncount, prisogtype.encode("utf-8").decode("utf-8"))
                columncount += 1
                oldval = prisogtype

        for j in opslag.find_all("h6"):
            if dowrite:
                liggetid = str(j.getText().strip())
                xlsxsheet.write(rowcount, columncount, liggetid.encode("utf-8").decode("utf-8"))
                columncount += 1

        if dowrite:
            rowcount += 1

    return rowcount


def boliga_spider(max_pages: int, row_limit: int = 40):
    rowcount = 0
    xlsxsheet, xlsxbook = get_xlsx_file()
    try:
        for page in range(1, max_pages + 1):
            if rowcount > row_limit:
                close_xlsx_file(xlsxbook)
                xlsxsheet, xlsxbook = get_xlsx_file()
                rowcount = 0
            url = "http://www.boliga.dk/bolig/" + str(page)
            plain_text = connector(url).content
            title = BeautifulSoup(plain_text, "html5lib").find("title").string
            print("Title: " + title)
            rowcount = get_opslag(plain_text, title, xlsxsheet, rowcount)
    except Exception as ex:
        print(ex)

    close_xlsx_file(xlsxbook)


def main():
    boliga_spider(12)


if __name__ == "__main__":
    main()
