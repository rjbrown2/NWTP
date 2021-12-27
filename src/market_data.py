import constants
import requests

from src import UI

req_url = "https://docs.google.com/spreadsheets/d/{}/export?format=csv&id={}".format(constants.MARKET_DATA,
                                                                                     constants.MARKET_DATA)


def fetch_market_data():
    req = requests.get(req_url, allow_redirects=True)
    with open("../config/sheets_export.csv", "wb") as f:
        f.write(req.content)


def lookup_prices(item):
    price_list = []
    with open(constants.MARKET_DATA_LOCAL, "r", -1, "UTF8") as read_file:
        lines = read_file.readlines()
    for line in lines:
        as_list = line.split(",")
        print(as_list)
        if item == as_list[0]:
            price_list.append(float(as_list[1]))
            price_list.append(float(as_list[2]))
            break
    if not price_list:
        print("Price list is empty, did not find " + str(item))
        _t = UI.lookup_dump_data(item)
        if _t == as_list[0]:
            price_list.append(float(as_list[1]))
            price_list.append(float(as_list[2]))
        else:
            raise ValueError("************************************NO VALUE FOUND FOR " + str(item))
    else:
        return price_list
