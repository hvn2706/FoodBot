"""
Load all the data from json files into database
Set environment variables for database port (DBPort) and password (DBP) to run the code
"""

import mysql.connector
import os
import json
import re
from datetime import datetime

mydb = mysql.connector.connect(
    host="localhost",
    port=os.environ["DBPort"],
    user="root",
    password=os.environ["DBP"],
    database="FindFood"
)

cursor = mydb.cursor(buffered=True)

path_bun = "../save/link_store_bún_"
path_com = "../save/link_store_cơm_"
path_pho = "../save/link_store_phở_"


def add_diner(name, address, city, district, price_min, price_max, website, review_point):
    """
    Add diner information, id auto_increment
    :param name: str diner name
    :param address: str diner address
    :param city: str diner location
    :param district: str
    :param price_min: float minimum price range
    :param price_max: float maximum price range
    :param website: str foody site
    :param review_point: list of review point for each aspects in format %.2f
    :return: None
    """
    global mydb
    global cursor
    values = [name, address, city, district, price_min, price_max, website] + prep_review(review_point)

    sqlLine = 'INSERT INTO diners(name, address, city, district, priceMin, priceMax, website, ' \
              'qualityPoint, pricePoint, servicePoint, destinationPoint, spacePoint)' \
              'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    # print(values)
    cursor.execute(sqlLine, values)
    mydb.commit()


def add_menu(name, price, diner_id, details=None):
    """
    add dished to menu table
    :param name: str dish name
    :param price: dish price
    :param diner_id: int specify which diner
    :param details: dish description
    :return: None
    """
    global mydb
    global cursor

    sqlLine = 'INSERT INTO menu(name, price, details, dinerID) VALUES (%s, %s, %s, %s)'

    if details is None:
        details = 'null'
    price = prep_price(price)
    cursor.execute(sqlLine, (name, price, details, diner_id))
    mydb.commit()


def get_diner_id():
    """
    :return: the next diner id
    """
    global mydb
    global cursor

    sqlLine = 'SELECT MAX(id) FROM diners'

    cursor.execute(sqlLine)
    rt = cursor.next()[0]
    if rt is None:
        return 1
    return rt


def prep_time(timetable: list, diner_id):
    """
    Time table preprocessing and add to database
    :param timetable: list of shifts of diners
    :param diner_id: int specify which diner
    :return: None
    """

    for shift in timetable:
        marks = shift.split('-')
        start = datetime.strptime(marks[0], '%H:%M').time()
        close = datetime.strptime(marks[1], '%H:%M').time()
        sqlLine = 'INSERT INTO timetable(dinerID, time_start, time_close) VALUES(%s, %s, %s)'
        cursor.execute(sqlLine, (diner_id, start, close))
        mydb.commit()


def prep_review(review_point: list):
    """
    preprocessing review_point
    :param review_point: list of points of each aspects
    :return: list of review_point in order: Chất lượng, Giá cả, Phục vụ, Vị trí, Không gian
    """
    reviews = [None] * 5

    for x in review_point:
        if list(x.keys())[0] == 'Chất lượng':
            reviews[0] = x['Chất lượng']
        if list(x.keys())[0] == 'Giá cả':
            reviews[1] = x['Giá cả']
        if list(x.keys())[0] == 'Phục vụ':
            reviews[2] = x['Phục vụ']
        if list(x.keys())[0] == 'Vị trí':
            reviews[3] = x['Vị trí']
        if list(x.keys())[0] == 'Không gian':
            reviews[4] = x['Không gian']
    return reviews


def remove_emoji(string):
    """remove emoji from string"""
    if string is None:
        return None
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)


def prep_price(price):
    """
    set all price to format %.2f
    :param price: priceMin priceMax from diners, price from menu
    :return: price with format %.2f
    """
    price = str(price)
    price = price.replace('đ', '')
    price = price.replace('.', '')
    price = price.replace(',', '')
    return price


def load_in_range(food_path, left, right):
    """
    get all the data from .json files to the database
    :param food_path: path of food type
    :param left: from epoch left
    :param right: to epoch right
    :return: None
    """
    for i in range(left, right + 1):
        path_tmp = food_path + str(i)
        file_list = os.listdir(path_tmp)
        for f in file_list:
            path = path_tmp + '/' + f
            file = open(path, 'r', encoding='utf8')
            try:
                data = json.load(file)
                try:
                    add_diner(data['name'],
                              data['address'],
                              data['city'],
                              data['district'],
                              prep_price(data['priceMin']),
                              prep_price(data['priceMax']),
                              data['website'],
                              data['review_point'])
                    diner_id = get_diner_id()
                    prep_time(data['Time'], diner_id)
                    menus = data['menu']['data']
                    for food in menus:
                        # details = remove_emoji(food['details'])
                        add_menu(food['name'], food['price'], diner_id, details=food['details'])
                except IndexError:
                    print('no menu')
            except Exception as e:
                print(e)
                print(path)
                # return  # comment this if you are too lazy to delete all the corrupted files
            file.close()


load_in_range(path_pho, 1, 30)
load_in_range(path_com, 1, 30)
load_in_range(path_bun, 1, 30)
mydb.close()
