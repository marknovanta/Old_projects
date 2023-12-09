'''
  ______  _____
 |  ____|/ ____|
 | |__  | (___
 |  __|  \___ \
 | |____ ____) |
 |______|_____/
---------------------
  --->>> ES <<<---
---------------------
'''

from tkinter import *
from bs4 import BeautifulSoup
import requests
import json
from dateutil import parser
import csv
import re

import math

from getpass import getpass
import calendar
import datetime
import time
import sqlite3
import winsound
import logging

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum

from ibapi.order import *

import threading

from string import Template

from time import strftime
from time import gmtime

import yfinance as yf
import numpy as np
import pandas as pd

version = '1.4'
print('MVT ES - v' + version)
print('Created by Marco Trazza')

# PASSWORD MANAGER----------------------------------------------------------------------------------
# psw = "StarLord"
# prompt = getpass("Enter password: ")
#
# while prompt != psw:
#     #VOICE <<<<<<-------------------------
#     winsound.PlaySound("sounds/voice/Allison/password_wrong.wav", winsound.SND_ASYNC)
#     print("Password not correct")
#     prompt = getpass("Enter password: ")
#
# print("Use allowed")
# #VOICE <<<<<<<<<<<------------------------
# winsound.PlaySound("sounds/voice/Allison/password_correct.wav", winsound.SND_ASYNC)
# print("Loading...")
# time.sleep(5)
# --------------------------------------------------------------------------------------------------
exp_volume = 0
most_liquid = None

# socket = 7496 # SOCKET PORT <<<---------- 7496 (paper); 7497 (real)

while True:
    print("""

    What type of account are we going to work on?
    r = REAL
    p = PAPER

    """)

    choice_S = input('continue?')
    if choice_S =='r' or choice_S =='R':
        socket = 7497
        print('/// WARNING, WE WILL WORK ON A REAL ACCOUNT ///')
        print('/// WARNING, WE WILL WORK ON A REAL ACCOUNT ///')
        print('/// WARNING, WE WILL WORK ON A REAL ACCOUNT ///')
        break
    elif choice_S =='p' or choice_S =='P':
        socket = 7496
        print('We will work on a PAPER account')
        break
    else:
        continue

starting_up = True

volume_leak_avg = 0

# formatting time_delta
class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    d["H"], rem = divmod(tdelta.seconds, 3600)
    d["M"], d["S"] = divmod(rem, 60)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


print('\n')
print('EXPIRATION INFO ---')

class Expirations(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def historicalData(self, reqId, bar):
        global exp_volume
        print("HistoricalData. ", reqId, " Date:", bar.date, "Volume:", bar.volume)
        exp_volume = bar.volume

    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        #print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        self.disconnect()

today = datetime.date.today()
today_day = today.strftime("%A")
td_delta = 1
td = datetime.timedelta(days=td_delta)
yesterday = today - td
yesterday_day = yesterday.strftime("%A")
while yesterday_day == "Sunday" or yesterday_day == "Saturday":
    td_delta += 1
    td = datetime.timedelta(days=td_delta)
    yesterday = today - td
    yesterday_day = yesterday.strftime("%A")

print("Today:", today_day)
print("Last trading day:", yesterday_day, yesterday)
#print(yesterday)

#getting the expiration days for the year
def third_friday(year, month):
    """Return datetime.date for monthly option expiration given year and
    month
    """
    # The 15th is the lowest third day in the month
    third = datetime.date(year, month, 15)
    # What day of the week is the 15th?
    w = third.weekday()
    # Friday is weekday 4
    if w != 4:
        # Replace just the day (of month)
        third = third.replace(day=(15 + (4 - w) % 7))
    return third

months = [3, 6, 9, 12]
exps = list()
today = datetime.date.today()
for m in months:
    friday = third_friday(today.year, m)
    exps.append(friday)

print(exps)

#get volumes from all the expirations that day
'''
- Marzo = H (Dicembre - Marzo)
- Giugno = M (Marzo - Giugno)
- Settembre = U (Giugno - Settembre)
- Dicembre = Z (Settembre - Dicembre)

'''

#warning! exclude expired security!
exps_symbol = ['H', 'M', 'U', 'Z']
exps_to_check = list()

tdy = datetime.timedelta(weeks=52)

if exps[0] <= today < exps[1]:
    year = str(today.year)
    year_var = year[-1]
    #building the ticker
    current_exp = "ES" + exps_symbol[1] + year_var
    next_exp = "ES" + exps_symbol[2] + year_var
    exps_to_check.append(current_exp)
    exps_to_check.append(next_exp)
    print("Current exp:", current_exp)
    print("Next exp:", next_exp)

elif exps[1] <= today < exps[2]:
    year = str(today.year)
    year_var = year[-1]
    #building the ticker
    current_exp = "ES" + exps_symbol[2] + year_var
    next_exp = "ES" + exps_symbol[3] + year_var
    exps_to_check.append(current_exp)
    exps_to_check.append(next_exp)
    print("Current exp:", current_exp)
    print("Next exp:", next_exp)

elif exps[2] <= today < exps[3]:
    year = str(today.year)
    year_var = year[-1]
    ny = today + tdy
    year1 = str(ny.year)
    year_var1 = year1[-1]
    #building the ticker
    current_exp = "ES" + exps_symbol[3] + year_var
    next_exp = "ES" + exps_symbol[0] + year_var1
    exps_to_check.append(current_exp)
    exps_to_check.append(next_exp)
    print("Current exp:", current_exp)
    print("Next exp:", next_exp)

elif exps[3] <= today:
    ny = today + tdy
    year1 = str(ny.year)
    year_var1 = year1[-1]
    #building the ticker
    current_exp = "ES" + exps_symbol[0] + year_var1
    next_exp = "ES" + exps_symbol[1] + year_var1
    exps_to_check.append(current_exp)
    exps_to_check.append(next_exp)
    print("Current exp:", current_exp)
    print("Next exp:", next_exp)

elif today < exps[0]:
    year = str(today.year)
    year_var = year[-1]
    #building the ticker
    current_exp = "ES" + exps_symbol[0] + year_var
    next_exp = "ES" + exps_symbol[1] + year_var
    exps_to_check.append(current_exp)
    exps_to_check.append(next_exp)
    print("Current exp:", current_exp)
    print("Next exp:", next_exp)

volumes = list()
print("Checking the most liquid expiration...")
contratto = None
while contratto is None:
    volumes = list()
    for e in exps_to_check:

        app = Expirations()
        print(e)
        app.connect("127.0.0.1", socket, 0)

        time.sleep(3)

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = e



        app.reqHistoricalData(2, contract, today.strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 0, 1, False, [])

        app.run()
        volumes.append(exp_volume)

    print(volumes)

    if volumes[0] > volumes[1]:
        print("Most liquid exp:", current_exp)
        most_liquid = current_exp
    elif volumes[0] < volumes[1]:
        print("Most liquid exp:", next_exp)
        most_liquid = next_exp

    contratto = most_liquid

# input(" --- Press ENTER to continue --- ")

#ORA LEGALE/ ORA SOLARE MANAGER --------------------------------------------------------------------
quindici = 15
ventuno = 21
sedici = 16
diciannove = 19

sei = 6 #time zone difference (for news)

print('\n')
print('SESSIONS TIME INFO ---')

def time_shift_period_check():
    global quindici
    global ventuno
    global sedici
    global diciannove

    global sei

    c = calendar.Calendar(firstweekday=calendar.SUNDAY)

    year = datetime.date.today().year
    #daylight US1
    month = 3
    monthcal = c.monthdatescalendar(year,month)
    second_sunday_mar = [day for week in monthcal for day in week if \
                    day.weekday() == calendar.SUNDAY and \
                    day.month == month][1]

    US1Y = second_sunday_mar.year
    US1M = second_sunday_mar.month
    US1D = second_sunday_mar.day

    #daylight US2
    month = 11
    monthcal = c.monthdatescalendar(year,month)
    first_sunday_nov = [day for week in monthcal for day in week if \
                    day.weekday() == calendar.SUNDAY and \
                    day.month == month][0]

    US2Y = first_sunday_nov.year
    US2M = first_sunday_nov.month
    US2D = first_sunday_nov.day

    #daylight EU1
    month = 3
    monthcal = c.monthdatescalendar(year,month)
    last_sunday_mar = [day for week in monthcal for day in week if \
                    day.weekday() == calendar.SUNDAY and \
                    day.month == month][-1]

    EU1Y = last_sunday_mar.year
    EU1M = last_sunday_mar.month
    EU1D = last_sunday_mar.day

    #daylight EU2
    month = 10
    monthcal = c.monthdatescalendar(year,month)
    last_sunday_oct = [day for week in monthcal for day in week if \
                    day.weekday() == calendar.SUNDAY and \
                    day.month == month][-1]

    EU2Y = last_sunday_oct.year
    EU2M = last_sunday_oct.month
    EU2D = last_sunday_oct.day

    time_check = datetime.date.today()

    ### to update once per year! ---------------------------- <<<
    us_switch1 = datetime.date(US1Y, US1M, US1D)       #US1
    it_switch1 = datetime.date(EU1Y, EU1M, EU1D) #max  #EU1

    us_switch2 = datetime.date(US2Y, US2M, US2D) #max  #US2
    it_switch2 = datetime.date(EU2Y, EU2M, EU2D)       #EU2
    ### ----------------------------------------------------- <<<

    if us_switch1 <= time_check <= it_switch1 or it_switch2 <= time_check <= us_switch2 :
        quindici = 15 - 1
        ventuno = 21 - 1 ###########################################################################################################################################
        sedici = 16 - 1
        diciannove = 19 - 1
        sei = 6 - 1
        print("Trading sessions are SHIFTED 1h back")
        input(" --- Press ENTER to continue --- ")

    else:
        quindici = 15
        ventuno = 21
        sedici = 16
        diciannove = 19
        sei = 6
        print("Trading sessions are at REGULAR time")
        # input(" --- Press ENTER to continue --- ")
# --------------------------------------------------------------------------------------------------
time_shift_period_check()
# input(" --- Press ENTER to continue --- ")

start_day = datetime.time(quindici, 15, 0)
end_day = datetime.time(ventuno, 45, 1)


f_pom = False
f_ser = False

f_pom_start = datetime.time(0, 0, 1)
f_pom_end = datetime.time(sedici, 32, 0)
f_ser_start = datetime.time(sedici, 33, 0)
f_ser_end = datetime.time(23, 59, 59)


wakeup = datetime.datetime.today()
print(wakeup)
if wakeup.time() < f_pom_end:
    f_pom = True
    f_ser = False
elif f_pom_end < wakeup.time():
    f_pom = False
    f_ser = True


#Check News Module (BEFORE M1_calc) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

news_range = False
evening_comp = False #
rest = False #

news = list() #to be reset every day
news_in_session = list() #to be reset every day

time_delta_post_news = datetime.timedelta(minutes=3, seconds=40)
time_delta_pre_news = datetime.timedelta(minutes=1, seconds=21)

# def setLogger():
#     logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s',
#                     filename='logs_file',
#                     filemode='w')
#     console = logging.StreamHandler()
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console.setFormatter(formatter)
#     logging.getLogger('').addHandler(console)

print('\n')
print('NEWS INFO ---')

def getEconomicCalendar(startlink):
    global sei
    global news

    # write to console current status
    #logging.info("Scraping data for link: {}".format(startlink))

    # get the page and make the soup
    attempt = 0
    r = ""
    while r == "":
        try:
            baseURL = "https://www.forexfactory.com/"
            r = requests.get(baseURL + startlink)
            break
        except:
            if attempt < 1:
                import time
                attempt += 1
                print("Attempt:", attempt)
                print("Connection refused by the server..")
                print("Let me sleep for 5 seconds")
                print("ZZzzzz...")
                time.sleep(5)
                print("Was a nice sleep, now let me continue...")
                continue
            else:
                print("!!! Connection to the news server failed. Insert news data manually !!!")
                is_there = input("Are there news today? (YES=Y / NO=AnyKey): ")
                is_there = is_there.upper()
                if is_there == "Y":
                    time = input("time (hh:mm): ")
                    dt = datetime.datetime.strptime(time, '%H:%M')
                    event = input("Event: ")
                    info = [dt, event]
                    news.append(info)
                    more = input("More? (YES=Y / NO=AnyKey): ")
                    more = more.upper()
                    while more == "Y":
                        time = input("time (hh:mm): ")
                        dt = datetime.datetime.strptime(time, '%H:%M')
                        event = input("Event: ")
                        info = [dt, event]
                        news.append(info)
                        more = input("More? (YES=Y / NO=AnyKey): ")
                        more = more.upper()
                    return
                elif is_there == "N":
                    return
                else:
                    continue

    data = r.text
    soup = BeautifulSoup(data, "lxml")

    # get and parse table data, ignoring details and graph
    table = soup.find("table", class_="calendar__table")

    # do not use the ".calendar__row--grey" css selector (reserved for historical data)
    trs = table.select("tr.calendar__row.calendar_row")
    fields = ["date","time","currency","impact","event","actual","forecast","previous"]

    # some rows do not have a date (cells merged)
    curr_year = startlink[-4:]
    curr_date = ""
    curr_time = ""
    time_delta = datetime.timedelta(hours=sei)
    for tr in trs:

        # fields may mess up sometimes, see Tue Sep 25 2:45AM French Consumer Spending
        # in that case we append to errors.csv the date time where the error is
        try:
            for field in fields:
                data = tr.select("td.calendar__cell.calendar__{}.{}".format(field,field))[0]
                # print(data)
                if field=="date" and data.text.strip()!="":
                    curr_date = data.text.strip()
                elif field=="time" and data.text.strip()!="":
                    # time is sometimes "All Day" or "Day X" (eg. WEF Annual Meetings)
                    if data.text.strip().find("Day")!=-1:
                        curr_time = "12:00am"
                    else:
                        curr_time = data.text.strip()
                elif field=="currency":
                    currency = data.text.strip()
                elif field=="impact":
                    # when impact says "Non-Economic" on mouseover, the relevant
                    # class name is "Holiday", thus we do not use the classname
                    impact = data.find("span")["title"]
                elif field=="event":
                    event = data.text.strip()
                elif field=="actual":
                    actual = data.text.strip()
                    # the state is to know if the actual value is better or worse than forecasted
                    if "better" in str(data):
                        state = "better"
                    elif "worse" in str(data):
                        state = "worse"
                    else:
                        state = "None"
                elif field=="forecast":
                    forecast = data.text.strip()
                elif field=="previous":
                    previous = data.text.strip()

            dt = datetime.datetime.strptime(",".join([curr_year,curr_date,curr_time]),
                                            "%Y,%a%b %d,%I:%M%p")
            tzadj = dt + time_delta
            if (currency == "USD" and impact == "High Impact Expected") or (currency == "USD" and event == "Bank Holiday"):
                #print(",".join([str(tzadj), currency, impact, event, actual, forecast, previous, state]))
                info = [tzadj, event]
                news.append(info)
        except:
            with open("errors.csv","a") as f:
                csv.writer(f).writerow([curr_year,curr_date,curr_time])


    #logging.info("Successfully retrieved data")
    return


# setLogger()
try:
    getEconomicCalendar("calendar.php?day={}".format(datetime.date.today().strftime("%b%d.%Y").lower()))
except:
    print('error to retrive news data. FORCING IT')
    def getEconomicCalendar_forced():
        global sei
        global news

        r = requests.get('https://nfs.faireconomy.media/ff_calendar_thisweek.json')
        try:
            r_dict = r.json()
        except:
            print('NEWS URL ERROR!')
            backup_url = input("enter JSON news url (ends at .json): ")
            r = requests.get(backup_url)
            try:
                r_dict = r.json()
            except:
                print('URL not working')
                input(" --- Press ENTER to quit --- ")
        curr_date = ""
        curr_time = ""
        time_delta = datetime.timedelta(hours=sei)
        for tr in r_dict:
            event = tr['title']
            currency = tr['country']
            date = tr['date'][:10]
            time = tr['date'][11:19]
            impact = tr['impact']
            # print(date, time, event, currency, impact)
            now = datetime.datetime.today()
            dt = parser.parse(str(date) + ' ' + str(time))
            tzadj = dt + time_delta
            # print(now.date() == tzadj.date())
            if ((currency == "USD" and impact == "High") or (currency == "USD" and event == "Bank Holiday")) and tzadj.date() == now.date():
                info = [tzadj, event]
                news.append(info)
        return
    getEconomicCalendar_forced()


#print(news)
if len(news) > 0:
    for i in news:
        news_time = i[0]
        news_in_session.append(news_time)
        news_event = i[1]
        if "FOMC" in news_event:
            print("FOMC, evening session is compromised")
            evening_comp = True #

        elif "Bank Holiday" in i[1]:
            print("Market closed today")
            rest = True

        else:
            # pre_news = i[0] - time_delta_pre_news
            # post_news = i[0] + time_delta_post_news

            print(news_time.date())
            print('news time:', news_time.time())
            print('news event:', news_event)

            # print('pre news:', pre_news.time())
            # print('post news:', post_news.time())

else:
    print("No news today")

# input(" --- Press ENTER to continue --- ")

mm = 2 #points <<<
session_mm = mm

print('\n')
print('LAST DAY INFO ---')

p_close = 0

# storing data from previous session in the DB -----------------------------------------------------
class Volume(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def historicalData(self, reqId, bar):
        global contratto
        today = datetime.date.today()
        volume = bar.volume
        date1 = bar.date
        date = date1[:4] + '-' + date1[4:6] + '-' + date1[6:]

        conn = sqlite3.connect('database.db') #<<<--- be sure is the correct DB
        cur = conn.cursor()
        cur.execute("INSERT INTO stats VALUES (NULL, ?, ?, NULL, NULL, ?, NULL)", (date, volume, contratto))
        conn.commit()
        conn.close()

        print("Last session: ", date)
        print("Daily volume: ", volume)
        print("Please, wait...")

    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        self.disconnect()

class Volatility(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def historicalData(self, reqId, bar):
        global contratto
        global p_close
        today = datetime.date.today()
        daily_max = bar.high
        daily_min = bar.low
        p_close = bar.close
        date1 = bar.date
        date = date1[:4] + '-' + date1[4:6] + '-' + date1[6:]
        range = daily_max - daily_min

        conn = sqlite3.connect('database.db') #<<<--- be sure is the correct DB
        cur = conn.cursor()
        cur.execute("UPDATE stats SET volatility= ? WHERE date= ?", (range, date))
        cur.execute("UPDATE stats SET data_check= ? WHERE date= ?", (today, date))
        cur.execute("UPDATE stats SET p_close= ? WHERE date= ?", (p_close, date))
        conn.commit()
        conn.close()

        print("Last session: ", date)
        print("Daily Range: ", range)
        print('Close: ', p_close)

    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        self.disconnect()

def Storage(choice, when):
    global contratto
    global socket
    app = choice()
    app.connect("127.0.0.1", socket, 0) #<<<<
    time.sleep(3)
    contract = Contract()
    contract.secType = "FUT"
    contract.exchange = "GLOBEX"
    contract.currency = "USD"
    contract.localSymbol = contratto # <<<--- change with the variable


    app.reqHistoricalData(2, contract, today.strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", when, 1, False, []) # change "data" with "today" <<<---
    app.run()

conn = sqlite3.connect('database.db') #<<<--- be sure is the correct DB
cur = conn.cursor()
cur.execute("SELECT * FROM stats ORDER BY id DESC LIMIT 1")
myresult = cur.fetchone()
conn.close()
yesterday = myresult[4]
today = datetime.date.today()
print(myresult)
print(yesterday)
print('CONTRACT:', contratto)
if str(today) != str(yesterday):
    Storage(Volume, 1)
    time.sleep(3)
    Storage(Volatility, 1)
    print("Data from yesterday stored in the DB")
else:
    print("Data in the DB are already stored")
    print('Retriving Previous close...')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    #selecting latest data from database
    cur.execute("SELECT * FROM stats ORDER BY id DESC LIMIT 1")
    retrived = cur.fetchone()
    conn.close()
    p_close = float(retrived[6])
    print('Previous close:', p_close)

# input(" --- Press ENTER to continue --- ")

### GET JOINT DATA -------------------------------------------------------------

def retrive_joint_data(days, store):

    global exp_volume
    global most_liquid
    global most_liquid2

    global hist_data_ES
    global hist_data_MES
    global joint_hist_data
    global joint_hist_volume
    global joint_hist_volatility

    exp_volume = 0
    most_liquid = None
    most_liquid2 = None

    hist_data_ES = dict()
    hist_data_MES = dict()
    joint_hist_data = dict()
    joint_hist_volume = list()
    joint_hist_volatility = list()

    def human_format(num):
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

    # formatting time_delta
    class DeltaTemplate(Template):
        delimiter = "%"

    def strfdelta(tdelta, fmt):
        d = {"D": tdelta.days}
        d["H"], rem = divmod(tdelta.seconds, 3600)
        d["M"], d["S"] = divmod(rem, 60)
        t = DeltaTemplate(fmt)
        return t.substitute(**d)


    print('\n')
    print('EXPIRATION INFO ES (for joint) ---')

    class Expirations(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)

        def error(self, reqId, errorCode, errorString):
            print("Error: ", reqId, " ", errorCode, " ", errorString)

        def historicalData(self, reqId, bar):
            global exp_volume
            print("HistoricalData. ", reqId, " Date:", bar.date, "Volume:", bar.volume)
            exp_volume = bar.volume

        def historicalDataEnd(self, reqId, start, end):
            super().historicalDataEnd(reqId, start, end)
            #print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
            self.disconnect()

    today = datetime.date.today()
    today_day = today.strftime("%A")
    td_delta = 1
    td = datetime.timedelta(days=td_delta)
    yesterday = today - td
    yesterday_day = yesterday.strftime("%A")
    while yesterday_day == "Sunday" or yesterday_day == "Saturday":
        td_delta += 1
        td = datetime.timedelta(days=td_delta)
        yesterday = today - td
        yesterday_day = yesterday.strftime("%A")

    print("Today:", today_day)
    print("Last trading day:", yesterday_day, yesterday)
    #print(yesterday)

    #getting the expiration days for the year
    def third_friday(year, month):
        """Return datetime.date for monthly option expiration given year and
        month
        """
        # The 15th is the lowest third day in the month
        third = datetime.date(year, month, 15)
        # What day of the week is the 15th?
        w = third.weekday()
        # Friday is weekday 4
        if w != 4:
            # Replace just the day (of month)
            third = third.replace(day=(15 + (4 - w) % 7))
        return third

    months = [3, 6, 9, 12]
    exps = list()
    today = datetime.date.today()
    for m in months:
        friday = third_friday(today.year, m)
        exps.append(friday)

    print(exps)

    #get volumes from all the expirations that day
    '''
    - Marzo = H (Dicembre - Marzo)
    - Giugno = M (Marzo - Giugno)
    - Settembre = U (Giugno - Settembre)
    - Dicembre = Z (Settembre - Dicembre)

    '''

    #warning! exclude expired security!
    exps_symbol = ['H', 'M', 'U', 'Z']
    exps_to_check = list()

    tdy = datetime.timedelta(weeks=52)

    if exps[0] <= today < exps[1]:
        year = str(today.year)
        year_var = year[-1]
        #building the ticker
        current_exp = "ES" + exps_symbol[1] + year_var
        next_exp = "ES" + exps_symbol[2] + year_var
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif exps[1] <= today < exps[2]:
        year = str(today.year)
        year_var = year[-1]
        #building the ticker
        current_exp = "ES" + exps_symbol[2] + year_var
        next_exp = "ES" + exps_symbol[3] + year_var
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif exps[2] <= today < exps[3]:
        year = str(today.year)
        year_var = year[-1]
        ny = today + tdy
        year1 = str(ny.year)
        year_var1 = year1[-1]
        #building the ticker
        current_exp = "ES" + exps_symbol[3] + year_var
        next_exp = "ES" + exps_symbol[0] + year_var1
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif exps[3] <= today:
        ny = today + tdy
        year1 = str(ny.year)
        year_var1 = year1[-1]
        #building the ticker
        current_exp = "ES" + exps_symbol[0] + year_var1
        next_exp = "ES" + exps_symbol[1] + year_var1
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif today < exps[0]:
        year = str(today.year)
        year_var = year[-1]
        #building the ticker
        current_exp = "ES" + exps_symbol[0] + year_var
        next_exp = "ES" + exps_symbol[1] + year_var
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    volumes = list()
    print("Checking the most liquid expiration...")
    global contratto
    contratto = None
    while contratto is None:
        volumes = list()
        for e in exps_to_check:

            app = Expirations()
            print(e)
            app.connect("127.0.0.1", socket, 888)

            time.sleep(0.1)

            contract = Contract()
            contract.secType = "FUT"
            contract.exchange = "GLOBEX"
            contract.currency = "USD"
            contract.localSymbol = e

            app.reqHistoricalData(2, contract, today.strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 0, 1, False, [])

            app.run()
            volumes.append(exp_volume)

        print(volumes)

        if volumes[0] > volumes[1]:
            print("Most liquid exp:", current_exp)
            most_liquid = current_exp
        elif volumes[0] < volumes[1]:
            print("Most liquid exp:", next_exp)
            most_liquid = next_exp

        contratto = most_liquid

    print('\n')

    # storing data from previous session in the DB -----------------------------------------------------
    class Volume(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)

        def error(self, reqId, errorCode, errorString):
            print("Error: ", reqId, " ", errorCode, " ", errorString)

        def historicalData(self, reqId, bar):
            global contratto
            today = datetime.date.today()
            volume = bar.volume
            date1 = bar.date
            date = date1[:4] + '-' + date1[4:6] + '-' + date1[6:]

            # print("Last session: ", date)
            # print("Daily volume: ", human_format(volume))
            print("Please, wait...")

            hist_data_ES[date] = {'volume' : volume, 'volatility' : 0}

        def historicalDataEnd(self, reqId, start, end):
            super().historicalDataEnd(reqId, start, end)
            self.disconnect()

    class Volatility(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)

        def error(self, reqId, errorCode, errorString):
            print("Error: ", reqId, " ", errorCode, " ", errorString)

        def historicalData(self, reqId, bar):
            global contratto
            global p_close
            today = datetime.date.today()
            daily_max = bar.high
            daily_min = bar.low
            p_close = bar.close
            date1 = bar.date
            date = date1[:4] + '-' + date1[4:6] + '-' + date1[6:]
            range = daily_max - daily_min


            # print("Last session: ", date)
            # print("Daily Range: ", range)

            hist_data_ES[date]['volatility'] = range

        def historicalDataEnd(self, reqId, start, end):
            super().historicalDataEnd(reqId, start, end)
            self.disconnect()

    def Storage(choice, when):
        global contratto
        global socket
        app = choice()
        app.connect("127.0.0.1", socket, 888) #<<<<
        time.sleep(0.1)
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto # <<<--- change with the variable


        app.reqHistoricalData(2, contract, today.strftime("%Y%m%d %H:%M:%S %Z"), days, "1 day", "TRADES", when, 1, False, []) # change "data" with "today" <<<---
        app.run()


    today = datetime.date.today()

    print('CONTRACT:', contratto)

    Storage(Volume, 1)
    time.sleep(0.1)
    Storage(Volatility, 1)

    # check last 10d average volatility
    def nearest_quarter(x):
        return round(x*4)/4

    def Average(lst):
        return sum(lst) / len(lst)


    print('\n')
    print('EXPIRATION INFO MES ---')

    class Expirations(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)

        def error(self, reqId, errorCode, errorString):
            print("Error: ", reqId, " ", errorCode, " ", errorString)

        def historicalData(self, reqId, bar):
            global exp_volume
            print("HistoricalData. ", reqId, " Date:", bar.date, "Volume:", bar.volume)
            exp_volume = bar.volume

        def historicalDataEnd(self, reqId, start, end):
            super().historicalDataEnd(reqId, start, end)
            #print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
            self.disconnect()

    today = datetime.date.today()
    today_day = today.strftime("%A")
    td_delta = 1
    td = datetime.timedelta(days=td_delta)
    yesterday = today - td
    yesterday_day = yesterday.strftime("%A")
    while yesterday_day == "Sunday" or yesterday_day == "Saturday":
        td_delta += 1
        td = datetime.timedelta(days=td_delta)
        yesterday = today - td
        yesterday_day = yesterday.strftime("%A")

    print("Today:", today_day)
    print("Last trading day:", yesterday_day, yesterday)

    #getting the expiration days for the year
    def third_friday(year, month):
        """Return datetime.date for monthly option expiration given year and
        month
        """
        # The 15th is the lowest third day in the month
        third = datetime.date(year, month, 15)
        # What day of the week is the 15th?
        w = third.weekday()
        # Friday is weekday 4
        if w != 4:
            # Replace just the day (of month)
            third = third.replace(day=(15 + (4 - w) % 7))
        return third

    months = [3, 6, 9, 12]
    exps = list()
    today = datetime.date.today()
    for m in months:
        friday = third_friday(today.year, m)
        exps.append(friday)

    print(exps)

    #get volumes from all the expirations that day
    '''
    - Marzo = H (Dicembre - Marzo)
    - Giugno = M (Marzo - Giugno)
    - Settembre = U (Giugno - Settembre)
    - Dicembre = Z (Settembre - Dicembre)

    '''

    #warning! exclude expired security!
    exps_symbol = ['H', 'M', 'U', 'Z']
    exps_to_check = list()

    tdy = datetime.timedelta(weeks=52)

    if exps[0] <= today < exps[1]:
        year = str(today.year)
        year_var = year[-1]
        #building the ticker
        current_exp = "MES" + exps_symbol[1] + year_var
        next_exp = "MES" + exps_symbol[2] + year_var
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif exps[1] <= today < exps[2]:
        year = str(today.year)
        year_var = year[-1]
        #building the ticker
        current_exp = "MES" + exps_symbol[2] + year_var
        next_exp = "MES" + exps_symbol[3] + year_var
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif exps[2] <= today < exps[3]:
        year = str(today.year)
        year_var = year[-1]
        ny = today + tdy
        year1 = str(ny.year)
        year_var1 = year1[-1]
        #building the ticker
        current_exp = "MES" + exps_symbol[3] + year_var
        next_exp = "MES" + exps_symbol[0] + year_var1
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif exps[3] <= today:
        ny = today + tdy
        year1 = str(ny.year)
        year_var1 = year1[-1]
        #building the ticker
        current_exp = "MES" + exps_symbol[0] + year_var1
        next_exp = "MES" + exps_symbol[1] + year_var1
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    elif today < exps[0]:
        year = str(today.year)
        year_var = year[-1]
        #building the ticker
        current_exp = "MES" + exps_symbol[0] + year_var
        next_exp = "MES" + exps_symbol[1] + year_var
        exps_to_check.append(current_exp)
        exps_to_check.append(next_exp)
        print("Current exp:", current_exp)
        print("Next exp:", next_exp)

    volumes = list()
    print("Checking the most liquid expiration...")
    global contratto2
    contratto2 = None
    while contratto2 is None:
        volumes = list()
        for e in exps_to_check:

            app = Expirations()
            print(e)
            app.connect("127.0.0.1", socket, 888)

            time.sleep(0.1)

            contract = Contract()
            contract.secType = "FUT"
            contract.exchange = "GLOBEX"
            contract.currency = "USD"
            contract.localSymbol = e

            app.reqHistoricalData(2, contract, today.strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 0, 1, False, [])

            app.run()
            volumes.append(exp_volume)

        print(volumes)

        if volumes[0] > volumes[1]:
            print("Most liquid exp:", current_exp)
            most_liquid2 = current_exp
        elif volumes[0] < volumes[1]:
            print("Most liquid exp:", next_exp)
            most_liquid2 = next_exp

        contratto2 = most_liquid2

    # storing data from previous session in the DB -----------------------------------------------------
    class Volume(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)

        def error(self, reqId, errorCode, errorString):
            print("Error: ", reqId, " ", errorCode, " ", errorString)

        def historicalData(self, reqId, bar):
            global contratto2
            today = datetime.date.today()
            volume = bar.volume
            date1 = bar.date
            date = date1[:4] + '-' + date1[4:6] + '-' + date1[6:]

            # print("Last session: ", date)
            # print("Daily volume: ", human_format(volume))
            print("Please, wait...")

            hist_data_MES[date] = {'volume' : volume, 'volatility' : 0}
            joint_hist_data[date] = {'volume': 0, 'volatility': 0}

        def historicalDataEnd(self, reqId, start, end):
            super().historicalDataEnd(reqId, start, end)
            self.disconnect()

    class Volatility(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)

        def error(self, reqId, errorCode, errorString):
            print("Error: ", reqId, " ", errorCode, " ", errorString)

        def historicalData(self, reqId, bar):
            global contratto2
            global p_close
            today = datetime.date.today()
            daily_max = bar.high
            daily_min = bar.low
            p_close = bar.close
            date1 = bar.date
            date = date1[:4] + '-' + date1[4:6] + '-' + date1[6:]
            range = daily_max - daily_min

            # print("Last session: ", date)
            # print("Daily Range: ", range)

            hist_data_MES[date]['volatility'] = range

        def historicalDataEnd(self, reqId, start, end):
            super().historicalDataEnd(reqId, start, end)
            self.disconnect()

    def Storage(choice, when):
        global contratto2
        global socket
        app = choice()
        app.connect("127.0.0.1", socket, 888) #<<<<
        time.sleep(0.1)
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto2 # <<<--- change with the variable


        app.reqHistoricalData(2, contract, today.strftime("%Y%m%d %H:%M:%S %Z"), days, "1 day", "TRADES", when, 1, False, []) # change "data" with "today" <<<---
        app.run()

    today = datetime.date.today()

    print('CONTRACT:', contratto2)

    Storage(Volume, 1)
    time.sleep(0.1)
    Storage(Volatility, 1)


    print('\n')
    print('ES data:')
    for i in hist_data_ES:
        print (i, hist_data_ES[i])

    print('\n')
    print('MES data:')
    for i in hist_data_MES:
        print (i, hist_data_MES[i])

    print('\n')

    for i in hist_data_ES:
        temp_volatility = list()
        temp_volatility.append(hist_data_ES.get(i, {}).get('volatility'))
        temp_volatility.append(hist_data_MES.get(i, {}).get('volatility'))
        joint_hist_data[i]['volatility'] = nearest_quarter(Average(temp_volatility))
        joint_hist_data[i]['volume'] = hist_data_ES.get(i, {}).get('volume') + hist_data_MES.get(i, {}).get('volume')


    print('JOINT data:')
    print('/' * 50)
    if store is True:
        conn = sqlite3.connect('database.db') #<<<--- be sure is the correct DB
        cur = conn.cursor()
        cur.execute("SELECT * FROM joint_stats ORDER BY id DESC LIMIT 1")
        myresult = cur.fetchone()
        conn.close()
        try:
            yesterday = myresult[4]
        except:
            yesterday = None
        today = datetime.date.today()

        if (str(today) != str(yesterday)) or (yesterday is None):
            stored = False
        else:
            stored = True
            print('Joint data already in the DB')

    volume_leaks = list()
    for i in joint_hist_data:
        volume_leak = round((hist_data_MES.get(i, {}).get('volume')/joint_hist_data.get(i, {}).get('volume'))*100)
        print (i, '-', 'Volume:', human_format(joint_hist_data.get(i, {}).get('volume')), '|', 'Volatility:', joint_hist_data.get(i, {}).get('volatility'), 'pt', '|', 'Volume leak:', volume_leak, '%')
        joint_hist_volume.append(joint_hist_data.get(i, {}).get('volume'))
        joint_hist_volatility.append(joint_hist_data.get(i, {}).get('volatility'))
        volume_leaks.append(volume_leak)
        if store is True:
            if stored is False:
                conn = sqlite3.connect('database.db') #<<<--- be sure is the correct DB
                cur = conn.cursor()
                cur.execute("INSERT INTO joint_stats VALUES (NULL, ?, ?, ?, ?, ?, ?)", (i, joint_hist_data.get(i, {}).get('volume'), joint_hist_data.get(i, {}).get('volatility'), today, contratto, volume_leak))
                conn.commit()
    if store is True:
        if stored is False:
            conn.close()

    global volume_leak_avg
    volume_leak_avg = Average(volume_leaks)/100
    print(volume_leak_avg)

    print('\n')
    print('Average Joint Volume:', human_format(Average(joint_hist_volume)))
    print('Average Joint Volatility:', nearest_quarter(Average(joint_hist_volatility)), 'pt')
    print('Average Volume Leak:', volume_leak_avg*100, '%')
    print('/' * 50)
    # print('\n')


retrive_joint_data('1 D', True)
### ----------------------------------------------------------------------------

reverse = 2 #previous 4.25
reverse_ob = 2
default_reverse = reverse_ob
range_bars_ticks = 5

# check last 10d average volatility
def nearest_quarter(x):
    return round(x*4)/4

print('\n')
print('LAST 10 DAYS INFO ---')

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def get_data_for_AVG_volatility_10d(type):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM stats ORDER BY id DESC LIMIT 10") #select last 10d
    # cur.execute("SELECT * FROM stats") #select ALL days

    myresult = cur.fetchall()
    raw = list()
    for i in myresult:
        vt = i[type] # M1 or max_move based on the type passed in
        raw.append(vt)
    conn.close()
    vts = list()
    for val in raw:
        if val != None :
            vts.append(val)
    if type == 3:
        print('Volatility:', vts)
    elif type == 2:
        print('Volume:', vts)
    def Average(lst):
        return sum(lst) / len(lst)

    return Average(vts)

avg_volatility_10d = nearest_quarter(get_data_for_AVG_volatility_10d(3))
avg_volume_10d = get_data_for_AVG_volatility_10d(2)
# print('Average volatility last 10 days:', avg_volatility_10d, 'points')
# print('Average volume last 10 days:', human_format(avg_volume_10d))

### set the reverse parameter accordingly to the scenario of the last 5d -----> ACTIVE
# if avg_volatility_5d > 27.5:
#     reverse = 2.75
#     range_bars_ticks = 10
#     print('--- WARNING ---')
#     print('Very high volatility scenario. Reverse parameter adjusted to:', reverse, 'points')
#     print('Virtual Range Bars used: 10 ticks')
# else:
#     print('Normal volatility scenario. Reverse parameter:', reverse, 'points')
#     print('Virtual Range Bars used: 5 ticks')



print('\n')
print('M1 INFO ---')

# DB HANDLE & M1 formula----------------------------------------------------------------------------
def M1_calc():
    global mm
    global session_mm
    global range_bars_ticks

    #getting data

    #connect to the database
    conn = sqlite3.connect('database.db')

    #create cursor
    cur = conn.cursor()

    #insert data in the database
    #cur.execute("INSERT INTO f_pom VALUES (NULL, ?, ?, ?)", (today, LLM, LM1))
    #conn.commit()

    #selecting latest data from database
    if f_pom is True:
        cur.execute("SELECT * FROM f_pom ORDER BY id DESC LIMIT 1")
    elif f_ser is True:
        cur.execute("SELECT * FROM f_ser ORDER BY id DESC LIMIT 1")

    myresult = cur.fetchone()

    #close database
    conn.close()

    yesterday = myresult[1]
    max_move = myresult[2]
    last_M1 = myresult[3]



    #function to round to the nearest 0.25
    def nearest_quarter(x):
        return round(x*4)/4

    #fix value
    alpha = 2/3

    M1_calc.today = datetime.date.today()

    #being sure isn't a second run in the same day
    if str(M1_calc.today) == str(yesterday):
        M1_calc.M1 = last_M1
    else:
        M1_calc.M1 = nearest_quarter((max_move - last_M1) * alpha + last_M1)

        #insert M1 & date in the database
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        if f_pom is True:
            cur.execute("INSERT INTO f_pom VALUES (NULL, ?, NULL, ?, NULL, ?, NULL)", (M1_calc.today, M1_calc.M1, range_bars_ticks))
        elif f_ser is True:
            cur.execute("INSERT INTO f_ser VALUES (NULL, ?, NULL, ?, NULL, ?, NULL)", (M1_calc.today, M1_calc.M1, range_bars_ticks))
        conn.commit()
        conn.close()

    # adaptive MM module <<<<<<<<<<----------  MM MANAGING
    if M1_calc.M1 <= 0:
        print("Error - M1 <= 0")
    elif 0 < M1_calc.M1 < 5:
        mm = 1
        session_mm = mm
    elif 5 <= M1_calc.M1 <= 7.50:
        mm = 1.5 # <<<<<----- it should be 1.5 normally, but 2 with a partially adaptive MM
        session_mm = mm
    elif M1_calc.M1 > 7.50:
        mm = 2
        session_mm = mm

    #sound
    #winsound.PlaySound("sounds/m1_entry.wav", winsound.SND_ASYNC)
    print("---------------------")
    print("Today M1: ", M1_calc.M1)
    if f_pom is True:
        print("Fascia pomeridiana")
        winsound.PlaySound("sounds/voice/Allison/M1_f_pom.wav", winsound.SND_ASYNC)
    elif f_ser is True:
        print("Fascia serale")
        winsound.PlaySound("sounds/voice/Allison/M1_f_ser.wav", winsound.SND_ASYNC)
    print("MM: ", mm)
    print("--------------------- READY >>>")

if rest is False:
    M1_calc()
    M1 = M1_calc.M1
    today = M1_calc.today
    M1_original = M1

    accuracy = None
    #Calculating Accuracy -------------- COMING SOON (when enough data)
    def accuracy_calc():
        global accuracy
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        if f_pom is True:
          cur.execute("SELECT * FROM f_pom_Profit ORDER BY id DESC LIMIT 1")
        elif f_ser is True:
          cur.execute("SELECT * FROM f_ser_Profit ORDER BY id DESC LIMIT 1")
        myresult1 = cur.fetchone()
        if f_pom is True:
          cur.execute("SELECT * FROM f_pom_Loss ORDER BY id DESC LIMIT 1")
        elif f_ser is True:
          cur.execute("SELECT * FROM f_ser_Loss ORDER BY id DESC LIMIT 1")
        myresult2 = cur.fetchone()
        conn.close()

        pr = myresult1[0]
        lr = myresult2[0]
        tot_op = pr + lr

        accuracy = round((pr/tot_op)*100, 0)
        print("Gain probability: ", accuracy, "%")
    #---------------------------------------------------------------------------------------------------
    accuracy_calc()


    print('\n')
    print('OPERATIVITY INFO ---')

    #MODE MANAGER---------------------------------------------------------------------------------------
    was_automatic = False
    print("---------- ES ----------")
    automatic = False
    manual = False
    # winsound.PlaySound("sounds/voice/Allison/mode_ask.wav", winsound.SND_ASYNC)
    # while automatic is False and manual is False:
    #     print("A = automatic mode")
    #     print("M = manual mode")
    #     mode = str(input("Select mode: "))
    #     mode = mode.upper()
    #     if mode == "A":
    #         confirm = input("Confirm automatic mode activation (YES=Y / NO=AnyKey): ")
    #         confirm = confirm.upper()
    #         if confirm == "Y":
    #             automatic = True
    #             manual = False
    #             was_automatic = True
    #             winsound.PlaySound("sounds/voice/Allison/automatic_mode.wav", winsound.SND_ASYNC)
    #             print("---------->>> AUTOMATIC MODE ACTIVE <<<----------")
    #         elif confirm == "N":
    #             continue
    #     if mode == "M":
    #         automatic = False
    #         manual = True
    #         winsound.PlaySound("sounds/voice/Allison/manual_mode.wav", winsound.SND_ASYNC)
    #         print("---------->>> MANUAL MODE ACTIVE <<<----------")

    #SET AUTOMATIC AS DEFAULT
    automatic = True
    manual = False
    was_automatic = True
    # winsound.PlaySound("sounds/voice/Allison/automatic_mode.wav", winsound.SND_ASYNC)
    print("---------->>> AUTOMATIC MODE ACTIVE <<<----------")
    #---------------------------------------------------------------------------------------------------



    #AVG MOVE CALC MODULE and historical data
    #-------------------------------------------------------------------------------
    def Average(lst):
        return sum(lst) / len(lst)

    def nearest_quarter(x):
        return round(x*4)/4


    year_to_retrive = 'ALL'
    future_to_retrive = 'ES'

    conn = sqlite3.connect('database.db') #<<<--- be sure is the correct DB

    cur = conn.cursor()

    year_encd = str(year_to_retrive)

    #GET MOVES
    global moves_pom
    global moves_ser
    if year_encd == 'ALL':
        # cur.execute("SELECT movement FROM f_pom_movements WHERE contract IS NOT NULL AND contract != ?", ("",)) ##excluding old moves
        cur.execute("SELECT movement FROM f_pom_movements")
        moves_pom = cur.fetchall()
        # cur.execute("SELECT movement FROM f_ser_movements WHERE contract IS NOT NULL AND contract != ?", ("",))
        cur.execute("SELECT movement FROM f_ser_movements")
        moves_ser = cur.fetchall()

    else:
        # cur.execute("SELECT movement FROM f_pom_movements WHERE strftime('%Y', date) = ? AND contract IS NOT NULL AND contract != ?", (year_encd, ""))
        cur.execute("SELECT movement FROM f_pom_movements WHERE strftime('%Y', date) = ?", (year_encd,))
        moves_pom = cur.fetchall()
        # cur.execute("SELECT movement FROM f_ser_movements WHERE strftime('%Y', date) = ? AND contract IS NOT NULL AND contract != ?", (year_encd, ""))
        cur.execute("SELECT movement FROM f_ser_movements WHERE strftime('%Y', date) = ?", (year_encd,))
        moves_ser = cur.fetchall()




    filtered_moves_pom = list()
    filtered_moves_ser = list()
    filtered_moves_tot = list()

    if future_to_retrive == 'ES':
        for i in moves_pom:
            if i[0] >= 5:
                filtered_moves_pom.append(i[0])

        for i in moves_ser:
            if i[0] >= 5:
                filtered_moves_ser.append(i[0])


    for i in filtered_moves_pom:
        filtered_moves_tot.append(i)
    for i in filtered_moves_ser:
        filtered_moves_tot.append(i)

    try:
        avg_pom = str(nearest_quarter(Average(filtered_moves_pom)))
    except:
        avg_pom = 5

    try:
        avg_ser = str(nearest_quarter(Average(filtered_moves_ser)))
    except:
        avg_ser = 5

    try:
        avg_tot = str(nearest_quarter(Average(filtered_moves_tot)))
    except:
        avg_tot = 5

    #GET HISTORICAL
    global historical_volume
    global historical_volatility

    def human_format(num):
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

    cur.execute("SELECT volume FROM stats")
    full_volume_stats_raw = cur.fetchall()
    conn.commit()

    cur.execute("SELECT volatility FROM stats")
    full_volatility_stats_raw = cur.fetchall()

    full_volume_stats = list()
    full_volatility_stats = list()

    for i in full_volume_stats_raw:
        for x in i:
            full_volume_stats.append(x)

    for i in full_volatility_stats_raw:
        for x in i:
            full_volatility_stats.append(x)

    try:
        historical_volume = float(round(Average(full_volume_stats)))
    except:
        historical_volume = 1500000
    try:
        historical_volatility = float(nearest_quarter(Average(full_volatility_stats)))
    except:
        historical_volatility = 25

    conn.close()

    retrive_joint_data('10 D', False)

    print('-' * 50)
    print('\n')
    print('AVG MOVE afternoon:', avg_pom)
    print('AVG MOVE evening:', avg_ser)
    print('AVG MOVE tot:', avg_tot)
    print('\n')
    print('Historical average Volume:', human_format(historical_volume))
    print('Historical average Volatility:', historical_volatility, 'points')
    print('Average Volume last 10 days:', human_format(avg_volume_10d))
    print('Average Volatility last 10 days:', avg_volatility_10d, 'points')
    print('\n')
    print('-' * 50)
    #-------------------------------------------------------------------------------



    #---------------------------------------------------------------------------------------------------

    #ESSENTIALS ---
    original_size = int(input("Enter your size: ")) #contracts <<<
    size = original_size
    # mm = 2 #points <<< moved above
    emergency_size = 0
    pre_session_size = original_size

    dynamic_size_increase = False ### <<<--- Enable/Disable dynamic size increasing
    double_size_low_vol = False
    print('Dynamic size increase:', dynamic_size_increase)

# reverse = 2
#
# # check last 10d average volatility
# def nearest_quarter(x):
#     return round(x*4)/4
#
# def get_data_for_AVG_volatility_10d(type):
#     conn = sqlite3.connect('database.db')
#     cur = conn.cursor()
#
#     cur.execute("SELECT * FROM stats ORDER BY id DESC LIMIT 10")
#
#     myresult = cur.fetchall()
#     raw = list()
#     for i in myresult:
#         vt = i[type] # M1 or max_move based on the type passed in
#         raw.append(vt)
#     conn.close()
#     vts = list()
#     for val in raw:
#         if val != None :
#             vts.append(val)
#     print(vts)
#     def Average(lst):
#         return sum(lst) / len(lst)
#
#     return Average(vts)
#
# avg_volatility_10d = nearest_quarter(get_data_for_AVG_volatility_10d(3))
# print('Average volatility last 10 days:', avg_volatility_10d, 'points')
#
# ### set the reverse parameter accordingly to the scenario of the last 10d -----> ACTIVE
# if avg_volatility_10d > 25:
#     reverse = 3
#     print('--- WARNING ---')
#     print('Very high volatility scenario. Reverse parameter adjusted to:', reverse, 'points')
#     print('Virtual Range Bars used: 10 ticks')
# else:
#     print('Normal volatility scenario. Reverse parameter:', reverse, 'points')
#     print('Virtual Range Bars used: 5 ticks')

#Expiration handle----------------------------------------------------------------------------------
# year = str(today.year)
# year_var = year[-1]
# print('''
# - Marzo = H
# - Giugno = M
# - Settembre = U
# - Dicembre = Z
# ''')
# expiration = input("Insert expiration: ")
# exp_var = expiration.capitalize()
#
# contratto = "ES" + exp_var + year_var
# print(contratto)
#---------------------------------------------------------------------------------------------------
contratto = most_liquid

def p_and_l(pt):
    ticks = pt/0.25
    return ticks

# VARIABLES ----------

VP_on = False

PAs_counter = 0
counting_UP = False
counting_DOWN = False
PAs_to_rev_list = list()
PAs_avg_to_rev = 0

volatility_expected = None

times = list()
start = time.time()
end = time.time()

pl = int(p_and_l(mm)) #profit and loss

#observe = True
first_move_notification = True
automatic_notification = True
manual_news_notification = True
manual_trigger_notification = True
manual_notification = True
notification = True
notif_start1 = datetime.time(quindici, 25, 0)
notif_end1 = datetime.time(quindici, 26, 0)
notif_start2 = datetime.time(diciannove, 40, 0)
notif_end2 = datetime.time(diciannove, 41, 0)

order = -1
last_order = 0

STP_operativity = False # ON / OFF (it could interfer with dynamic M1)
continuation_mode = False
if rest is False:
    if M1 >= 11 and STP_operativity is True:
        continuation_mode = True
        print('--- STP ORDERS ALLOWED ---')

continuation_margin = 1.25

count = -1

five_min_done = False
five_min_reset = False
try_again_reset = False

op_reset_allowed = True #### ALLOW MULTIPLE OPERATIONS or RESET IF ORDER NOT PLACED
reset_timer = 0

up_trend = False
dwn_trend = False
up_trend_ob = False
dwn_trend_ob = False

last_price = None
current_price = None
move = 0
move_ob = 0
rev_move = 0
rev_move_ob = 0
last_max = 0
last_max_ob = 0
last_min = 1000000000
last_min_ob = 1000000000

price_levels = list()
movements = list()
movements_ob = list()
# movements_cleaned = list()
# movements_cleaned_ob = list()
max_move = -1
average_move = 0
move_in_range = False
last_avg_move_check = False

if f_pom is True:
    start_time = datetime.time(quindici, 15, 0)
    end_time = datetime.time(sedici, 30, 0)
    start_trading_time = datetime.time(quindici, 35, 1)
    end_trading_time = datetime.time(sedici, 29, 0)
    start_op_time = datetime.time(quindici, 30, 0)
elif f_ser is True:
    start_time = datetime.time(diciannove, 30, 0)
    end_time = datetime.time(ventuno, 45, 0)
    start_trading_time = datetime.time(diciannove, 45, 0)
    end_trading_time = datetime.time(ventuno, 44, 0)
    start_op_time = datetime.time(diciannove, 45, 0)

go = False
done = False
op_done = False

daily_max = 0
daily_min = 1000000000

first_hour_max = 0
first_hour_min = 1000000000

pos = list()
executed = False
result = None

tp_multiplier = 1 #change this to set RR 1 is 1:1, 2 is 2:1 etc

gain = "+" + str(pl*tp_multiplier)
loss = "-" + str(pl)

if rest is False:
    print("Potential gain: ", gain)
    print("Potential loss: ", loss)

tp = 0
sl = 0
entry_price = 0

trigger_price_delta = 2
trigger_price = -1
order_placed = False

is_long = False
is_short = False

difference = 0
difference_ob = 0

fm_check_done = False

green_light = True

#----------
is_closed = True

range = 0

gap_allowed = 1

order_moved = False

default_dynamic_M1 = False
dynamic_M1 = default_dynamic_M1

position_manager = True
exit_price_position_manager = 0
position_manager_ready = False
stp_moved = False

volume_profile_active = True
sell_levels = None
buy_levels = None

#Telegram API
T_url = "https://api.telegram.org/bot1264496829:AAFmR_r3sU2lZsJOZW1Fjh7cVYfQmlXztCM/"

def send_message(chat_id, message_text):
    params = {"chat_id": chat_id, "text": message_text}
    response = requests.post(T_url + "sendMessage", data=params)
    return response

#MM calculation -------------------------- <<< Prototype
def mm_check(max, min):
    range = max - min
    if range < 12.75:
        return 1
    if 13 <= range < 25:
        return 1.5
    if 25 <= range:
        return 2

def calibrate_security():
    global gap_allowed

    def Average(lst):
        return sum(lst) / len(lst)

    def nearest_quarter(x):
        return round(x*4)/4

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM gaps ORDER BY id DESC LIMIT 10")
    myresult = cur.fetchall()
    conn.close()
    gaps_list = list()
    for i in myresult:
        gaps_list.append(i[2])
    try:
        gap_allowed = nearest_quarter(Average(gaps_list))
    except:
        gap_allowed = 2
    print('Gap allowed:', gap_allowed)

    # def get_data_for_AVG(type):
    #     conn = sqlite3.connect('database.db')
    #     cur = conn.cursor()
    #     if f_pom is True:
    #         cur.execute("SELECT * FROM f_pom ORDER BY id DESC LIMIT 10")
    #     elif f_ser is True:
    #         cur.execute("SELECT * FROM f_ser ORDER BY id DESC LIMIT 10")
    #     myresult = cur.fetchall()
    #     raw = list()
    #     for i in myresult:
    #         M1 = i[type] # M1 or max_move based on the type passed in
    #         raw.append(M1)
    #     conn.close()
    #     m1s = list()
    #     for val in raw:
    #         if val != None :
    #             m1s.append(val)
    #
    #     def Average(lst):
    #         return sum(lst) / len(lst)
    #
    #     return Average(m1s)
    #
    # avg_M1 = get_data_for_AVG(3)
    # avg_move = get_data_for_AVG(2)
    # AVG = nearest_quarter((avg_M1 + avg_move)/2)
    # print('AVG M1 & Moves =', AVG)

    # if AVG >= 10:
    #     gap_allowed = 1.25
    #     print('High risk profile - Gap allowed:', gap_allowed)
    # elif 7.5 <= AVG < 10:
    #     gap_allowed = 1
    #     print('Medium risk profile - Gap allowed:', gap_allowed)
    # elif AVG < 7.5:
    #     gap_allowed = 1 ##### <<<--- EVENTUALLY 0.75
    #     print('Low risk profile - Gap allowed:', gap_allowed)

    # if volatility_expected == 'High':
    #     gap_allowed = nearest_quarter(1.25 + (1.25 * volume_leak_avg))
    #     print('High risk profile - Gap allowed:', gap_allowed)
    # elif volatility_expected == 'Medium':
    #     gap_allowed = nearest_quarter(1 + (1 * volume_leak_avg))
    #     print('Medium risk profile - Gap allowed:', gap_allowed)
    # elif volatility_expected == 'Low':
    #     gap_allowed = nearest_quarter(1 + (1 * volume_leak_avg)) ##### <<<--- EVENTUALLY 0.75
    #     print('Low risk profile - Gap allowed:', gap_allowed)

# def op_reset():
#     order = -1
#     print('order:', order)
#     last_order = 0
#     print('last order:', last_order)
#     go = False
#     print('go:', go)
#     done = False
#     print('done:', done)
#     op_done = False
#     print('op done:', op_done)
#     tp = 0
#     print('tp:', tp)
#     sl = 0
#     print('sl:', sl)
#     entry_price = 0
#     print('entry price:', entry_price)
#     trigger_price = -1
#     print('trigger price:', trigger_price)
#     fm_check_done = False ### <---
#     print('fm check done:', fm_check_done)
#     order_moved = False
#     print('order moved:', order_moved)
#     exit_price_position_manager = 0
#     print('exit price position manager:', exit_price_position_manager)
#
#     print('!!! OPERATIVITY RESET !!!')

class TestApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString) #504 errorCode for not connected
        if errorCode == 504:
            print('Connection error detected, SLEEP MODE ACTIVE')
            #sleep mode
            hours = [1,2,3,4,5,6,7,8,9,10]
            minutes = [1,2,3,4,5,6,7,8,9,10,
                11,12,13,14,15,16,17,18,19,20,
                21,22,23,24,25,26,27,28,29,30,
                31,32,33,34,35,36,37,38,39,40,
                41,42,43,44,45,46,47,48,49,50,
                51,52,53,54,55,56,57,58,59,60]
            for h in hours:
                for m in minutes: #1h
                    time.sleep(60) #1min

    #get positions
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        global pos
        super().position(account, contract, position, avgCost)
        #print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:", contract.currency, "Position:", position, "Avg cost:", avgCost)
        if contract.symbol == "ES":
            pos.append(contract.symbol)
            pos.append(int(position))

    def positionEnd(self):
        global positions
        super().positionEnd()
        #print("PositionEnd")
        global pos
        global executed
        global is_long
        global is_short
        global emergency_size
        global is_closed
        #print(pos)
        if len(pos) > 0:
            if pos[-1] != 0:
                emergency_size = int(abs(pos[-1])) ###emergency_size to be set for emergency close position
                executed = True
                is_closed = False
                if pos[-1] > 0:
                    is_long = True
                    # is_short = False
                elif pos[-1] < 0:
                    # is_long = False
                    is_short = True
            elif pos[-1] == 0:
                is_closed = True
                #executed = False
                # is_long = False
                # is_short = False
        # elif len(pos) == 0:
            #executed = False
            # is_long = False
            # is_short = False
        #print("Executed:", executed)
        pos = list()

    def position_check(self):
        while True:
            self.reqPositions()
            time.sleep(0.1)


    def security_system(self):
        global start_op_time
        global end_time
        global done
        global go
        global automatic
        global order_placed
        global executed
        global is_long
        global is_short
        global difference ####
        global current_price
        global last_price
        global green_light
        global is_closed
        global gap_allowed
        global T_url
        global volatility_expected

        time.sleep(3)
        while True:
            if up_trend is True or dwn_trend is True:
                difference = current_price - last_price
                last_price = current_price
                # print("Difference: ", difference)
            now = datetime.datetime.today()
            if start_op_time <= now.time() <= end_time:
                    #observe = False
                    if done is False and go is True and automatic is True:
                        if difference > gap_allowed or difference < -gap_allowed:  ### <<<------------ pay attention
                            green_light = False
                            done = True
                            go = False
                            print(now.time())
                            print("GAP: ", difference)
                            print("Too much volatility. Security on")
                            if order_placed is True and executed is False and automatic is True and is_closed is True:
                                # self.reqGlobalCancel()
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                order_placed = False
                                is_long = False #
                                is_short = False #
                                print("Orders canceled because there is too much volatility")
                            winsound.PlaySound("sounds/voice/Allison/security.wav", winsound.SND_ASYNC)
                            send_message(25169251, ('ES - Too much volatility. Security on'))

                            todayDB = datetime.date.today()
                            conn = sqlite3.connect('database.db')
                            cur = conn.cursor()
                            cur.execute("INSERT INTO gaps VALUES (NULL, ?, ?)", (todayDB, abs(difference)))
                            conn.commit()
                            conn.close()
                            print("Gap saved in the DB")
            time.sleep(0.3)

    def trade_logic(self):
        global done
        global go
        global executed
        global is_long
        global is_short
        global current_price
        global tp
        global sl
        global result
        global gain
        global loss
        global f_pom
        global f_ser
        global op_done
        global emergency_size

        global entry_time
        global exit_time
        global size
        global action
        global future
        global contratto
        global entry_price
        global exit_price
        global punti
        global pl_dollars
        global trade_duration

        global commissions
        global mm
        global session_mm

        global T_url

        global position_manager
        global exit_price_position_manager
        global position_manager_ready
        global stp_moved

        global op_reset_allowed
        global try_again_reset

        global order_placed

        global order
        global last_order
        global trigger_price_delta
        global trigger_price
        global fm_check_done
        # global green_light
        global order_moved
        global reset_timer
        global news_range


        commissions = 4.20 # <<<---------- SET COMMISSIONS
        multiplier = 50

        future = 'ES'

        def time_conversion(time1):
            new = list()
            split = time1.split(':')
            for i in split:
                if int(i) < 10:
                    i1 = '0'+str(i)
                    new.append(i1)
                else:
                    new.append(i)
            # print(new)
            # print(new)
            new.insert(1,':')
            new.insert(3,':')
            puff = ''
            for n in new:
                n1 = str(n)
                puff += n1

            return puff

        time.sleep(3)
        while True:
            now = datetime.datetime.today()
            if done is True and go is False: ### TLM
                #trade logic
                if executed is True and is_short is True and op_done is False: #add the op_done variable
                    if current_price < tp:
                        exit_price = tp
                        punti = -(exit_price - entry_price)
                        result = "GAIN " + gain
                        winsound.PlaySound("sounds/voice/Allison/gain.wav", winsound.SND_ASYNC)
                        exit_time = now
                        trade_duration = strfdelta((exit_time - entry_time), "%H:%M:%S")
                        trade_duration = time_conversion(trade_duration)
                        entry_time = entry_time.strftime("%H:%M:%S")
                        exit_time = exit_time.strftime("%H:%M:%S")
                        print(now.time())
                        ###########################################
                        # print("Take Profit Price: ", tp)
                        # print("Stop Loss Price: ", sl)
                        # print("Current Price: ", current_price)
                        # print("Boolean Check - price lower than TP: ", current_price < tp)
                        ###########################################
                        print("Operation: ", result)
                        # print("Executed:", executed)
                        print("1.1")
                        print("**********")
                        time.sleep(1)
                        executed = False
                        is_long = False #
                        is_short = False #
                        op_done = True
                        send_message(25169251, ('ES - GAIN'))
                        time.sleep(1)
                        if op_reset_allowed is True:
                            self.cancelOrder(self.nextValidOrderId-1)
                            self.cancelOrder(self.nextValidOrderId-2)
                            self.cancelOrder(self.nextValidOrderId-3)
                            self.cancelOrder(self.nextValidOrderId-4)
                            self.cancelOrder(self.nextValidOrderId-5)
                            self.cancelOrder(self.nextValidOrderId-6)
                            time.sleep(1)
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        #     op_reset()

                    elif current_price >= sl:
                        exit_price = sl
                        punti = -(exit_price - entry_price)
                        result = "LOSS " + loss
                        winsound.PlaySound("sounds/voice/Allison/loss.wav", winsound.SND_ASYNC)
                        exit_time = now
                        trade_duration = strfdelta((exit_time - entry_time), "%H:%M:%S")
                        trade_duration = time_conversion(trade_duration)
                        entry_time = entry_time.strftime("%H:%M:%S")
                        exit_time = exit_time.strftime("%H:%M:%S")
                        print(now.time())
                        ###########################################
                        # print("Take Profit Price: ", tp)
                        # print("Stop Loss Price: ", sl)
                        # print("Current Price: ", current_price)
                        ###########################################
                        print("Operation: ", result)
                        # print("Executed:", executed)
                        print("1.2")
                        print("**********")
                        time.sleep(1)
                        executed = False
                        is_long = False #
                        is_short = False
                        op_done = True
                        send_message(25169251, ('ES - LOSS'))
                        time.sleep(1)
                        if op_reset_allowed is True:
                            self.cancelOrder(self.nextValidOrderId-1)
                            self.cancelOrder(self.nextValidOrderId-2)
                            self.cancelOrder(self.nextValidOrderId-3)
                            self.cancelOrder(self.nextValidOrderId-4)
                            self.cancelOrder(self.nextValidOrderId-5)
                            self.cancelOrder(self.nextValidOrderId-6)
                            time.sleep(1)
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        #     op_reset()

                    # position manager
                    elif current_price == tp or current_price == (tp + 0.25) and position_manager_ready is False and position_manager is True and automatic is True and stp_moved is False:
                        if mm > 1:
                            position_manager_ready = True
                            TestApp.move_stp_down(self)
                            print('Position manager triggered and ready')
                            stp_moved = True
                            print('time:', now)
                    # elif current_price == exit_price_position_manager or current_price > exit_price_position_manager and position_manager_ready is True and position_manager is True:
                    #     if automatic is True:
                    #         TestApp.close_short(self)
                    #         time.sleep(1)
                    #         # self.reqGlobalCancel()
                    #         self.cancelOrder(self.nextValidOrderId-1)
                    #         self.cancelOrder(self.nextValidOrderId-2)
                    #         self.cancelOrder(self.nextValidOrderId-3)
                    #         print("!!! MANAGED !!!")
                    #         is_short = False
                    #         is_long = False
                    #         executed = False

                    elif position_manager_ready is True and current_price >= exit_price_position_manager:
                        print('!!! MANAGED !!!')
                        time.sleep(1)
                        executed = False
                        is_long = False #
                        is_short = False
                        op_done = True
                        send_message(25169251, ('ES - Managed'))
                        print('time:', now)
                        time.sleep(1)
                        if op_reset_allowed is True:
                            self.cancelOrder(self.nextValidOrderId-1)
                            self.cancelOrder(self.nextValidOrderId-2)
                            self.cancelOrder(self.nextValidOrderId-3)
                            self.cancelOrder(self.nextValidOrderId-4)
                            self.cancelOrder(self.nextValidOrderId-5)
                            self.cancelOrder(self.nextValidOrderId-6)
                            time.sleep(1)
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True: ######## THIS COULD CAUSE PROBLEMS
                        #     # op_reset()
                        #     order = -1
                        #     last_order = 0
                        #     go = False
                        #     done = False
                        #     op_done = False
                        #     tp = 0
                        #     sl = 0
                        #     entry_price = 0
                        #     trigger_price = -1
                        #     fm_check_done = False ### <---
                        #     # green_light = True ### <---
                        #     order_moved = False
                        #     exit_price_position_manager = 0
                        #     reset_timer = 0 ##### USE THIS TO DELAY RESET IN CASE OP DONE IS TRUE AND AN OP HAS TO BE CLOSED IN EMERGENCY
                        #
                        #     print('!!! OPERATIVITY RESET !!!')

                    # else: # BETA 26 OTT 2020
                    #     break

                elif executed is True and is_long is True and op_done is False:
                    if current_price > tp:
                        exit_price = tp
                        punti = (exit_price - entry_price)
                        result = "GAIN " + gain
                        winsound.PlaySound("sounds/voice/Allison/gain.wav", winsound.SND_ASYNC)
                        exit_time = now
                        trade_duration = strfdelta((exit_time - entry_time), "%H:%M:%S")
                        trade_duration = time_conversion(trade_duration)
                        entry_time = entry_time.strftime("%H:%M:%S")
                        exit_time = exit_time.strftime("%H:%M:%S")
                        print(now.time())
                        ###########################################
                        # print("Take Profit Price: ", tp)
                        # print("Stop Loss Price: ", sl)
                        # print("Current Price: ", current_price)
                        # print("Boolean Check - price higher than TP: ", current_price > tp)
                        ###########################################
                        print("Operation: ", result)
                        # print("Executed:", executed)
                        print("2.1")
                        print("**********")
                        time.sleep(1)
                        executed = False
                        is_long = False
                        is_short = False
                        op_done = True
                        send_message(25169251, ('ES - GAIN'))
                        time.sleep(1)
                        if op_reset_allowed is True:
                            self.cancelOrder(self.nextValidOrderId-1)
                            self.cancelOrder(self.nextValidOrderId-2)
                            self.cancelOrder(self.nextValidOrderId-3)
                            self.cancelOrder(self.nextValidOrderId-4)
                            self.cancelOrder(self.nextValidOrderId-5)
                            self.cancelOrder(self.nextValidOrderId-6)
                            time.sleep(1)
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        #     op_reset()

                    elif current_price <= sl:
                        exit_price = sl
                        punti = (exit_price - entry_price)
                        result = "LOSS " + loss
                        winsound.PlaySound("sounds/voice/Allison/loss.wav", winsound.SND_ASYNC)
                        exit_time = now
                        trade_duration = strfdelta((exit_time - entry_time), "%H:%M:%S")
                        trade_duration = time_conversion(trade_duration)
                        entry_time = entry_time.strftime("%H:%M:%S")
                        exit_time = exit_time.strftime("%H:%M:%S")
                        print(now.time())
                        ###########################################
                        # print("Take Profit Price: ", tp)
                        # print("Stop Loss Price: ", sl)
                        # print("Current Price: ", current_price)
                        ###########################################
                        print("Operation: ", result)
                        # print("Executed:", executed)
                        print("2.2")
                        print("**********")
                        time.sleep(1)
                        executed = False
                        is_long = False
                        is_short = False
                        op_done = True
                        send_message(25169251, ('ES - LOSS'))
                        time.sleep(1)
                        if op_reset_allowed is True:
                            self.cancelOrder(self.nextValidOrderId-1)
                            self.cancelOrder(self.nextValidOrderId-2)
                            self.cancelOrder(self.nextValidOrderId-3)
                            self.cancelOrder(self.nextValidOrderId-4)
                            self.cancelOrder(self.nextValidOrderId-5)
                            self.cancelOrder(self.nextValidOrderId-6)
                            time.sleep(1)
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        #     op_reset()

                    # position manager
                    elif current_price == tp or current_price == (tp - 0.25) and position_manager_ready is False and position_manager is True and automatic is True and stp_moved is False:
                        if mm > 1:
                            position_manager_ready = True
                            TestApp.move_stp_up(self)
                            print('Position manager triggered and ready')
                            stp_moved = True
                            print('time:', now)
                    # elif current_price == exit_price_position_manager or current_price < exit_price_position_manager and position_manager_ready is True and position_manager is True:
                    #     if automatic is True:
                    #         TestApp.close_long(self)
                    #         time.sleep(1)
                    #         # self.reqGlobalCancel()
                    #         self.cancelOrder(self.nextValidOrderId-1)
                    #         self.cancelOrder(self.nextValidOrderId-2)
                    #         self.cancelOrder(self.nextValidOrderId-3)
                    #         print("!!! MANAGED !!!")
                    #         is_long = False
                    #         is_short = False
                    #         executed = False

                    elif position_manager_ready is True and current_price <= exit_price_position_manager:
                        print('!!! MANAGED !!!')
                        time.sleep(1)
                        executed = False
                        is_long = False #
                        is_short = False
                        op_done = True
                        send_message(25169251, ('ES - Managed'))
                        print('time:', now)
                        time.sleep(1)
                        if op_reset_allowed is True:
                            self.cancelOrder(self.nextValidOrderId-1)
                            self.cancelOrder(self.nextValidOrderId-2)
                            self.cancelOrder(self.nextValidOrderId-3)
                            self.cancelOrder(self.nextValidOrderId-4)
                            self.cancelOrder(self.nextValidOrderId-5)
                            self.cancelOrder(self.nextValidOrderId-6)
                            time.sleep(1)
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        #     # op_reset()
                        #     order = -1
                        #     last_order = 0
                        #     go = False
                        #     done = False
                        #     op_done = False
                        #     tp = 0
                        #     sl = 0
                        #     entry_price = 0
                        #     trigger_price = -1
                        #     fm_check_done = False ### <---
                        #     # green_light = True ### <---
                        #     order_moved = False
                        #     exit_price_position_manager = 0
                        #     reset_timer = 0
                        #
                        #     print('!!! OPERATIVITY RESET !!!')

                    # else: # BETA 26 OTT 2020
                    #     break

                elif result is not None:

                    pl_dollars = ((multiplier * punti) * size) - (commissions * size)

                    #Saving in the database
                    conn = sqlite3.connect('database.db')
                    cur = conn.cursor()
                    if f_pom is True:
                        cur.execute("UPDATE f_pom SET gain_loss= ? WHERE date= ?", (result, today))
                        conn.commit()
                    elif f_ser is True:
                        cur.execute("UPDATE f_ser SET gain_loss= ? WHERE date= ?", (result, today))
                        conn.commit()
                    conn.close()
                    if result.startswith("GAIN"):
                        conn = sqlite3.connect('database.db')
                        cur = conn.cursor()
                        if f_pom is True:
                            cur.execute("INSERT INTO f_pom_Profit VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (M1_calc.today, action, size, future, contratto, entry_time, exit_time, entry_price, exit_price, punti, pl_dollars, trade_duration))
                            conn.commit()
                        elif f_ser is True:
                            cur.execute("INSERT INTO f_ser_Profit VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (M1_calc.today, action, size, future, contratto, entry_time, exit_time, entry_price, exit_price, punti, pl_dollars, trade_duration))
                            conn.commit()
                        conn.close()
                        time.sleep(1)
                        result = None
                        executed = False
                    elif result.startswith("LOSS"):
                        conn = sqlite3.connect('database.db')
                        cur = conn.cursor()
                        if f_pom is True:
                            cur.execute("INSERT INTO f_pom_Loss VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (M1_calc.today, action, size, future, contratto, entry_time, exit_time, entry_price, exit_price, punti, pl_dollars, trade_duration))
                            conn.commit()
                        elif f_ser is True:
                            cur.execute("INSERT INTO f_ser_Loss VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (M1_calc.today, action, size, future, contratto, entry_time, exit_time, entry_price, exit_price, punti, pl_dollars, trade_duration))
                            conn.commit()
                        conn.close()
                        time.sleep(1)
                        result = None
                        executed = False
                        # if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        #     # op_reset()
                        #     order = -1
                        #     last_order = 0
                        #     go = False
                        #     done = False
                        #     op_done = False
                        #     tp = 0
                        #     sl = 0
                        #     entry_price = 0
                        #     trigger_price = -1
                        #     fm_check_done = False ### <---
                        #     # green_light = True ### <---
                        #     order_moved = False
                        #     exit_price_position_manager = 0
                        #     reset_timer = 0
                        #
                        #     print('!!! OPERATIVITY RESET !!!')

                #emergency close positions <<<----------
                elif executed is True and op_done is True and is_long is True and is_closed is False:
                    if automatic is True:
                        TestApp.close_long(self)
                        time.sleep(1)
                        # self.reqGlobalCancel()
                        self.cancelOrder(self.nextValidOrderId-1)
                        self.cancelOrder(self.nextValidOrderId-2)
                        self.cancelOrder(self.nextValidOrderId-3)
                        print("!!! Emergency close !!!")
                        is_long = False
                        is_short = False
                        executed = False
                        send_message(25169251, ('ES - Emergency close'))
                elif executed is True and op_done is True and is_short is True and is_closed is False:
                    if automatic is True:
                        TestApp.close_short(self)
                        time.sleep(1)
                        # self.reqGlobalCancel()
                        self.cancelOrder(self.nextValidOrderId-1)
                        self.cancelOrder(self.nextValidOrderId-2)
                        self.cancelOrder(self.nextValidOrderId-3)
                        print("!!! Emergency close !!!")
                        is_short = False
                        is_long = False
                        executed = False
                        send_message(25169251, ('ES - Emergency close'))
                elif order_placed is False and executed is False and op_done is False and news_range is False:
                    if op_reset_allowed is True and green_light is True and try_again_reset is True:
                        # op_reset()
                        order = -1
                        last_order = 0
                        go = False
                        done = False
                        op_done = False
                        tp = 0
                        sl = 0
                        entry_price = 0
                        trigger_price_delta = 2
                        trigger_price = -1
                        fm_check_done = False ### <---
                        # green_light = True ### <---
                        order_moved = False
                        exit_price_position_manager = 0
                        reset_timer = 0

                        # print('!!! OPERATIVITY RESET !!!')
                elif op_done is True and executed is False and news_range is False:
                    if reset_timer > 5:
                        if op_reset_allowed is True and green_light is True and try_again_reset is True:
                            # op_reset()
                            order = -1
                            last_order = 0
                            go = False
                            done = False
                            op_done = False
                            tp = 0
                            sl = 0
                            entry_price = 0
                            trigger_price_delta = 2
                            trigger_price = -1
                            fm_check_done = False ### <---
                            # green_light = True ### <---
                            order_moved = False
                            exit_price_position_manager = 0
                            reset_timer = 0

                            # print('!!! OPERATIVITY RESET !!!')
                    else:
                        reset_timer += 1
                else:
                    if news_range is False:
                        if op_reset_allowed is True and green_light is True and try_again_reset is True:
                            # op_reset()
                            order = -1
                            last_order = 0
                            go = False
                            done = False
                            op_done = False
                            tp = 0
                            sl = 0
                            entry_price = 0
                            trigger_price_delta = 2
                            trigger_price = -1
                            fm_check_done = False ### <---
                            # green_light = True ### <---
                            order_moved = False
                            exit_price_position_manager = 0
                            reset_timer = 0

                            # print('!!! OPERATIVITY RESET !!!')

            time.sleep(0.1)

    # def done_check(self):
    #     global up_trend
    #     global dwn_trend
    #     global order
    #     global start_time
    #     global end_time
    #     global current_price
    #     global executed
    #     global done
    #     global go
    #     global start_trading_time
    #     global end_trading_time
    #     global tp
    #     global sl
    #     global entry_price
    #     global is_long
    #     global is_short
    #     global automatic
    #     global order_placed
    #     global last_order
    #     time.sleep(3)
    #     while True:
    #         now = datetime.datetime.today()
    #         if done is False and go is True:
    #             if up_trend is True and order > -1 and order == last_order and start_time <= now.time() <= end_time:
    #                 if current_price > order or executed is True:
    #                     print(now.time())
    #                     print('''
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     1.1
    #                     ''')
    #                     done = True
    #                     go = False
    #                     if start_time < now.time() < start_trading_time:
    #                         print("In the first 5 minutes")
    #                         winsound.PlaySound("sounds/voice/Allison/five_minutes.wav", winsound.SND_ASYNC)
    #                     if start_trading_time <= now.time() <= end_trading_time:
    #                         #executed = True
    #                         winsound.PlaySound("sounds/voice/Allison/order_executed.wav", winsound.SND_ASYNC)
    #                         print("Entry price: ", entry_price)
    #                         print("TP: ", tp)
    #                         print("SL: ", sl)
    #                         print("Executed:", executed)
    #                         print("Current price:", current_price)
    #                         #position direction recognizer
    #                         #for close_position function
    #                         is_short = True
    #                 elif now.time() > end_time:
    #                     if order_placed is True and executed is False and automatic is True:
    #                         self.reqGlobalCancel()
    #                         order_placed = False
    #                         print("Orders canceled because the session is done")
    #                     #sound
    #                     #winsound.PlaySound("sounds/time_over.wav", winsound.SND_ASYNC)
    #                     winsound.PlaySound("sounds/voice/Allison/no_trade.wav", winsound.SND_ASYNC)
    #
    #                     print('''
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     1.2
    #                     ''')
    #                     print(now.time())
    #                     print("---> NO TRADE <---")
    #                     done = True
    #                     go = False
    #             if dwn_trend is True and order > -1 and start_time <= now.time() <= end_time:
    #                 if current_price < order or executed is True:
    #                     print(now.time())
    #                     print('''
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     2.1
    #                     ''')
    #                     done = True
    #                     go = False
    #                     if start_time < now.time() < start_trading_time:
    #                         print("In the first 5 minutes")
    #                         winsound.PlaySound("sounds/voice/Allison/five_minutes.wav", winsound.SND_ASYNC)
    #                     if start_trading_time <= now.time() <= end_trading_time:
    #                         #executed = True
    #                         winsound.PlaySound("sounds/voice/Allison/order_executed.wav", winsound.SND_ASYNC)
    #                         print("Entry price: ", entry_price)
    #                         print("TP: ", tp)
    #                         print("SL: ", sl)
    #                         print("Executed:", executed)
    #                         print("Current price:", current_price)
    #                         #position direction recognizer
    #                         #for close_position function
    #                         #is_long = True
    #                 elif now.time() > end_time:
    #                     if order_placed is True and executed is False and automatic is True:
    #                         self.reqGlobalCancel()
    #                         order_placed = False
    #                         print("Orders canceled because the session is done")
    #                     #sound
    #                     #winsound.PlaySound("sounds/time_over.wav", winsound.SND_ASYNC)
    #                     winsound.PlaySound("sounds/voice/Allison/no_trade.wav", winsound.SND_ASYNC)
    #
    #                     print('''
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     !!! DONE DONE DONE !!!
    #                     2.2
    #                     ''')
    #                     print(now.time())
    #                     print("---> NO TRADE <---")
    #                     done = True
    #                     go = False
    #         time.sleep(0.1)

    #get historical data ----------------------------- <<<
    def historicalData(self, reqId, bar):
        global daily_max
        global daily_min
        global range
        # print("HistoricalData. ", reqId, " Date:", bar.date, "Open:", bar.open,
        #   "High:", bar.high, "Low:", bar.low, "Close:", bar.close, "Volume:", bar.volume,
        #   "Count:", bar.barCount, "WAP:", bar.average)
        # print(bar.high)
        # print(bar.low)
        daily_max = bar.high
        daily_min = bar.low

        range = daily_max - daily_min
        # mm = mm_check(daily_max, daily_min) #pass last max and last min
        print("Range:", range)
        # print("MM: ", mm)

        ### STORE RANGE IN DB
        ###TO DO

    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        #print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
    #----------------------------------------------------------

    ########## GUI GUI GUI ##########
    # def switch_btn(self):
    #     def switch():
    #         global automatic
    #         global manual
    #         global was_automatic
    #
    #         if automatic is True:
    #             automatic = False
    #             manual = True
    #             was_automatic = False
    #             myButton.config(bg='#D7E4F3')
    #             status = 'OFF'
    #             myButton.config(text=f'ES AUTO MODE {status}')
    #             winsound.PlaySound("sounds/voice/Allison/manual_mode_btn.wav", winsound.SND_ASYNC)
    #         else:
    #             automatic = True
    #             manual = False
    #             was_automatic = True
    #             myButton.config(bg='#55FF33')
    #             status = 'ON'
    #             myButton.config(text=f'ES AUTO MODE {status}')
    #             winsound.PlaySound("sounds/voice/Allison/auto_mode_btn.wav", winsound.SND_ASYNC)
    #
    #         print('\n')
    #         print('Automatic:', automatic)
    #         print('Manual:', manual)
    #         print('Was automatic:', was_automatic)
    #         print('\n')
    #
    #     def disable_event():
    #         pass
    #
    #     root = Tk()
    #     root.title("ES")
    #     root.protocol("WM_DELETE_WINDOW", disable_event)
    #     root.resizable(False, False)
    #
    #     if automatic is True:
    #         status = 'ON'
    #     else:
    #         status = 'OFF'
    #
    #     myButton = Button(root, text=f'ES AUTO MODE {status}', padx=200, pady=50, command=switch, font=("Futura", 21))
    #
    #     if automatic is True:
    #         myButton.config(bg='#55FF33')
    #     else:
    #         myButton.config(bg='#D7E4F3')
    #
    #     myButton.pack()
    #
    #     root.mainloop()
    ########## GUI GUI GUI ##########

    def operativity(self):
        global contratto

        global times
        global start
        global end

        global quindici
        global ventuno
        global sedici
        global diciannove
        global sei

        global news_range
        global evening_comp
        global rest

        global news #to be reset every day
        global news_in_session #to be reset every day

        global time_delta_post_news
        global time_delta_pre_news

        global automatic
        global manual
        global was_automatic

        global first_move_notification
        global automatic_notification
        global manual_news_notification
        global manual_trigger_notification
        global manual_notification
        global notification
        global notif_start1
        global notif_end1
        global notif_start2
        global notif_end2

        global start_day
        global end_day

        global current_price
        global last_price

        global M1
        global order
        global last_order

        global count

        global up_trend
        global dwn_trend

        global last_price
        global move
        global rev_move
        global last_max
        global last_min

        global movements
        global max_move
        global average_move
        global move_in_range
        global last_avg_move_check

        global f_pom_start
        global f_pom_end
        global f_ser_start
        global f_ser_end

        global M1_ser_calc

        global start_time
        global end_time
        global start_trading_time
        global end_trading_time

        global start_op_time

        global done
        global go

        global daily_max
        global daily_min
        global p_close

        global pos
        global executed
        global result

        global size
        global pre_session_size
        global mm
        global session_mm
        global pl
        global gain
        global loss

        global tp
        global sl
        global entry_price
        global trigger_price_delta
        global trigger_price
        global order_placed

        global is_long
        global is_short
        global emergency_size
        global op_done

        global f_pom
        global f_ser

        global difference

        global fm_check_done

        global accuracy

        global green_light

        global entry_time
        global action

        global is_closed

        global pre_market_range

        global original_size

        global price_levels

        global gap_allowed

        global T_url

        global dynamic_size_increase
        global double_size_low_vol

        global reverse
        global default_reverse

        global order_moved

        global range_bars_ticks

        global default_dynamic_M1
        global dynamic_M1
        global M1_original
        # global movements_cleaned

        global position_manager
        global exit_price_position_manager
        global position_manager_ready

        global avg_volatility_10d

        global continuation_mode
        global STP_operativity
        global continuation_margin

        global five_min_done
        global five_min_reset
        global try_again_reset

        global op_reset_allowed

        global starting_up

        global volatility_expected

        global avg_pom
        global avg_ser
        global avg_tot

        global historical_volume
        global historical_volatility

        global first_hour_max
        global first_hour_min

        global volume_leak_avg

        global reverse_ob
        global rev_move_ob
        global last_max_ob
        global last_min_ob
        global move_ob
        global up_trend_ob
        global dwn_trend_ob
        global difference_ob
        global movements_ob

        global volume_profile_active
        global sell_levels
        global buy_levels
        global tp_multiplier
        # global movements_cleaned_ob

        global PAs_counter
        global counting_UP
        global counting_DOWN
        global PAs_to_rev_list
        global PAs_avg_to_rev

        global VP_on

        #############################
        # print("Last max: ", last_max)
        # print("Last min: ", last_min)
        #############################

        time.sleep(5)


        #round to nearest psycho area
        def myround(x, base=2.5):
            return base * round(x/base) #<<< closest one

        def round_up(x):
            return float(math.ceil(x / 2.5)) * 2.5

        def round_down(x):
            return float(math.floor(x / 2.5)) * 2.5

        def human_format(num):
            num = float('{:.3g}'.format(num))
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num /= 1000.0
            return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

        def volume_profile(df, price_pace=0.25, return_raw=False):
            global sell_levels
            global buy_levels

            cmin = min(df.Close)
            cmax = max(df.Close)
            cmin_int = int(cmin / price_pace) * price_pace  # int(0.9) = 0
            cmax_int = int(cmax / price_pace) * price_pace
            if cmax_int < cmax:
                cmax_int += price_pace
            cmax_int += price_pace  # right bracket is not included in arrange

            price_buckets = np.arange(cmin_int, cmax_int, price_pace)
            price_coors = pd.Series(price_buckets).rolling(2).mean().dropna()
            vol_bars = np.histogram(df.Close, bins=price_buckets, weights=df.Volume)[0]

            vol_prof = dict(zip(price_buckets, vol_bars))
            vol_prof_sorted = sorted([[k,v] for k,v in vol_prof.items()])

            # for k,v in vol_prof_sorted: #sorting data to print
            #     print(f'{k} : {v}')

            #getting avg volumes
            avgVol_list = list()
            for k,v in vol_prof.items():
                avgVol_list.append(v)
            avgVol = round(sum(avgVol_list)/float(len(avgVol_list)))
            # print('Avg Volume:', avgVol)

            #getting interesting price levels
            interest_levels = list()
            for k,v in vol_prof.items():
                if v > avgVol * 2:
                    interest_levels.append(k)
            # print('Levels:', interest_levels)

            #getting POC
            max_key = max(vol_prof, key=vol_prof.get)
            print('POC:', max_key)

            #locating price Levels
            sell_levels_raw = list()
            buy_levels_raw = list()
            for l in interest_levels:
                if l > current_price: #use daily max and min in the afternoon session
                    sell_levels_raw.append(myround(l))
                elif l < current_price: #use daily max and min in the afternoon session
                    buy_levels_raw.append(myround(l))

            sell_levels = set(sell_levels_raw)
            buy_levels = set(buy_levels_raw)

            print('SELL levels:', sell_levels)
            print('BUY levels:', buy_levels)

        ### ORDER ANALYSIS FUNCTION
        def order_analysis(up_trend, dwn_trend, order1):
            global size
            global pre_session_size
            global dynamic_size_increase
            global order
            global order_moved
            global last_max
            global last_min
            global last_order
            global continuation_margin
            global mm
            global session_mm
            global tp_multiplier

            size = pre_session_size

            def custom_round(x, base=25): #50 on NQ
                return int(base * round(float(x)/base))

            Mega_Area = custom_round(order1) #MA
            print('Mega Area:', Mega_Area)

            Mega_Area_distance = 5

            if up_trend is True:
                Mega_Area_distance = Mega_Area - order1
            elif dwn_trend is True:
                Mega_Area_distance = order1 - Mega_Area
            print('Mega Area distance:', Mega_Area_distance)

            if continuation_mode is False:
                if Mega_Area_distance == 2.5:
                    print('order too close to MA')
                    order = Mega_Area  # TIP: make it dynamic to move the order just in mid/high volatility
                    print('order moved to MA')
                    mm = 2
                    order_moved = True
                    # if size > 1:
                    #     size -= 1
                    #     print('Size lowered to', size)
                elif Mega_Area_distance == 0:
                    print('order on a Mega Area')
                    if accuracy > 50 and dynamic_size_increase is True:
                        size += 1
                        print('very high probability of success. Size increased to', size)
                    mm = 2
                else:
                    print('order on a neutral area')
                    if size != pre_session_size and pre_session_size > 0:
                        size = pre_session_size
                        print('size restored to pre-session size:', size)
                    mm = session_mm
            # else: ### DIFFERENCE WITH NQ TO BE TESTED!!! <<<------
            #     if up_trend is True:
            #         delta = order1 - last_min
            #         if delta >= 5:
            #             print('order too far away')
            #             order = (myround(last_min + M1)) + continuation_margin
            #             last_order = order
            #             print('order moved closer')
            #             order_moved = True
            #     elif dwn_trend is True:
            #         delta = last_max - order1
            #         if delta >= 5:
            #             print('order too far away')
            #             order = (myround(last_max - M1)) - continuation_margin
            #             last_order = order
            #             print('order moved closer')
            #             order_moved = True

        def range_check():
            global news_range
            # print('checking')
            for n in news_in_session:
                pre_news = n - time_delta_pre_news
                post_news = n + time_delta_post_news
                if pre_news.time() <= now.time() <= post_news.time():
                    news_range = True
                    return
                    #print(">>> In news range <<<")
                else:
                    news_range = False

        def nearest_quarter(x):
            return round(x*4)/4

        def Average(lst):
            return sum(lst) / len(lst)

        def op_reset():
            order = -1
            last_order = 0
            go = False
            done = False
            op_done = False
            tp = 0
            sl = 0
            entry_price = 0
            trigger_price_delta = 2
            trigger_price = -1
            fm_check_done = False ### <---
            order_moved = False
            exit_price_position_manager = 0

            print('!!! OPERATIVITY RESET !!!')

        PAs = list()
        first_PA = 0
        active_PA = 0
        reverse_PA = 0
        pa_last_min = 10000000000
        pa_last_max = -1
        pa_move = 0

        def isPA(number):
            return number % 2.5 == 0 #TRUE if is a PA

        def count_PAs(minmax,last): #### COUNTS HOW MANY PAs BETWEEN LAST MIN/MAX AND CURRENT PRICE
            count = 0
            round = 0
            if minmax == last:
                return count
            elif minmax < last:
                #uptrend
                while minmax <= last:
                    if minmax % 2.5 == 0:
                        count += 1
                        if minmax not in PAs:
                            PAs.append(minmax)
                    minmax += 0.25
                return count

            elif minmax > last:
                #downtrend
                while minmax >= last:
                    if minmax % 2.5 == 0:
                        count += 1
                        if minmax not in PAs:
                            PAs.append(minmax)
                    minmax -= 0.25
                return count

        while True:

            #time
            now = datetime.datetime.today()

            if evening_comp is True and f_ser is True:
                automatic = False
                manual = True

            #check if is in news range
            if len(news_in_session) > 0:
                range_check()

            if news_range is True and manual is True and manual_news_notification is True:
                # winsound.PlaySound("sounds/voice/Allison/news_coming.wav", winsound.SND_ASYNC)
                manual_news_notification = False
            if news_range is True and automatic is True:
                if order_placed is True and executed is False:
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    order_placed = False
                    is_long = False #
                    is_short = False #
                    print("Orders canceled because the news is coming")
                elif executed is True and is_long is True and is_short is False and is_closed is False:
                    TestApp.close_long(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    is_long = False
                    is_short = False
                    executed = False
                    op_done = True
                    send_message(25169251, ('ES - Emergency close'))
                elif executed is True and is_short is True and is_long is False and is_closed is False:
                    TestApp.close_short(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    is_short = False
                    is_long = False
                    executed = False
                    op_done = True
                    send_message(25169251, ('ES - Emergency close'))
                automatic = False
                manual = True
                manual_news_notification = False
                #notification
                if automatic_notification is True:
                    print("News is coming, Automatic mode deactivated")
                    print("Automatic:", automatic)
                    print("Manual:", manual)
                    automatic_notification = False
            elif news_range is False and automatic is False and was_automatic is True:
                if f_pom is True or (f_ser is True and evening_comp is False):
                    automatic = True
                    manual = False
                    #notification
                    if manual_notification is True:
                        print("Automatic mode activated")
                        print("Check Automatic:", automatic)
                        print("Check Manual:", manual)
                        manual_notification = False
                elif evening_comp is True and f_ser is True:
                    if manual_notification is True:
                        print("Keeping Automatic mode off. Evening session is compromised")
                        print("Check Automatic:", automatic)
                        print("Check Manual:", manual)
                        manual_notification = False
            #-------------------------------------

            if f_pom_start <= now.time() <= f_pom_end:
                f_pom = True
                f_ser = False

            elif f_ser_start <= now.time() <= f_ser_end:
                f_pom = False
                f_ser = True

            #Notification manager #AFTERNOON
            if (notif_start1 < now.time() < notif_end1 and notification is True) or ((start_time < now.time() < end_time) and starting_up is True):

                print('\n')
                print('PRE-MARKET INFO')
                print('-' * 50)

                contract = Contract()
                contract.secType = "FUT"
                contract.exchange = "GLOBEX"
                contract.currency = "USD"
                contract.localSymbol = contratto
                self.reqHistoricalData(2, contract, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 0, 1, False, [])

                time.sleep(3)

                # M1 recalibrating
                # if range <= 12:
                #     if M1 > 5:
                #         M1 = 5
                #         print('M1 recalibrated. New M1:', M1)


                print('-' * 50)
                print('\n')
                print('AVG MOVE afternoon:', avg_pom)
                # print('AVG MOVE evening:', avg_ser)
                # print('AVG MOVE tot:', avg_tot)
                print('\n')
                print('Historical average Volume:', human_format(historical_volume))
                print('Historical average Volatility:', historical_volatility, 'points')
                print('Average Volume last 10 days:', human_format(avg_volume_10d))
                print('Average Volatility last 10 days:', avg_volatility_10d, 'points')
                print('\n')
                print('-' * 50)

                # if range > historical_volatility: #previous > 25
                #     if M1 < 10:
                #         dynamic_M1 = False
                #         # M1 = 10
                #         # print('M1 recalibrated. New M1:', M1)
                #         M1_original = M1

                # if range < avg_volatility_10d:
                #     if continuation_mode is True:
                #         continuation_mode = False

                if range > (avg_volatility_10d * 1.20): #above 30 <---
                    #BETA
                    if STP_operativity is True:
                        continuation_mode = True
                        print('--- STP ORDERS ALLOWED ---')
                        volatility_expected = 'High'
                        # M1 = 3.75
                    else:
                        continuation_mode = False
                        # M1 = 10 ### activate to make it static
                        M1 = nearest_quarter(float(avg_pom) * 1.33333)
                        print('--- LMT ORDERS ALLOWED ---')
                        volatility_expected = 'High'
                    #BETA ^^^
                    if M1 < nearest_quarter(float(avg_pom)*1.33333):
                        M1 = nearest_quarter(float(avg_pom)*1.33333)
                        mm = 2
                        session_mm = mm
                    # # trigger_price_delta = 1
                    # pl = int(p_and_l(mm)) #profit and loss
                    # gain = "+" + str(pl*1.5)
                    # loss = "-" + str(pl)
                    # print("Potential gain: ", gain)
                    # print("Potential loss: ", loss)
                elif (avg_volatility_10d * 0.6) <= range <= (avg_volatility_10d * 1.20): #between 15 and 30 <---
                    #BETA
                    continuation_mode = False
                    print('--- LMT ORDERS ALLOWED ---')
                    volatility_expected = 'Medium'
                    # M1 = float(avg_pom)
                    #BETA ^^^
                    if (M1 > nearest_quarter(float(avg_pom)*1.33333)) or (M1 < nearest_quarter(float(avg_pom)*0.66667)):
                        M1 = float(avg_pom)
                        mm = 1.5
                        session_mm = mm
                    # # trigger_price_delta = 0.75
                    # pl = int(p_and_l(mm)) #profit and loss
                    # gain = "+" + str(pl*1.5)
                    # loss = "-" + str(pl)
                    # print("Potential gain: ", gain)
                    # print("Potential loss: ", loss)
                elif range < (avg_volatility_10d * 0.6): #below 15 <---
                    #BETA
                    continuation_mode = False
                    print('--- LMT ORDERS ALLOWED ---')
                    volatility_expected = 'Low'
                    # M1 = nearest_quarter(float(avg_pom) * 0.875) # 3.75 or 4
                    #BETA ^^^
                    if M1 > nearest_quarter(float(avg_pom)*0.66667):
                        M1 = nearest_quarter(float(avg_pom)*0.66667)
                        mm = 1
                        session_mm = mm
                    # # trigger_price_delta = 0.5
                    # pl = int(p_and_l(mm)) #profit and loss
                    # gain = "+" + str(pl*1.5)
                    # loss = "-" + str(pl)
                    # print("Potential gain: ", gain)
                    # print("Potential loss: ", loss)

                print('M1 recalibrated. New M1:', M1)
                print('MM recalibrated. New MM:', mm)
                print('Volatility expected:', volatility_expected)

                # Resizing
                if mm is 1:
                    if double_size_low_vol is True:
                        size *= 2
                        print('MM for low volatility, size increased')
                        print('Size: ', size)
                else:
                    print('MM regular, size regular')

                if accuracy > 50 and dynamic_size_increase is True:
                    size += 1
                    print('Higher success rate, size rised')
                    print('Old size:', original_size)
                    print('New size:', size)
                    pre_session_size = size
                elif accuracy < 50 and size > 1 and dynamic_size_increase is True:
                    size -=1
                    print('Lower success rate, size lowered')
                    print('Old size:', original_size)
                    print('New size:', size)
                    pre_session_size = size


                # security calibration <---
                calibrate_security()

                # if len(movements_cleaned) > 0:
                #     print('\n')
                #     print('Filtered Moves:', movements_cleaned)
                #     print('AVG move:', average_move)
                #     print('\n')

                if starting_up is False:
                    winsound.PlaySound("sounds/voice/Allison/afternoon_session_start.wav", winsound.SND_ASYNC)
                    expected_range = nearest_quarter(range*0.8) ### usually 1st hour move is 80% of premarket move
                    print('\n')
                    print('>>> Expected Range:', expected_range)
                    print('\n')

                print('-' * 50)
                if VP_on is True:
                    try:
                        #GETTING VOLUME PROFILE
                        sd = datetime.datetime.today() - datetime.timedelta(days=7)
                        ed = datetime.datetime.today()
                        df = yf.download(tickers='ES=F', start=sd, end=ed, interval="1m") #NQ=F for Nasdaq
                        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

                        volume_profile(df, price_pace=0.25, return_raw=False)
                    except:
                        print('!!! Failed retriving Volume Profile !!!')
                        volume_profile_active = False
                print('-' * 50)
                print('\n')

                notification = False
                # starting_up = False

            #EVENING
            elif (notif_start2 < now.time() < notif_end2 and notification is True) or ((start_time < now.time() < end_time) and starting_up is True):

                print('\n')
                print('PRE-SESSION INFO')
                print('-' * 50)

                contract = Contract()
                contract.secType = "FUT"
                contract.exchange = "GLOBEX"
                contract.currency = "USD"
                contract.localSymbol = contratto
                self.reqHistoricalData(2, contract, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 1, 1, False, [])

                time.sleep(3)

                # M1 recalibrating
                # if range <= 12:
                #     if M1 > 5:
                #         M1 = 5
                #         print('M1 recalibrated. New M1:', M1)



                print('-' * 50)
                print('\n')
                # print('AVG MOVE afternoon:', avg_pom)
                print('AVG MOVE evening:', avg_ser)
                # print('AVG MOVE tot:', avg_tot)
                print('\n')
                print('Historical average Volume:', human_format(historical_volume))
                print('Historical average Volatility:', historical_volatility, 'points')
                print('Average Volume last 10 days:', human_format(avg_volume_10d))
                print('Average Volatility last 10 days:', avg_volatility_10d, 'points')
                print('\n')
                print('-' * 50)

                # if range > historical_volatility:
                #     if M1 < 10:
                #         dynamic_M1 = False
                #         # M1 = 10
                #         # print('M1 recalibrated. New M1:', M1)
                #         M1_original = M1

                # if range < avg_volatility_10d:
                #     if continuation_mode is True:
                #         continuation_mode = False

                if range > (avg_volatility_10d * 1.20): #above 30 <---
                    #BETA
                    if STP_operativity is True:
                        continuation_mode = True
                        print('--- STP ORDERS ALLOWED ---')
                        volatility_expected = 'High'
                        # M1 = 3.75
                    else:
                        continuation_mode = False
                        # M1 = 10 ### activate to make it static
                        M1 = nearest_quarter(float(avg_ser) * 1.33333)
                        print('--- LMT ORDERS ALLOWED ---')
                        volatility_expected = 'High'
                    #BETA ^^^
                    if M1 < nearest_quarter(float(avg_ser)*1.33333):
                        M1 = nearest_quarter(float(avg_ser)*1.33333)
                        mm = 2
                        session_mm = mm
                    # mm = 2
                    # session_mm = mm
                    # # trigger_price_delta = 1
                    # pl = int(p_and_l(mm)) #profit and loss
                    # gain = "+" + str(pl*1.5)
                    # loss = "-" + str(pl)
                    # print("Potential gain: ", gain)
                    # print("Potential loss: ", loss)
                elif (avg_volatility_10d * 0.6) <= range <= (avg_volatility_10d * 1.20): #between 15 and 30 <---
                    #BETA
                    continuation_mode = False
                    print('--- LMT ORDERS ALLOWED ---')
                    volatility_expected = 'Medium'
                    # M1 = float(avg_ser) # 5 on normal conditions
                    #BETA ^^^
                    if (M1 > nearest_quarter(float(avg_ser)*1.33333)) or (M1 < nearest_quarter(float(avg_ser)*0.66667)):
                        M1 = float(avg_ser)
                        mm = 1.5
                        session_mm = mm
                    # mm = 1.5
                    # session_mm = mm
                    # # trigger_price_delta = 0.75
                    # pl = int(p_and_l(mm)) #profit and loss
                    # gain = "+" + str(pl*1.5)
                    # loss = "-" + str(pl)
                    # print("Potential gain: ", gain)
                    # print("Potential loss: ", loss)
                elif range < (avg_volatility_10d * 0.6): #below 15 <---
                    #BETA
                    continuation_mode = False
                    print('--- LMT ORDERS ALLOWED ---')
                    volatility_expected = 'Low'
                    # M1 = nearest_quarter(float(avg_ser) * 0.875) # 3.75 or 4
                    #BETA ^^^
                    if M1 > nearest_quarter(float(avg_ser)*0.66667):
                        M1 = nearest_quarter(float(avg_ser)*0.66667)
                        mm = 1
                        session_mm = mm
                    # mm = 1
                    # session_mm = mm
                    # # trigger_price_delta = 0.5
                    # pl = int(p_and_l(mm)) #profit and loss
                    # gain = "+" + str(pl*1.5)
                    # loss = "-" + str(pl)
                    # print("Potential gain: ", gain)
                    # print("Potential loss: ", loss)

                print('M1 recalibrated. New M1:', M1)
                print('MM recalibrated. New MM:', mm)
                print('Volatility expected:', volatility_expected)

                # Resizing
                if mm is 1:
                    if double_size_low_vol is True:
                        size *= 2
                        print('MM for low volatility, size increased')
                        print('Size: ', size)
                else:
                    print('MM regular, size regular')

                if accuracy > 50 and dynamic_size_increase is True:
                    size += 1
                    print('Higher success rate, size rised')
                    print('Old size:', original_size)
                    print('New size:', size)
                    pre_session_size = size
                elif accuracy < 50 and size > 1 and dynamic_size_increase is True:
                    size -=1
                    print('Lower success rate, size lowered')
                    print('Old size:', original_size)
                    print('New size:', size)
                    pre_session_size = size

                # security calibration <---
                calibrate_security()

                # if len(movements_cleaned) > 0:
                #     print('\n')
                #     print('Filtered Moves:', movements_cleaned)
                #     print('AVG move:', average_move)
                #     print('\n')

                if starting_up is False:
                    winsound.PlaySound("sounds/voice/Allison/evening_session_start.wav", winsound.SND_ASYNC)

                print('-' * 50)
                if VP_on is True:
                    try:
                        #GETTING VOLUME PROFILE
                        sd = datetime.datetime.today() - datetime.timedelta(days=7)
                        ed = datetime.datetime.today()
                        df = yf.download(tickers='ES=F', start=sd, end=ed, interval="1m") #NQ=F for Nasdaq
                        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

                        volume_profile(df, price_pace=0.25, return_raw=False)
                    except:
                        print('!!! Failed retriving Volume Profile !!!')
                        volume_profile_active = False
                print('-' * 50)
                print('\n')

                notification = False


            #Calculating new M1
            if datetime.time(diciannove, 25, 0) <= now.time() <= datetime.time(diciannove, 26, 0):
                if executed is True and is_long is True and is_short is False and automatic is True and is_closed is False:
                    TestApp.close_long(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    #executed = False
                    is_long = False
                    is_short = False
                    send_message(25169251, ('ES - Emergency close'))
                elif executed is True and is_short is True and is_long is False and automatic is True and is_closed is False:
                    TestApp.close_short(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    #executed = False
                    is_short = False
                    is_long = False
                    send_message(25169251, ('ES - Emergency close'))
                elif executed is False and is_long is False and is_short is False:
                    print("No open positions")


                M1_calc()

                pl = int(p_and_l(mm)) #profit and loss
                gain = "+" + str(pl*tp_multiplier)
                loss = "-" + str(pl)
                # print("Potential gain: ", gain)
                # print("Potential loss: ", loss)
                accuracy_calc()
                M1 = M1_calc.M1
                M1_original = M1
                order = -1
                last_order = 0
                movements = list()
                movements_ob = list()
                max_move = -1

                five_min_done = False
                five_min_reset = False

                continuation_mode = False
                if M1 >= 11 and STP_operativity is True:
                    continuation_mode = True
                    print('--- STP ORDERS ALLOWED ---')

                # average_move = 0
                tp = 0
                sl = 0
                entry_price = 0
                trigger_price_delta = 2
                trigger_price = -1
                go = False
                done = False
                op_done = False

                f_pom = False
                f_ser = True

                automatic_notification = True
                manual_news_notification = True
                manual_notification = True
                first_move_notification = True

                fm_check_done = False

                green_light = True

                dynamic_M1 = default_dynamic_M1

                exit_price_position_manager = 0
                position_manager_ready = False
                stp_moved = False

                sell_levels = None
                buy_levels = None

                if evening_comp is True:
                    automatic = False
                    manual = True
                    print("Evening session is compromised, automatic mode is been deactivated.")
                    print("Check Automatic:", automatic)
                    print("Check Manual:", manual)

                time.sleep(60)

            elif datetime.time(1, 5, 0) <= now.time() <= datetime.time(1, 6, 0):

                # #sleep mode
                # def sleeping(hours):
                #     for h in range(int(hours)):
                #         for m in range(60): #1h
                #             time.sleep(60) #1min
                # sleeping(10)


                time_shift_period_check()

                news = list()
                news_in_session = list()

                # setLogger()
                getEconomicCalendar("calendar.php?day={}".format(datetime.date.today().strftime("%b%d.%Y").lower()))

                if len(news) > 0:
                    for i in news:
                        news_time = i[0]
                        news_in_session.append(news_time)
                        news_event = i[1]
                        if "FOMC" in news_event:
                            print("FOMC, evening session is compromised")
                            evening_comp = True #

                        else:
                            evening_comp = False
                            # pre_news = i[0] - time_delta_pre_news
                            # post_news = i[0] + time_delta_post_news

                            print(news_time.date())
                            print('news time:', news_time.time())
                            print('news event:', news_event)
                            # print('pre news:', pre_news.time())
                            # print('post news:', post_news.time())
                        if "Bank Holiday" in i[1]:
                            print("Market closed today")
                            rest = True

                else:
                    print("No news today")

                M1_calc()

                pl = int(p_and_l(mm)) #profit and loss
                gain = "+" + str(pl*tp_multiplier)
                loss = "-" + str(pl)
                # print("Potential gain: ", gain)
                # print("Potential loss: ", loss)
                accuracy_calc()
                M1 = M1_calc.M1
                M1_original = M1
                order = -1
                last_order = 0
                movements = list()
                movements_ob = list()
                # movements_cleaned = list()
                # movements_cleaned_ob = list()
                max_move = -1
                average_move = 0

                five_min_done = False
                five_min_reset = False

                continuation_mode = False
                if M1 >= 11 and STP_operativity is True:
                    continuation_mode = True
                    print('--- STP ORDERS ALLOWED ---')

                tp = 0
                sl = 0
                entry_price = 0
                trigger_price_delta = 2
                trigger_price = -1
                go = False
                done = False
                op_done = False

                f_pom = True
                f_ser = False

                automatic_notification = True
                manual_news_notification = True
                manual_notification = True
                first_move_notification = True

                fm_check_done = False

                green_light = True

                dynamic_M1 = default_dynamic_M1

                exit_price_position_manager = 0
                position_manager_ready = False
                stp_moved = False

                sell_levels = None
                buy_levels = None

                p_close = 0


                if automatic is False and was_automatic is True:
                    automatic = True
                    manual = False
                    print("Automatic mode is been activated back.")
                    print("Check Automatic:", automatic)
                    print("Check Manual:", manual)


                time.sleep(60)

            if f_pom is True:
                start_time = datetime.time(quindici, 15, 0)
                end_time = datetime.time(sedici, 30, 0)
                start_trading_time = datetime.time(quindici, 35, 1)
                end_trading_time = datetime.time(sedici, 29, 0)
                start_op_time = datetime.time(quindici, 30, 0)
            elif f_ser is True:
                start_time = datetime.time(diciannove, 30, 0)
                end_time = datetime.time(ventuno, 45, 0)
                start_trading_time = datetime.time(diciannove, 45, 0)
                end_trading_time = datetime.time(ventuno, 44, 0)
                start_op_time = datetime.time(diciannove, 45, 0)

            if datetime.time(sedici, 31, 0) < now.time() < datetime.time(sedici, 32, 0):
                # winsound.PlaySound("sounds/voice/Allison/move_show.wav", winsound.SND_ASYNC)
                # print(now.time())
                # print("FASCIA POMERIDIANA, SESSION IS DONE")
                # print("Movements: ", movements)
                # print("Max movement: ", max_move)
                #
                # # save movements in the DB
                # todayDB = datetime.date.today()
                # conn = sqlite3.connect('database.db')
                # cur = conn.cursor()
                # for m in movements:
                #     cur.execute("INSERT INTO f_pom_movements VALUES (NULL, ?, ?, ?, ?)", (todayDB, m, range_bars_ticks, contratto))
                #     conn.commit()
                # conn.close()
                # print("Movements saved in the DB")
                #
                # # -------------------- ADJUSTING MAX MOVEMENT (MAM)
                # if len(movements) > 0:
                #     index = movements.index(max_move)
                #     #print("Max movement index: ", index)
                #     while movements[-1] != max_move and movements[-2] != max_move and movements[index+1] < mm: #original 2.50
                #         index = movements.index(max_move)
                #         if movements[index+1] < mm: #original 2.50
                #             max_move = max_move + (movements[index+2] - movements[index+1])
                #             del movements[index+1]
                #             del movements[index+1]
                #             movements[index] = max_move
                # else:
                #     if reverse == default_reverse:
                #         max_move = 5
                #     else:
                #         max_move = 7.5
                # print("Adjusted max: ", max_move)
                # conn = sqlite3.connect('database.db')
                # cur = conn.cursor()
                # if f_pom is True:
                #     cur.execute("UPDATE f_pom SET max_movement= ? WHERE date= ?", (max_move, today))
                #     conn.commit()
                # elif f_ser is True:
                #     cur.execute("UPDATE f_ser SET max_movement= ? WHERE date= ?", (max_move, today))
                #     conn.commit()
                # conn.close()
                #
                # notification = True
                # #observe = True
                #
                # print('Executed:', executed)
                # print('Is closed:', is_closed)
                #
                # if executed is True and is_closed is True:
                #     executed = False
                #     print('Executed:', executed)
                #     print('Is closed:', is_closed)
                #
                # if executed is True and is_long is True and is_short is False and automatic is True and is_closed is False:
                #     TestApp.close_long(self)
                #     time.sleep(1)
                #     # self.reqGlobalCancel()
                #     self.cancelOrder(self.nextValidOrderId-1)
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     print("Emergency close")
                #     executed = False
                #     is_long = False
                #     is_short = False
                #     send_message(25169251, ('ES - Emergency close'))
                #     # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                # elif executed is True and is_short is True and is_long is False and automatic is True and is_closed is False:
                #     TestApp.close_short(self)
                #     time.sleep(1)
                #     # self.reqGlobalCancel()
                #     self.cancelOrder(self.nextValidOrderId-1)
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     print("Emergency close")
                #     executed = False
                #     is_short = False
                #     is_long = False
                #     send_message(25169251, ('ES - Emergency close'))
                #     # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                # elif executed is False and is_long is False and is_short is False:
                #     print("No open positions")
                #     print('One last check')
                #     self.cancelOrder(self.nextValidOrderId-1) ####### this cause the order cancel attempt in the end
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     time.sleep(1)
                #     # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                #
                # # if executed is False and is_long is False and is_short is False:
                # #     print("No open positions")
                # #     self.cancelOrder(self.nextValidOrderId-1)
                # #     self.cancelOrder(self.nextValidOrderId-2)
                # #     self.cancelOrder(self.nextValidOrderId-3)
                # #     print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                #
                # size = original_size
                # pre_session_size = original_size
                # order_moved = False
                #
                # if len(movements_cleaned) > 0:
                #     print('\n')
                #     print('Filtered Moves:', movements_cleaned)
                #     # if len(times) > 0:
                #     #     print('Movement durations:', times)
                #     print('\n')
                #
                # first_hour_range = first_hour_max - first_hour_min
                # print('1st hour range:', first_hour_range)
                # print('\n')
                #
                # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                #
                # time.sleep(60)
                pass

            if datetime.time(ventuno, 46, 0) < now.time() < datetime.time(ventuno, 47, 0):
                # winsound.PlaySound("sounds/voice/Allison/move_show.wav", winsound.SND_ASYNC)
                # print(now.time())
                # print("FASCIA SERALE, SESSION IS DONE")
                # print("Movements: ", movements)
                # print("Max movement: ", max_move)
                #
                # # save movements in the DB
                # todayDB = datetime.date.today()
                # conn = sqlite3.connect('database.db')
                # cur = conn.cursor()
                # for m in movements:
                #     cur.execute("INSERT INTO f_ser_movements VALUES (NULL, ?, ?, ?, ?)", (todayDB, m, range_bars_ticks, contratto))
                #     conn.commit()
                # conn.close()
                # print("Movements saved in the DB")
                #
                # # -------------------- ADJUSTING MAX MOVEMENT (MAM)
                # if len(movements) > 0:
                #     index = movements.index(max_move)
                #     #print("Max movement index: ", index)
                #     while movements[-1] != max_move and movements[-2] != max_move and movements[index+1] < mm: #original 2.50
                #         index = movements.index(max_move)
                #         if movements[index+1] < mm: #original 2.50
                #             max_move = max_move + (movements[index+2] - movements[index+1])
                #             del movements[index+1]
                #             del movements[index+1]
                #             movements[index] = max_move
                # else:
                #     if reverse == default_reverse:
                #         max_move = 5
                #     else:
                #         max_move = 7.5
                # print("Adjusted max: ", max_move)
                # conn = sqlite3.connect('database.db')
                # cur = conn.cursor()
                # if f_pom is True:
                #     cur.execute("UPDATE f_pom SET max_movement= ? WHERE date= ?", (max_move, today))
                #     conn.commit()
                # elif f_ser is True:
                #     cur.execute("UPDATE f_ser SET max_movement= ? WHERE date= ?", (max_move, today))
                #     conn.commit()
                # conn.close()
                #
                # notification = True
                # #observe = True
                # print('Executed:', executed)
                # print('Is closed:', is_closed)
                #
                # if executed is True and is_closed is True:
                #     executed = False
                #     print('Executed:', executed)
                #     print('Is closed:', is_closed)
                #
                # if executed is True and is_long is True and is_short is False and automatic is True and is_closed is False:
                #     TestApp.close_long(self)
                #     time.sleep(1)
                #     # self.reqGlobalCancel()
                #     self.cancelOrder(self.nextValidOrderId-1)
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     print("Emergency close")
                #     executed = False
                #     is_long = False
                #     is_short = False
                #     send_message(25169251, ('ES - Emergency close'))
                #     # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                # elif executed is True and is_short is True and is_long is False and automatic is True and is_closed is False:
                #     TestApp.close_short(self)
                #     time.sleep(1)
                #     # self.reqGlobalCancel()
                #     self.cancelOrder(self.nextValidOrderId-1)
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     print("Emergency close")
                #     executed = False
                #     is_short = False
                #     is_long = False
                #     send_message(25169251, ('ES - Emergency close'))
                #     # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                # elif executed is False and is_long is False and is_short is False:
                #     print("No open positions")
                #     print('One last check')
                #     self.cancelOrder(self.nextValidOrderId-1)
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     time.sleep(1)
                #     # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                #
                # size = original_size
                # pre_session_size = original_size
                # order_moved = False
                #
                # if len(movements_cleaned) > 0:
                #     print('\n')
                #     print('Filtered Moves:', movements_cleaned)
                #     # if len(times) > 0:
                #     #     print('Movement durations:', times)
                #     print('\n')
                #
                # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                #
                # time.sleep(60)
                pass

            #recognize max and min 1st hours
            # if f_pom is True:
            #     if start_op_time <= now.time() < end_time:
            #         if current_price > first_hour_max:
            #             first_hour_max = current_price
            #         if current_price < first_hour_min:
            #             first_hour_min = current_price

            #recognize max and min DAILY
            # if current_price > daily_max:
            #     daily_max = current_price
            # if current_price < daily_min:
            #     daily_min = current_price

            ### FIVE MINUTE RESET
            if start_trading_time <= now.time() <= end_trading_time and five_min_done is True and five_min_reset is False: #and op_reset_allowed is True <-- add it to blend it to general reset option
                # op_reset()

                order = -1
                last_order = 0
                go = False
                done = False
                op_done = False
                tp = 0
                sl = 0
                entry_price = 0
                trigger_price_delta = 2
                trigger_price = -1
                fm_check_done = False ### <---
                # green_light = True ### <---
                order_moved = False
                exit_price_position_manager = 0

                print('!!! OPERATIVITY RESET 5min !!!')
                five_min_reset = True


            if count > 10:
            #if start_day <= now.time() <= end_day:
                # difference = current_price - last_price


                #recognize max and min
                if current_price > last_max:
                    last_max = current_price
                if current_price < last_min:
                    last_min = current_price


                #PAs counting
                if current_price > pa_last_max:
                    pa_last_max = current_price
                if current_price < pa_last_min:
                    pa_last_min = current_price

                #NEUTRAL TREND PAs
                if counting_UP is False and counting_DOWN is False:
                    if last_price != None:
                        pa_difference = current_price - last_price
                        if pa_move > 1:
                            counting_UP = True
                            counting_DOWN = False
                        if pa_move < -1:
                            counting_DOWN = True
                            counting_UP = False
                        pa_move += pa_difference

                if counting_UP is True:
                    #UP TREND PAs
                    PAs_counted_temp = count_PAs(pa_last_min, current_price)
                    if PAs_counted_temp > PAs_counter:
                        PAs_counter = PAs_counted_temp

                    if len(PAs) > 1:
                        active_PA = PAs[-1]
                        reverse_PA = PAs[-2]

                        if current_price <= reverse_PA:
                            pa_last_min = current_price
                            counting_UP = False
                            counting_DOWN = True
                            PAs = list()
                            if start_op_time <= now.time() <= end_time:
                                PAs_to_rev_list.append(PAs_counter) #THIS JUST DURING SESSION
                            PAs_counter = 0

                    else:
                        if current_price < pa_last_min:
                            pa_last_min = current_price
                            counting_UP = False
                            counting_DOWN = True
                            PAs = list()
                            if start_op_time <= now.time() <= end_time:
                                PAs_to_rev_list.append(PAs_counter) #THIS JUST DURING SESSION
                            PAs_counter = 0

                elif counting_DOWN is True:
                    #DOWN TREND PAs
                    PAs_counted_temp = count_PAs(pa_last_max, current_price)
                    if PAs_counted_temp > PAs_counter:
                        PAs_counter = PAs_counted_temp

                    if len(PAs) > 1:
                        active_PA = PAs[-1]
                        reverse_PA = PAs[-2]

                        if current_price >= reverse_PA:
                            pa_last_max = current_price
                            counting_UP = True
                            counting_DOWN = False
                            PAs = list()
                            if start_op_time <= now.time() <= end_time:
                                PAs_to_rev_list.append(PAs_counter) #THIS JUST DURING SESSION
                            PAs_counter = 0

                    else:
                        if current_price > pa_last_max:
                            pa_last_max = current_price
                            counting_UP = True
                            counting_DOWN = False
                            PAs = list()
                            if start_op_time <= now.time() <= end_time:
                                PAs_to_rev_list.append(PAs_counter) #THIS JUST DURING SESSION
                            PAs_counter = 0


                if len(PAs_to_rev_list) > 0:
                    PAs_avg_to_rev = round(Average(PAs_to_rev_list))




            #OBSERVE---------------------------------------------------------------
                # if observe is True:
                #     if up_trend is False and dwn_trend is False:
                #
                #         if move > 1:
                #             up_trend = True
                #             dwn_trend = False
                #         if move < -1:
                #             dwn_trend = True
                #             up_trend = False
                #         move += difference
                #     if up_trend is True:
                #         dwn_trend = False
                #         move = last_max - last_min
                #         rev_move = current_price - last_max
                #         if rev_move > -2:
                #             if current_price > last_max:
                #                 rev_move = 0
                #         if rev_move <= -2:
                #             last_min = current_price
                #             up_trend = False
                #             dwn_trend = True
                #             rev_move = 0
                #     if dwn_trend is True:
                #         up_trend = False
                #         move = last_max - last_min
                #         rev_move = current_price - last_min
                #         if rev_move < 2:
                #             if current_price < last_min:
                #                 rev_move = 0
                #         if rev_move >= 2:
                #             last_max = current_price
                #             dwn_trend = False
                #             up_trend = True
                #             rev_move = 0
            #----------------------------------------------------------------------

                #SECURITY SYSTEM ----------------------------- <<<<<<<<<< !!!!!!!!!
                # if start_op_time <= now.time() <= end_time:
                #     #observe = False
                #     if done is False and go is True and automatic is True:
                #         if difference > 1.75:
                #             done = True
                #             go = False
                #             print(now.time())
                #             print("Too much volatility. Security on")
                #             if order_placed is True and executed is False and automatic is True:
                #                 self.reqGlobalCancel()
                #                 order_placed = False
                #                 is_long = False #
                #                 is_short = False #
                #                 print("Orders canceled because there is too much volatility")
                #             winsound.PlaySound("sounds/voice/Allison/security.wav", winsound.SND_ASYNC)

    # NEUTRAL TREND ----------
                if up_trend is False and dwn_trend is False:

                    if last_price != None:
                        difference = current_price - last_price


                        if move > 1:
                            up_trend = True
                            dwn_trend = False
                        if move < -1:
                            dwn_trend = True
                            up_trend = False
                        move += difference
    #----------


    # UP TREND ----------
                if up_trend is True:
                    dwn_trend = False

                    #first movement analysis
                    if start_op_time <= now.time() < end_time and done is False:
                        if (len(movements) is 0 or five_min_reset is True or try_again_reset is True) and fm_check_done is False: ### old statement
                        # if fm_check_done is False:
                            # print('Check 1')
                            temp_move = current_price - last_min

                            # print('Check 2')

                            if continuation_mode is True and STP_operativity is True:
                                temp_order = (round_up(last_min + M1)) + continuation_margin
                            else:
                            ####### IF YOU CHANGE SOMETHING HERE, CHANGE EVEN INSIDE THE TREND
                                if 0 < M1 < 5:
                                    temp_order = round_up(last_min + M1)
                                elif M1 == 5:
                                    temp_order = round_up(last_min + M1)
                                elif 5 < M1 < 7.50:
                                    temp_order = round_up(last_min + M1)
                                elif M1 == 7.50:
                                    temp_order = round_up(last_min + M1)
                                elif 7.50 < M1 < 10:
                                    temp_order = round_up(last_min + M1)
                                elif M1 == 10:
                                    temp_order = round_up(last_min + M1)
                                elif M1 > 10:
                                    temp_order = round_up(last_min + M1)

                            # print('Check 3')

                            if temp_move >= M1 or current_price >= temp_order or temp_order in price_levels:
                                # print('Check 4')
                                go = False
                                done = True
                                fm_check_done = True
                                if first_move_notification is True and STP_operativity is False:
                                    print(now.time())
                                    print("First move > M1, or above the order, or order touched")
                                    print("First move: ", temp_move)
                                    first_move_notification = False
                                    # send_message(25169251, ('ES - First move > M1, or above the order, or order touched'))
                                if op_reset_allowed is True:
                                    fm_check_done = False
                                    done = False
                            elif temp_move < M1:
                                # print('Check 5')
                                go = True
                                fm_check_done = True
                                if try_again_reset is True:
                                    print('!!! OPERATIVITY RESET !!!')
                                    try_again_reset = False
                        elif len(movements) is not 0 and fm_check_done is False:
                            # print('Check 6')
                            go = True
                            fm_check_done = True
                            if try_again_reset is True:
                                print('!!! OPERATIVITY RESET !!!')
                                try_again_reset = False

                    #order and print handle
                    if now.time() > start_op_time and go is True:
                        # order = last_min + M1

                        # order = myround(last_min + M1) # to place the order to the closest psycho area <<<----------
                        # order = round_up(last_min + M1) # to place the order to the next psycho area <<<----------

                        # ADAPTIVE ORDERS ----------

                        # standard adjusting
                        # if 0 < M1 < 5:
                        #     order = myround(last_min + M1) # to the closest psycho area <<<----------
                        # elif 5 <= M1 < 7.50:
                        #     order = round_up(last_min + M1) # to the next psycho area <<<----------
                        # elif M1 >= 7.50:
                        #     order = round_up(last_min + M1) # to the next psycho area <<<----------

                        if continuation_mode is True and STP_operativity is True:
                            order = (round_up(last_min + M1)) + continuation_margin
                        else:
                            # advanced adjusting
                            if order_moved is False:
                                if 0 < M1 < 5:
                                    order = round_up(last_min + M1)
                                elif M1 == 5:
                                    order = round_up(last_min + M1)
                                elif 5 < M1 < 7.50:
                                    order = round_up(last_min + M1)
                                elif M1 == 7.50:
                                    order = round_up(last_min + M1)
                                elif 7.50 < M1 < 10:
                                    order = round_up(last_min + M1)
                                elif M1 == 10:
                                    order = round_up(last_min + M1)
                                elif M1 > 10:
                                    order = round_up(last_min + M1)


                    #Security system ----------
                    # if start_time <= now.time() <= end_time:
                    #     if difference > 1:
                    #         done = True
                    #         go = False
                    #         print(now.time())
                    #         print("Too much volatility. Security on")
                    #         if order_placed is True and executed is False and automatic is True:
                    #             self.reqGlobalCancel()
                    #             order_placed = False
                    #             is_long = False #
                    #             is_short = False #
                    #         winsound.PlaySound("sounds/voice/Allison/security.wav", winsound.SND_ASYNC)


                    if done is False and go is True:
                        if current_price < order and executed is False and start_op_time <= now.time() <= end_time:
                            if order != last_order and order > -1:

                                print("_" * 50)
                                print(now.time())
                                print("ES >>>>>>>>>>")

                                print('\n')

                                order_analysis(up_trend, dwn_trend, order)

                                #sound
                                #winsound.PlaySound("sounds/reverse.wav", winsound.SND_ASYNC)
                                if continuation_mode is True and STP_operativity is True:
                                    entry_price = float(order)
                                    tp = (float(entry_price)) + (mm*tp_multiplier)
                                    print('TP:', tp)
                                    sl = (float(entry_price)) - mm
                                    print('SL:', sl)
                                    trigger_price = entry_price - trigger_price_delta
                                    print('Trigger price:', trigger_price)

                                    exit_price_position_manager = (float(entry_price)) + 0.25
                                    print('Exit position for manager:', exit_price_position_manager)
                                else:
                                    entry_price = float(order)
                                    tp = (float(entry_price)) - (mm*tp_multiplier)
                                    print('TP:', tp)
                                    sl = (float(entry_price)) + mm
                                    print('SL:', sl)
                                    trigger_price = entry_price - trigger_price_delta
                                    print('Trigger price:', trigger_price)

                                    exit_price_position_manager = (float(entry_price)) - 0.25
                                    print('Exit position for manager:', exit_price_position_manager)



                                #Get historical data for MM -------------------------------------------- COMING SOON >>>>>>>>>>
                                # contract = Contract()
                                # contract.secType = "FUT"
                                # contract.exchange = "GLOBEX"
                                # contract.currency = "USD"
                                # contract.localSymbol = contratto

                                # self.reqHistoricalData(2, contract, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 0, 1, False, [])

                                # print("^^^^^^")
                                # print("Start time: ", start_time)
                                # print("End time: ", end_time)
                                # print("End Trading Time: ", end_trading_time)
                                # print("^^^^^^")
                                print('\n')
                                # if reverse == default_reverse:
                                #     print('Virtual Range Bars: 5 ticks')
                                # else:
                                #     print('Virtual Range Bars: 10 ticks')
                                print("M1: ", M1_original)
                                ###BETA
                                try:
                                    print('AVG move:', average_move)
                                    print('Dynamic M1:', M1)
                                except:
                                    print('error in Dynmic M1 calc')
                                ###BETA
                                print("--- UP ---")
                                print("Last min: ", last_min)
                                if continuation_mode is True and STP_operativity is True:
                                    print("------>>> BUY at: ", order, "<<<------")
                                else:
                                    print("------>>> SELL at: ", order, "<<<------")
                                print("Size: ", size)
                                print('Volatility expected:', volatility_expected)
                                print("MM: ", mm)

                                print('\n')
                                print('PAs took to reverse so far:', PAs_to_rev_list)
                                print(f'It reverses after {PAs_avg_to_rev} PAs, on average')
                                print('Last PA min:', pa_last_min)

                                # print('\n')
                                # print('||||||||||')
                                # print('News in session:', news_in_session)
                                # print('News range:', news_range)
                                # if news_range is True:
                                #     print('IN NEWS RANGE')
                                # else:
                                #     print('NOT IN NEWS RANGE')
                                # print('||||||||||')

                                print('\n')
                                print("Automatic: ", automatic)
                                print("Gain probability: ", accuracy, "%")

                                if len(times) > 0:
                                    print('\n')
                                    try:
                                        print("Last move time: ", strftime("%H:%M:%S",gmtime(times[-1])))
                                    except:
                                        print('!!! Error converting last move time into human format !!!')
                                        print("Last move time: ", times[-1])
                                    try:
                                        print("AVG moves time: ", strftime("%H:%M:%S",gmtime(Average(times))))
                                    except:
                                        print('!!! Error converting average move time into human format !!!')
                                        print("AVG moves time: ", Average(times))
                                print("_" * 50)

                                last_order = order
                            if start_trading_time <= now.time() <= end_trading_time:
                                if trigger_price <= current_price < order and trigger_price > -1:

                                    current_time = time.time()
                                    partial_time = current_time - start

                                    if manual is True and green_light is True and manual_trigger_notification is True and news_range is False:
                                        # winsound.PlaySound("sounds/voice/Allison/trigger_sell.wav", winsound.SND_ASYNC)
                                        manual_trigger_notification = False
                                    if order_placed is False and automatic is True and green_light is True:
                                        if continuation_mode is True and STP_operativity is True:
                                            if current_price > (p_close + 5):
                                                if len(times) > 0:
                                                    if partial_time > Average(times): ### BETA 26 OTT 2020
                                                        TestApp.BUY_STP(self)
                                                        order_placed = True
                                                        print(now.time())
                                                        print("Order Placed")
                                        else:
                                            # if (volatility_expected == 'Medium' or volatility_expected == 'High') and current_price < (p_close - 5): ### BETA 26 OTT 2020 ### CONSIDERING TO USE TIME FOR THIS TOO!!!
                                            if (volatility_expected == 'Medium' or volatility_expected == 'High'):
                                                if len(times) > 0:
                                                    if partial_time < Average(times):
                                                        if volume_profile_active is True and VP_on is True:
                                                            if order in sell_levels:
                                                                if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                    TestApp.SELL(self)
                                                                    order_placed = True
                                                                    print(now.time())
                                                                    print("Order Placed")
                                                        else:
                                                            if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                TestApp.SELL(self)
                                                                order_placed = True
                                                                print(now.time())
                                                                print("Order Placed")
                                            elif volatility_expected == 'Low':
                                                if len(times) > 0:
                                                    if partial_time < Average(times):
                                                        if volume_profile_active is True and VP_on is True:
                                                            if order in sell_levels:
                                                                if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                    TestApp.SELL(self)
                                                                    order_placed = True
                                                                    print(now.time())
                                                                    print("Order Placed")
                                                        else:
                                                            if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                TestApp.SELL(self)
                                                                order_placed = True
                                                                print(now.time())
                                                                print("Order Placed")
                        elif (current_price > order or executed is True) and start_time <= now.time() <= end_time and order > -1:
                            print(now.time())
                            print('''
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            1.1
                            ''')
                            done = True
                            go = False
                            if start_time < now.time() < start_trading_time:
                                print("In the first 5 minutes")
                                five_min_done = True
                                if STP_operativity is False:
                                    # winsound.PlaySound("sounds/voice/Allison/five_minutes.wav", winsound.SND_ASYNC)
                                    # send_message(25169251, ('ES - Triggered in the first 5 minutes'))
                                    print('...')
                            if start_trading_time <= now.time() <= end_trading_time and news_range is False:
                                #executed = True
                                if order_placed is True:
                                    winsound.PlaySound("sounds/voice/Allison/order_executed.wav", winsound.SND_ASYNC)
                                entry_time = now

                                if continuation_mode is True and STP_operativity is True:
                                    action = 'BOT'
                                else:
                                    action = 'SLD'

                                print("Entry price: ", entry_price)
                                print("TP: ", tp)
                                print("SL: ", sl)
                                print("Executed:", executed)
                                print("Current price:", current_price)

                                if order_placed is False: #TO ALLOW JUST ONE OPERATION
                                    try_again_reset = True

                                if order_placed is True:
                                    send_message(25169251, ('ES - Order executed'))
                                #position direction recognizer
                                #for close_position function
                                # is_short = True
                        elif now.time() > end_time:
                            if order_placed is True and executed is False and automatic is True:
                                # self.reqGlobalCancel()
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                order_placed = False
                                print(now.time())
                                print("Orders canceled because the session is done")
                            #sound
                            #winsound.PlaySound("sounds/time_over.wav", winsound.SND_ASYNC)
                            winsound.PlaySound("sounds/voice/Allison/no_trade.wav", winsound.SND_ASYNC)

                            print('''
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            1.2
                            ''')
                            print(now.time())
                            print("---> NO TRADE <---")
                            done = True
                            go = False
                            send_message(25169251, ('ES - No trade'))
                    # elif done is True and go is False:
                    #     #trade logic
                    #     if executed is True:
                    #         if current_price < tp:
                    #             result = "GAIN " + gain
                    #             winsound.PlaySound("sounds/voice/Allison/gain.wav", winsound.SND_ASYNC)
                    #             print(now.time())
                    #             ###########################################
                    #             print("Take Profit Price: ", tp)
                    #             print("Stop Loss Price: ", sl)
                    #             print("Current Price: ", current_price)
                    #             print("Boolean Check - price lower than TP: ", current_price < tp)
                    #             ###########################################
                    #             print("Operation: ", result)
                    #             executed = False
                    #             is_long = False #
                    #             is_short = False #
                    #         elif current_price >= sl:
                    #             result = "LOSS " + loss
                    #             winsound.PlaySound("sounds/voice/Allison/loss.wav", winsound.SND_ASYNC)
                    #             print(now.time())
                    #             ###########################################
                    #             print("Take Profit Price: ", tp)
                    #             print("Stop Loss Price: ", sl)
                    #             print("Current Price: ", current_price)
                    #             ###########################################
                    #             print("Operation: ", result)
                    #             executed = False #
                    #             is_long = False #
                    #             is_short = False
                    #     if result is not None:
                    #         #Saving in the database
                    #         conn = sqlite3.connect('database.db')
                    #         cur = conn.cursor()
                    #         if f_pom is True:
                    #             cur.execute("UPDATE f_pom SET gain_loss= ? WHERE date= ?", (result, today))
                    #             conn.commit()
                    #         elif f_ser is True:
                    #             cur.execute("UPDATE f_ser SET gain_loss= ? WHERE date= ?", (result, today))
                    #             conn.commit()
                    #         conn.close()
                    #         if result.startswith("GAIN"):
                    #             conn = sqlite3.connect('database.db')
                    #             cur = conn.cursor()
                    #             if f_pom is True:
                    #                 cur.execute("INSERT INTO f_pom_Profit VALUES (NULL, ?, ?)", (M1_calc.today, gain))
                    #                 conn.commit()
                    #             elif f_ser is True:
                    #                 cur.execute("INSERT INTO f_ser_Profit VALUES (NULL, ?, ?)", (M1_calc.today, gain))
                    #                 conn.commit()
                    #             conn.close()
                    #             result = None
                    #             executed = False
                    #         elif result.startswith("LOSS"):
                    #             conn = sqlite3.connect('database.db')
                    #             cur = conn.cursor()
                    #             if f_pom is True:
                    #                 cur.execute("INSERT INTO f_pom_Loss VALUES (NULL, ?, ?)", (M1_calc.today, loss))
                    #                 conn.commit()
                    #             elif f_ser is True:
                    #                 cur.execute("INSERT INTO f_ser_Loss VALUES (NULL, ?, ?)", (M1_calc.today, loss))
                    #                 conn.commit()
                    #             conn.close()
                    #             result = None
                    #             executed = False


                    #move recognizer
                    move = last_max - last_min
                    # if len(movements_cleaned) > 0:
                    #     average_move = nearest_quarter(Average(movements_cleaned))
                    #     if dynamic_M1 is True:
                    #         M1 = nearest_quarter(Average([M1_original, average_move]))


                        # if move <= average_move:
                        #     move_in_range = True
                        #     if last_avg_move_check != move_in_range:
                        #         # print('Move in avg range')
                        #         last_avg_move_check = move_in_range
                        # else:
                        #     move_in_range = False
                        #     if last_avg_move_check != move_in_range:
                        #         if start_time <= now.time() <= end_time:
                        #             print('\n')
                        #             print(now.time())
                        #             print('Avg move:', average_move)
                        #             print('!!! Move out of avg range !!!')
                        #         last_avg_move_check = move_in_range

                    rev_move = current_price - last_max

                    #### MOVE DURATION CHECK
                    if len(times) > 0:
                        if done is False and go is True:
                            end_temp = time.time()
                            duration_check = end_temp - start
                            if duration_check > Average(times) and order_placed is True and executed is False:
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                self.cancelOrder(self.nextValidOrderId-4)
                                self.cancelOrder(self.nextValidOrderId-5)
                                self.cancelOrder(self.nextValidOrderId-6)
                                order_placed = False
                                print(now.time())
                                print("Orders canceled because this movement is taking too long")
                                print("AVG moves time: ", strftime("%H:%M:%S",gmtime(Average(times))))
                                print("Current move time: ", strftime("%H:%M:%S",gmtime(duration_check)))

                    if rev_move > -reverse:
                        if current_price > last_max:

                            rev_move = 0

                        if len(movements) is 0 and current_price not in price_levels:
                            price_levels.append(current_price)

                    if rev_move <= -reverse:
                        end = time.time()
                        final_time = end - start
                        # times.append(final_time)
                        #grabbing movements in the trading timeframe
                        # if move > 3: #previously 5
                        #     movements_cleaned.append(move)

                        if start_time <= now.time() <= end_time:
                            if now.time() > start_op_time:
                                times.append(final_time)
                                movements.append(move)
                        if order_placed is True and executed is False:
                            if done is False and automatic is True:
                                # self.reqGlobalCancel()
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                self.cancelOrder(self.nextValidOrderId-4)
                                self.cancelOrder(self.nextValidOrderId-5)
                                self.cancelOrder(self.nextValidOrderId-6)
                                order_placed = False
                                print(now.time())
                                print("Orders canceled because reverse")

                        last_min = current_price

                        # if len(movements_cleaned) > 0:
                        #     average_move = nearest_quarter(Average(movements_cleaned))
                        #     if dynamic_M1 is True:
                        #         M1 = nearest_quarter(Average([M1_original, average_move]))
                        if len(movements) > 0:
                            average_move = nearest_quarter(Average(movements))
                            ###ADJUST MM IN RELATION TO AVG MOVE
                            ##TO DO
                            if dynamic_M1 is True:
                                M1 = nearest_quarter(Average([M1_original, average_move]))


                        up_trend = False
                        dwn_trend = True
                        manual_trigger_notification = True #could cause a repeated notification around order entry
                        rev_move = 0

                        order_moved = False

                        price_levels = list()
                        start = time.time()
    #----------


    # DOWN TREND ----------
                if dwn_trend is True:
                    up_trend = False

                    #first movement analysis
                    if start_op_time <= now.time() < end_time and done is False:
                        if (len(movements) is 0 or five_min_reset is True or try_again_reset is True) and fm_check_done is False: ### old version
                        # if fm_check_done is False:
                            # print('Check 1.1')
                            temp_move = last_max - current_price

                            # print('Check 2.1')

                            if continuation_mode is True and STP_operativity is True:
                                temp_order = (round_down(last_max - M1)) - continuation_margin
                            else:
                                ####### IF YOU CHANGE SOMETHING HERE, CHANGE EVEN INSIDE THE TREND
                                if 0 < M1 < 5:
                                    temp_order = round_down(last_max - M1)
                                elif M1 == 5:
                                    temp_order = round_down(last_max - M1)
                                elif 5 < M1 < 7.50:
                                    temp_order = round_down(last_max - M1)
                                elif M1 == 7.50:
                                    temp_order = round_down(last_max - M1)
                                elif 7.50 < M1 < 10:
                                    temp_order = round_down(last_max - M1)
                                elif M1 == 10:
                                    temp_order = round_down(last_max - M1)
                                elif M1 > 10:
                                    temp_order = round_down(last_max - M1)


                            # print('Check 3.1')


                            if temp_move >= M1 or current_price <= temp_order or temp_order in price_levels:
                                # print('Check 4.1')
                                go = False
                                done = True
                                fm_check_done = True
                                if first_move_notification is True and STP_operativity is False:
                                    print(now.time())
                                    print("First move > M1, or below the order, or order touched")
                                    print("First move: ", temp_move)
                                    first_move_notification = False
                                    # send_message(25169251, ('ES - First move > M1, or below the order, or order touched'))
                                if op_reset_allowed is True:
                                    fm_check_done = False
                                    done = False
                            elif temp_move < M1:
                                # print('Check 5.1')
                                go = True
                                fm_check_done = True
                                if try_again_reset is True:
                                    print('!!! OPERATIVITY RESET !!!')
                                    try_again_reset = False
                        elif len(movements) is not 0 and fm_check_done is False:
                            # print('Check 6.1')
                            go = True
                            fm_check_done = True
                            if try_again_reset is True:
                                print('!!! OPERATIVITY RESET !!!')
                                try_again_reset = False

                    #order and print handle
                    if now.time() > start_op_time and go is True:
                        # order = last_max - M1

                        # order = myround(last_max - M1) # to place the order to the closest psycho area <<<----------
                        # order = round_down(last_max - M1) # to place the order to the next psycho area <<<----------

                        # ADAPTIVE ORDERS ----------

                        # standard adjusting
                        # if 0 < M1 < 5:
                        #     order = myround(last_max - M1) # to the closest psycho area <<<----------
                        # elif 5 <= M1 < 7.50:
                        #     order = round_down(last_max - M1) # to the next psycho area <<<----------
                        # elif M1 >= 7.50:
                        #     order = round_down(last_max - M1) # to the next psycho area <<<----------


                        if continuation_mode is True and STP_operativity is True:
                            order = (round_down(last_max - M1)) - continuation_margin
                        else:
                            # advanced adjusting
                            if order_moved is False:
                                if 0 < M1 < 5:
                                    order = round_down(last_max - M1)
                                elif M1 == 5:
                                    order = round_down(last_max - M1)
                                elif 5 < M1 < 7.50:
                                    order = round_down(last_max - M1)
                                elif M1 == 7.50:
                                    order = round_down(last_max - M1)
                                elif 7.50 < M1 < 10:
                                    order = round_down(last_max - M1)
                                elif M1 == 10:
                                    order = round_down(last_max - M1)
                                elif M1 > 10:
                                    order = round_down(last_max - M1)


                    #Security system ----------
                    # if start_time <= now.time() <= end_time:
                    #     if difference > 1:
                    #         done = True
                    #         go = False
                    #         print(now.time())
                    #         print("Too much volatility. Security on")
                    #         if order_placed is True and executed is False and automatic is True:
                    #             self.reqGlobalCancel()
                    #             order_placed = False
                    #             is_long = False #
                    #             is_short = False #
                    #         winsound.PlaySound("sounds/voice/Allison/security.wav", winsound.SND_ASYNC)


                    if done is False and go is True:
                        if current_price > order and executed is False and start_op_time <= now.time() <= end_time:
                            if order != last_order and order > -1:

                                print("_" * 50)
                                print(now.time())
                                print("ES >>>>>>>>>>")

                                print('\n')

                                order_analysis(up_trend, dwn_trend, order)

                                #sound
                                #winsound.PlaySound("sounds/reverse.wav", winsound.SND_ASYNC)

                                if continuation_mode is True and STP_operativity is True:
                                    entry_price = float(order)
                                    tp = (float(entry_price)) - (mm*tp_multiplier)
                                    print('TP:', tp)
                                    sl = (float(entry_price)) + mm
                                    print('SL:', sl)
                                    trigger_price = entry_price + trigger_price_delta
                                    print('Trigger price:', trigger_price)

                                    exit_price_position_manager = (float(entry_price)) - 0.25
                                    print('Exit position for manager:', exit_price_position_manager)
                                else:
                                    entry_price = float(order)
                                    tp = (float(entry_price)) + (mm*tp_multiplier)
                                    print('TP:', tp)
                                    sl = (float(entry_price)) - mm
                                    print('SL:', sl)
                                    trigger_price = entry_price + trigger_price_delta
                                    print('Trigger price:', trigger_price)

                                    exit_price_position_manager = (float(entry_price)) + 0.25
                                    print('Exit position for manager:', exit_price_position_manager)



                                #Get historical data for MM -------------------------------------------- COMING SOON >>>>>>>>>>
                                # contract = Contract()
                                # contract.secType = "FUT"
                                # contract.exchange = "GLOBEX"
                                # contract.currency = "USD"
                                # contract.localSymbol = contratto

                                # self.reqHistoricalData(3, contract, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"), "1 D", "1 day", "TRADES", 0, 1, False, [])

                                # print("^^^^^^")
                                # print("Start time: ", start_time)
                                # print("End time: ", end_time)
                                # print("End Trading Time: ", end_trading_time)
                                # print("^^^^^^")
                                print('\n')
                                # if reverse == default_reverse:
                                #     print('Virtual Range Bars: 5 ticks')
                                # else:
                                #     print('Virtual Range Bars: 10 ticks')
                                print("M1: ", M1_original)
                                ###BETA
                                try:
                                    print('AVG move:', average_move)
                                    print('Dynamic M1:', M1)
                                except:
                                    print('error in Dynmic M1 calc')
                                ###BETA
                                print("--- DOWN ---")
                                print("Last max: ", last_max)
                                if continuation_mode is True and STP_operativity is True:
                                    print("------>>> SELL at: ", order, "<<<------")
                                else:
                                    print("------>>> BUY at: ", order, "<<<------")
                                print("Size: ", size)
                                print('Volatility expected:', volatility_expected)
                                print("MM: ", mm)

                                print('\n')
                                print('PAs took to reverse so far:', PAs_to_rev_list)
                                print(f'It reverses after {PAs_avg_to_rev} PAs, on average')
                                print('Last PA max:', pa_last_max)

                                # print('\n')
                                # print('||||||||||')
                                # print('News in session:', news_in_session)
                                # print('News range:', news_range)
                                # if news_range is True:
                                #     print('IN NEWS RANGE')
                                # else:
                                #     print('NOT IN NEWS RANGE')
                                # print('||||||||||')

                                print('\n')
                                print("Automatic: ", automatic)
                                print("Gain probability: ", accuracy, "%")

                                if len(times) > 0:
                                    print('\n')
                                    try:
                                        print("Last move time: ", strftime("%H:%M:%S",gmtime(times[-1])))
                                    except:
                                        print('!!! Error converting last move time into human format !!!')
                                        print("Last move time: ", times[-1])
                                    try:
                                        print("AVG moves time: ", strftime("%H:%M:%S",gmtime(Average(times))))
                                    except:
                                        print('!!! Error converting average move time into human format !!!')
                                        print("AVG moves time: ", Average(times))
                                print("_" * 50)

                                last_order = order
                            if start_trading_time <= now.time() <= end_trading_time:
                                if order < current_price <= trigger_price and trigger_price > -1:

                                    current_time = time.time()
                                    partial_time = current_time - start

                                    if manual is True and green_light is True and manual_trigger_notification is True and news_range is False:
                                        # winsound.PlaySound("sounds/voice/Allison/trigger_buy.wav", winsound.SND_ASYNC)
                                        manual_trigger_notification = False
                                    if order_placed is False and automatic is True and green_light is True:
                                        if continuation_mode is True and STP_operativity is True:
                                            if current_price < (p_close - 5):
                                                if len(times) > 0:
                                                    if partial_time > Average(times): ### BETA 26 OTT 2020
                                                        TestApp.SELL_STP(self)
                                                        order_placed = True
                                                        print(now.time())
                                                        print("Order Placed")
                                        else:
                                            # if (volatility_expected == 'Medium' or volatility_expected == 'High') and current_price > (p_close + 5): ### BETA 26 OTT 2020 ### CONSIDERING TO USE TIME FOR THIS TOO!!!
                                            if (volatility_expected == 'Medium' or volatility_expected == 'High'):
                                                if len(times) > 0:
                                                    if partial_time < Average(times):
                                                        if volume_profile_active is True and VP_on is True:
                                                            if order in buy_levels:
                                                                if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                    TestApp.BUY(self)
                                                                    order_placed = True
                                                                    print(now.time())
                                                                    print("Order Placed")
                                                        else:
                                                            if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                TestApp.BUY(self)
                                                                order_placed = True
                                                                print(now.time())
                                                                print("Order Placed")
                                            elif volatility_expected == 'Low':
                                                if len(times) > 0:
                                                    if partial_time < Average(times):
                                                        if volume_profile_active is True and VP_on is True:
                                                            if order in buy_levels:
                                                                if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                    TestApp.BUY(self)
                                                                    order_placed = True
                                                                    print(now.time())
                                                                    print("Order Placed")
                                                        else:
                                                            if (len(PAs_to_rev_list) > 0) and (PAs_counter >= (PAs_avg_to_rev-1)):
                                                                TestApp.BUY(self)
                                                                order_placed = True
                                                                print(now.time())
                                                                print("Order Placed")
                        elif (current_price < order or executed is True) and start_time <= now.time() <= end_time and order > -1:
                            print(now.time())
                            print('''
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            2.1
                            ''')
                            done = True
                            go = False
                            if start_time < now.time() < start_trading_time:
                                print("In the first 5 minutes")
                                five_min_done = True
                                if STP_operativity is False:
                                    # winsound.PlaySound("sounds/voice/Allison/five_minutes.wav", winsound.SND_ASYNC)
                                    # send_message(25169251, ('ES - Triggered in the first 5 minutes'))
                                    print('...')
                            if start_trading_time <= now.time() <= end_trading_time and news_range is False:
                                #executed = True
                                if order_placed is True:
                                    winsound.PlaySound("sounds/voice/Allison/order_executed.wav", winsound.SND_ASYNC)
                                entry_time = now

                                if continuation_mode is True and STP_operativity is True:
                                    action = 'SLD'
                                else:
                                    action = 'BOT'

                                print("Entry price: ", entry_price)
                                print("TP: ", tp)
                                print("SL: ", sl)
                                print("Executed:", executed)
                                print("Current price:", current_price)

                                if order_placed is False: #TO ALLOW JUST ONE OPERATION
                                    try_again_reset = True

                                if order_placed is True:
                                    send_message(25169251, ('ES - Order executed'))
                                #position direction recognizer
                                #for close_position function
                                #is_long = True
                        elif now.time() > end_time:
                            if order_placed is True and executed is False and automatic is True:
                                # self.reqGlobalCancel()
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                order_placed = False
                                print("Orders canceled because the session is done")
                            #sound
                            #winsound.PlaySound("sounds/time_over.wav", winsound.SND_ASYNC)
                            winsound.PlaySound("sounds/voice/Allison/no_trade.wav", winsound.SND_ASYNC)

                            print('''
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            !!! DONE DONE DONE !!!
                            2.2
                            ''')
                            print(now.time())
                            print("---> NO TRADE <---")
                            done = True
                            go = False
                            send_message(25169251, ('ES - No trade'))
                    # elif done is True and go is False:
                    #     #trade logic
                    #     if executed is True:
                    #         if current_price > tp:
                    #             result = "GAIN " + gain
                    #             winsound.PlaySound("sounds/voice/Allison/gain.wav", winsound.SND_ASYNC)
                    #             print(now.time())
                    #             ###########################################
                    #             print("Take Profit Price: ", tp)
                    #             print("Stop Loss Price: ", sl)
                    #             print("Current Price: ", current_price)
                    #             print("Boolean Check - price higher than TP: ", current_price > tp)
                    #             ###########################################
                    #             print("Operation: ", result)
                    #             executed = False
                    #             is_long = False
                    #             is_short = False
                    #         elif current_price <= sl:
                    #             result = "LOSS " + loss
                    #             winsound.PlaySound("sounds/voice/Allison/loss.wav", winsound.SND_ASYNC)
                    #             print(now.time())
                    #             ###########################################
                    #             print("Take Profit Price: ", tp)
                    #             print("Stop Loss Price: ", sl)
                    #             print("Current Price: ", current_price)
                    #             ###########################################
                    #             print("Operation: ", result)
                    #             executed = False
                    #             is_long = False
                    #             is_short = False
                    #     if result is not None:
                    #         #Saving in the database
                    #         conn = sqlite3.connect('database.db')
                    #         cur = conn.cursor()
                    #         if f_pom is True:
                    #             cur.execute("UPDATE f_pom SET gain_loss= ? WHERE date= ?", (result, today))
                    #             conn.commit()
                    #         elif f_ser is True:
                    #             cur.execute("UPDATE f_ser SET gain_loss= ? WHERE date= ?", (result, today))
                    #             conn.commit()
                    #         conn.close()
                    #         if result.startswith("GAIN"):
                    #             conn = sqlite3.connect('database.db')
                    #             cur = conn.cursor()
                    #             if f_pom is True:
                    #                 cur.execute("INSERT INTO f_pom_Profit VALUES (NULL, ?, ?)", (M1_calc.today, gain))
                    #                 conn.commit()
                    #             elif f_ser is True:
                    #                 cur.execute("INSERT INTO f_ser_Profit VALUES (NULL, ?, ?)", (M1_calc.today, gain))
                    #                 conn.commit()
                    #             conn.close()
                    #             result = None
                    #             executed = False
                    #         elif result.startswith("LOSS"):
                    #             conn = sqlite3.connect('database.db')
                    #             cur = conn.cursor()
                    #             if f_pom is True:
                    #                 cur.execute("INSERT INTO f_pom_Loss VALUES (NULL, ?, ?)", (M1_calc.today, loss))
                    #                 conn.commit()
                    #             elif f_ser is True:
                    #                 cur.execute("INSERT INTO f_ser_Loss VALUES (NULL, ?, ?)", (M1_calc.today, loss))
                    #                 conn.commit()
                    #             conn.close()
                    #             result = None
                    #             executed = False


                    #move recognizer
                    move = last_max - last_min
                    # if len(movements_cleaned) > 0:
                    #     average_move = nearest_quarter(Average(movements_cleaned))
                    #     if dynamic_M1 is True:
                    #         M1 = nearest_quarter(Average([M1_original, average_move]))


                        # if move <= average_move:
                        #     move_in_range = True
                        #     if last_avg_move_check != move_in_range:
                        #         # print('Move in avg range')
                        #         last_avg_move_check = move_in_range
                        # else:
                        #     move_in_range = False
                        #     if last_avg_move_check != move_in_range:
                        #         if start_time <= now.time() <= end_time:
                        #             print('\n')
                        #             print(now.time())
                        #             print('Avg move:', average_move)
                        #             print('!!! Move out of avg range !!!')
                        #         last_avg_move_check = move_in_range

                    rev_move = current_price - last_min

                    #### MOVE DURATION CHECK
                    if len(times) > 0:
                        if done is False and go is True:
                            end_temp = time.time()
                            duration_check = end_temp - start
                            if duration_check > Average(times) and order_placed is True and executed is False:
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                self.cancelOrder(self.nextValidOrderId-4)
                                self.cancelOrder(self.nextValidOrderId-5)
                                self.cancelOrder(self.nextValidOrderId-6)
                                order_placed = False
                                print(now.time())
                                print("Orders canceled because this movement is taking too long")
                                print("AVG moves time: ", strftime("%H:%M:%S",gmtime(Average(times))))
                                print("Current move time: ", strftime("%H:%M:%S",gmtime(duration_check)))

                    if rev_move < reverse:
                        if current_price < last_min:

                            rev_move = 0

                        if len(movements) is 0 and current_price not in price_levels:
                            price_levels.append(current_price)

                    if rev_move >= reverse:
                        end = time.time()
                        final_time = end - start
                        # times.append(final_time)
                        #grabbing movements in the trading timeframe
                        # if move > 3: #previously 5
                        #     movements_cleaned.append(move)

                        if start_time <= now.time() <= end_time:
                            if now.time() > start_op_time:
                                times.append(final_time)
                                movements.append(move)
                        if order_placed is True and executed is False:
                            if done is False and automatic is True:
                                # self.reqGlobalCancel()
                                self.cancelOrder(self.nextValidOrderId-1)
                                self.cancelOrder(self.nextValidOrderId-2)
                                self.cancelOrder(self.nextValidOrderId-3)
                                self.cancelOrder(self.nextValidOrderId-4)
                                self.cancelOrder(self.nextValidOrderId-5)
                                self.cancelOrder(self.nextValidOrderId-6)
                                order_placed = False
                                print(now.time())
                                print("Orders canceled because reverse")


                        last_max = current_price

                        # if len(movements_cleaned) > 0:
                        #     average_move = nearest_quarter(Average(movements_cleaned))
                        #     if dynamic_M1 is True:
                        #         M1 = nearest_quarter(Average([M1_original, average_move]))
                        if len(movements) > 0:
                            average_move = nearest_quarter(Average(movements))
                            if dynamic_M1 is True:
                                M1 = nearest_quarter(Average([M1_original, average_move]))


                        dwn_trend = False
                        up_trend = True
                        manual_trigger_notification = True #could cause a repeated notification around order entry
                        rev_move = 0

                        order_moved = False

                        price_levels = list()
                        start = time.time()
    #----------

    # TRADE LOGIC MODULE (TLM) -----------------------------------------------------
                # if done is True and go is False: ### TLM
                #     #trade logic
                #     if executed is True and is_short is True:
                #         if current_price < tp:
                #             result = "GAIN " + gain
                #             winsound.PlaySound("sounds/voice/Allison/gain.wav", winsound.SND_ASYNC)
                #             print(now.time())
                #             ###########################################
                #             print("Take Profit Price: ", tp)
                #             print("Stop Loss Price: ", sl)
                #             print("Current Price: ", current_price)
                #             print("Boolean Check - price lower than TP: ", current_price < tp)
                #             ###########################################
                #             print("Operation: ", result)
                #             print("Executed:", executed)
                #             print("1.1")
                #             print("**********")
                #             # executed = False
                #             # is_long = False #
                #             # is_short = False #
                #         elif current_price >= sl:
                #             result = "LOSS " + loss
                #             winsound.PlaySound("sounds/voice/Allison/loss.wav", winsound.SND_ASYNC)
                #             print(now.time())
                #             ###########################################
                #             print("Take Profit Price: ", tp)
                #             print("Stop Loss Price: ", sl)
                #             print("Current Price: ", current_price)
                #             ###########################################
                #             print("Operation: ", result)
                #             print("Executed:", executed)
                #             print("1.2")
                #             print("**********")
                #             # executed = False #
                #             # is_long = False #
                #             # is_short = False
                #     elif executed is True and is_long is True:
                #         if current_price > tp:
                #             result = "GAIN " + gain
                #             winsound.PlaySound("sounds/voice/Allison/gain.wav", winsound.SND_ASYNC)
                #             print(now.time())
                #             ###########################################
                #             print("Take Profit Price: ", tp)
                #             print("Stop Loss Price: ", sl)
                #             print("Current Price: ", current_price)
                #             print("Boolean Check - price higher than TP: ", current_price > tp)
                #             ###########################################
                #             print("Operation: ", result)
                #             print("Executed:", executed)
                #             print("2.1")
                #             print("**********")
                #             # executed = False
                #             # is_long = False
                #             # is_short = False
                #         elif current_price <= sl:
                #             result = "LOSS " + loss
                #             winsound.PlaySound("sounds/voice/Allison/loss.wav", winsound.SND_ASYNC)
                #             print(now.time())
                #             ###########################################
                #             print("Take Profit Price: ", tp)
                #             print("Stop Loss Price: ", sl)
                #             print("Current Price: ", current_price)
                #             ###########################################
                #             print("Operation: ", result)
                #             print("Executed:", executed)
                #             print("2.2")
                #             print("**********")
                #             # executed = False
                #             # is_long = False
                #             # is_short = False
                #     elif result is not None:
                #         #Saving in the database
                #         conn = sqlite3.connect('database.db')
                #         cur = conn.cursor()
                #         if f_pom is True:
                #             cur.execute("UPDATE f_pom SET gain_loss= ? WHERE date= ?", (result, today))
                #             conn.commit()
                #         elif f_ser is True:
                #             cur.execute("UPDATE f_ser SET gain_loss= ? WHERE date= ?", (result, today))
                #             conn.commit()
                #         conn.close()
                #         if result.startswith("GAIN"):
                #             conn = sqlite3.connect('database.db')
                #             cur = conn.cursor()
                #             if f_pom is True:
                #                 cur.execute("INSERT INTO f_pom_Profit VALUES (NULL, ?, ?)", (M1_calc.today, gain))
                #                 conn.commit()
                #             elif f_ser is True:
                #                 cur.execute("INSERT INTO f_ser_Profit VALUES (NULL, ?, ?)", (M1_calc.today, gain))
                #                 conn.commit()
                #             conn.close()
                #             result = None
                #             # executed = False
                #         elif result.startswith("LOSS"):
                #             conn = sqlite3.connect('database.db')
                #             cur = conn.cursor()
                #             if f_pom is True:
                #                 cur.execute("INSERT INTO f_pom_Loss VALUES (NULL, ?, ?)", (M1_calc.today, loss))
                #                 conn.commit()
                #             elif f_ser is True:
                #                 cur.execute("INSERT INTO f_ser_Loss VALUES (NULL, ?, ?)", (M1_calc.today, loss))
                #                 conn.commit()
                #             conn.close()
                #             result = None
                #             # executed = False
    # ------------------------------------------------------------------------------

            # max movement recognizer ----------
            # for move in movements:
            #     if start_time <= now.time() <= end_time:
            #         if now.time() > start_op_time:
            #             if move > max_move:
            #                 max_move = move
            #
            #                 #save data in the database
            #                 conn = sqlite3.connect('database.db')
            #                 cur = conn.cursor()
            #                 if f_pom is True:
            #                     cur.execute("UPDATE f_pom SET max_movement= ? WHERE date= ?", (max_move, today))
            #                     conn.commit()
            #                 elif f_ser is True:
            #                     cur.execute("UPDATE f_ser SET max_movement= ? WHERE date= ?", (max_move, today))
            #                     conn.commit()
            #                 conn.close()
            #
            #     else:
            #         continue
            #----------

            #end of the loop!
            if up_trend is False and dwn_trend is False:
                last_price = current_price

            starting_up = False
            count += 1
            time.sleep(0.1)

    def observation(self): #BETA
        global contratto

        global times
        global start
        global end

        global quindici
        global ventuno
        global sedici
        global diciannove
        global sei

        global news_range
        global evening_comp
        global rest

        global news #to be reset every day
        global news_in_session #to be reset every day

        global time_delta_post_news
        global time_delta_pre_news

        global automatic
        global manual
        global was_automatic

        global first_move_notification
        global automatic_notification
        global manual_news_notification
        global manual_trigger_notification
        global manual_notification
        global notification
        global notif_start1
        global notif_end1
        global notif_start2
        global notif_end2

        global start_day
        global end_day

        global current_price
        global last_price

        global M1
        global order
        global last_order

        global count

        global up_trend
        global dwn_trend

        global last_price
        global move
        global rev_move
        global last_max
        global last_min

        global movements
        global max_move
        global average_move
        global move_in_range
        global last_avg_move_check

        global f_pom_start
        global f_pom_end
        global f_ser_start
        global f_ser_end

        global M1_ser_calc

        global start_time
        global end_time
        global start_trading_time
        global end_trading_time

        global start_op_time

        global done
        global go

        global daily_max
        global daily_min
        global p_close

        global pos
        global executed
        global result

        global size
        global pre_session_size
        global mm
        global session_mm
        global pl
        global gain
        global loss

        global tp
        global sl
        global entry_price
        global trigger_price_delta
        global trigger_price
        global order_placed

        global is_long
        global is_short
        global emergency_size
        global op_done

        global f_pom
        global f_ser

        global difference

        global fm_check_done

        global accuracy

        global green_light

        global entry_time
        global action

        global is_closed

        global pre_market_range

        global original_size

        global price_levels

        global gap_allowed

        global T_url

        global dynamic_size_increase
        global double_size_low_vol

        global reverse
        global default_reverse

        global order_moved

        global range_bars_ticks

        global default_dynamic_M1
        global dynamic_M1
        global M1_original
        # global movements_cleaned

        global position_manager
        global exit_price_position_manager
        global position_manager_ready

        global avg_volatility_10d

        global continuation_mode
        global STP_operativity
        global continuation_margin

        global five_min_done
        global five_min_reset
        global try_again_reset

        global op_reset_allowed

        global starting_up

        global volatility_expected

        global avg_pom
        global avg_ser
        global avg_tot

        global historical_volume
        global historical_volatility

        global first_hour_max
        global first_hour_min

        global volume_leak_avg

        global reverse_ob
        global rev_move_ob
        global last_max_ob
        global last_min_ob
        global move_ob
        global up_trend_ob
        global dwn_trend_ob
        global difference_ob
        global movements_ob
        global tp_multiplier
        # global movements_cleaned_ob

        global VP_on

        #############################
        # print("Last max: ", last_max)
        # print("Last min: ", last_min)
        #############################

        time.sleep(5)


        #round to nearest psycho area
        def myround(x, base=2.5):
            return base * round(x/base) #<<< closest one

        def round_up(x):
            return float(math.ceil(x / 2.5)) * 2.5

        def round_down(x):
            return float(math.floor(x / 2.5)) * 2.5

        def human_format(num):
            num = float('{:.3g}'.format(num))
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num /= 1000.0
            return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

        def nearest_quarter(x):
            return round(x*4)/4

        def Average(lst):
            return sum(lst) / len(lst)

        while True:

            #time
            now = datetime.datetime.today()

            #-------------------------------------

            if datetime.time(1, 5, 0) <= now.time() <= datetime.time(1, 6, 0):

                #sleep mode
                def sleeping(hours):
                    for h in range(hours):
                        for m in range(60): #1h
                            time.sleep(60) #1min
                sleeping(10)
                time.sleep(60)

            if datetime.time(sedici, 31, 0) < now.time() < datetime.time(sedici, 32, 0):
                winsound.PlaySound("sounds/voice/Allison/move_show.wav", winsound.SND_ASYNC)
                print(now.time())
                print("FASCIA POMERIDIANA, SESSION IS DONE")
                print("Movements: ", movements_ob)
                print("Max movement: ", max_move)

                # save movements in the DB
                todayDB = datetime.date.today()
                conn = sqlite3.connect('database.db')
                cur = conn.cursor()
                for m in movements_ob:
                    try:
                        cur.execute("INSERT INTO f_pom_movements VALUES (NULL, ?, ?, ?, ?)", (todayDB, m, range_bars_ticks, contratto))
                    except:
                        print('ERROR WRITING MOVES IN DB --------- !!!')
                        continue
                    conn.commit()
                conn.close()
                print("Movements saved in the DB")

                # -------------------- ADJUSTING MAX MOVEMENT (MAM)
                if len(movements_ob) > 0:
                    index = movements_ob.index(max_move)
                    #print("Max movement index: ", index)
                    while movements_ob[-1] != max_move and movements_ob[-2] != max_move and movements_ob[index+1] < mm: #original 2.50
                        index = movements_ob.index(max_move)
                        if movements_ob[index+1] < mm: #original 2.50
                            max_move = max_move + (movements_ob[index+2] - movements_ob[index+1])
                            del movements_ob[index+1]
                            del movements_ob[index+1]
                            movements_ob[index] = max_move
                else:
                    if reverse_ob == default_reverse:
                        max_move = default_reverse
                    else:
                        max_move = reverse_ob
                print("Adjusted max: ", max_move)
                conn = sqlite3.connect('database.db')
                cur = conn.cursor()
                if f_pom is True:
                    cur.execute("UPDATE f_pom SET max_movement= ? WHERE date= ?", (max_move, today))
                    conn.commit()
                    cur.execute("UPDATE f_pom SET PAs_to_rev= ? WHERE date= ?", (PAs_avg_to_rev, today))
                    conn.commit()
                elif f_ser is True:
                    cur.execute("UPDATE f_ser SET max_movement= ? WHERE date= ?", (max_move, today))
                    conn.commit()
                    cur.execute("UPDATE f_ser SET PAs_to_rev= ? WHERE date= ?", (PAs_avg_to_rev, today))
                    conn.commit()
                conn.close()

                notification = True
                #observe = True

                print('Executed:', executed)
                print('Is closed:', is_closed)

                if executed is True and is_closed is True:
                    executed = False
                    print('Executed:', executed)
                    print('Is closed:', is_closed)

                if executed is True and is_long is True and is_short is False and automatic is True and is_closed is False:
                    TestApp.close_long(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    executed = False
                    is_long = False
                    is_short = False
                    send_message(25169251, ('ES - Emergency close'))
                    # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                elif executed is True and is_short is True and is_long is False and automatic is True and is_closed is False:
                    TestApp.close_short(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    executed = False
                    is_short = False
                    is_long = False
                    send_message(25169251, ('ES - Emergency close'))
                    # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                elif executed is False and is_long is False and is_short is False:
                    print("No open positions")
                    print('One last check')
                    self.cancelOrder(self.nextValidOrderId-1) ####### this cause the order cancel attempt in the end
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    time.sleep(1)
                    # print("- YOU CAN CLOSE THE SOFTWARE NOW -")

                # if executed is False and is_long is False and is_short is False:
                #     print("No open positions")
                #     self.cancelOrder(self.nextValidOrderId-1)
                #     self.cancelOrder(self.nextValidOrderId-2)
                #     self.cancelOrder(self.nextValidOrderId-3)
                #     print("- YOU CAN CLOSE THE SOFTWARE NOW -")

                size = original_size
                pre_session_size = original_size
                order_moved = False

                # if len(movements_cleaned_ob) > 0:
                #     print('\n')
                #     print('Filtered Moves OBSERVATION:', movements_cleaned_ob)
                #     if len(movements_cleaned) > 0:
                #         print('-' * 50)
                #         print('Filtered Moves OPERATIVITY:', movements_cleaned)
                    # if len(times) > 0:
                    #     print('Movement durations:', times)
                    # print('\n')

                first_hour_range = first_hour_max - first_hour_min
                print('1st hour range:', first_hour_range)
                print('\n')

                print("- YOU CAN CLOSE THE SOFTWARE NOW -")

                time.sleep(60)

            if datetime.time(ventuno, 46, 0) < now.time() < datetime.time(ventuno, 47, 0):
                winsound.PlaySound("sounds/voice/Allison/move_show.wav", winsound.SND_ASYNC)
                print(now.time())
                print("FASCIA SERALE, SESSION IS DONE")
                print("Movements: ", movements_ob)
                print("Max movement: ", max_move)

                # save movements in the DB
                todayDB = datetime.date.today()
                conn = sqlite3.connect('database.db')
                cur = conn.cursor()
                for m in movements_ob:
                    try:
                        cur.execute("INSERT INTO f_ser_movements VALUES (NULL, ?, ?, ?, ?)", (todayDB, m, range_bars_ticks, contratto))
                    except:
                        print('ERROR WRITING MOVES IN DB --------- !!!')
                        continue
                    conn.commit()
                conn.close()
                print("Movements saved in the DB")

                # -------------------- ADJUSTING MAX MOVEMENT (MAM)
                if len(movements_ob) > 0:
                    index = movements_ob.index(max_move)
                    #print("Max movement index: ", index)
                    while movements_ob[-1] != max_move and movements_ob[-2] != max_move and movements_ob[index+1] < mm: #original 2.50
                        index = movements_ob.index(max_move)
                        if movements_ob[index+1] < mm: #original 2.50
                            max_move = max_move + (movements_ob[index+2] - movements_ob[index+1])
                            del movements_ob[index+1]
                            del movements_ob[index+1]
                            movements_ob[index] = max_move
                else:
                    if reverse_ob == default_reverse:
                        max_move = default_reverse
                    else:
                        max_move = reverse_ob
                print("Adjusted max: ", max_move)
                conn = sqlite3.connect('database.db')
                cur = conn.cursor()
                if f_pom is True:
                    cur.execute("UPDATE f_pom SET max_movement= ? WHERE date= ?", (max_move, today))
                    conn.commit()
                    cur.execute("UPDATE f_pom SET PAs_to_rev= ? WHERE date= ?", (PAs_avg_to_rev, today))
                    conn.commit()
                elif f_ser is True:
                    cur.execute("UPDATE f_ser SET max_movement= ? WHERE date= ?", (max_move, today))
                    conn.commit()
                    cur.execute("UPDATE f_ser SET PAs_to_rev= ? WHERE date= ?", (PAs_avg_to_rev, today))
                    conn.commit()
                conn.close()

                notification = True
                #observe = True
                print('Executed:', executed)
                print('Is closed:', is_closed)

                if executed is True and is_closed is True:
                    executed = False
                    print('Executed:', executed)
                    print('Is closed:', is_closed)

                if executed is True and is_long is True and is_short is False and automatic is True and is_closed is False:
                    TestApp.close_long(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    executed = False
                    is_long = False
                    is_short = False
                    send_message(25169251, ('ES - Emergency close'))
                    # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                elif executed is True and is_short is True and is_long is False and automatic is True and is_closed is False:
                    TestApp.close_short(self)
                    time.sleep(1)
                    # self.reqGlobalCancel()
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    print("Emergency close")
                    executed = False
                    is_short = False
                    is_long = False
                    send_message(25169251, ('ES - Emergency close'))
                    # print("- YOU CAN CLOSE THE SOFTWARE NOW -")
                elif executed is False and is_long is False and is_short is False:
                    print("No open positions")
                    print('One last check')
                    self.cancelOrder(self.nextValidOrderId-1)
                    self.cancelOrder(self.nextValidOrderId-2)
                    self.cancelOrder(self.nextValidOrderId-3)
                    time.sleep(1)
                    # print("- YOU CAN CLOSE THE SOFTWARE NOW -")

                size = original_size
                pre_session_size = original_size
                order_moved = False

                # if len(movements_cleaned_ob) > 0:
                #     print('\n')
                #     print('Filtered Moves OBSERVATION:', movements_cleaned_ob)
                #     if len(movements_cleaned) > 0:
                #         print('-' * 50)
                #         print('Filtered Moves OPERATIVITY:', movements_cleaned)
                    # if len(times) > 0:
                    #     print('Movement durations:', times)
                    # print('\n')

                print("- YOU CAN CLOSE THE SOFTWARE NOW -")

                time.sleep(60)

            #recognize max and min 1st hours
            if f_pom is True:
                if start_op_time <= now.time() < end_time:
                    if current_price > first_hour_max:
                        first_hour_max = current_price
                    if current_price < first_hour_min:
                        first_hour_min = current_price

            #recognize max and min DAILY
            # if current_price > daily_max:
            #     daily_max = current_price
            # if current_price < daily_min:
            #     daily_min = current_price



            if count > 10:
            #if start_day <= now.time() <= end_day:
                # difference = current_price - last_price


                #recognize max and min
                if current_price > last_max_ob:
                    last_max_ob = current_price
                if current_price < last_min_ob:
                    last_min_ob = current_price

    # NEUTRAL TREND ----------
                if up_trend_ob is False and dwn_trend_ob is False:

                    if last_price != None:
                        difference_ob = current_price - last_price


                        if move_ob > 1:
                            up_trend_ob = True
                            dwn_trend_ob = False
                        if move_ob < -1:
                            dwn_trend_ob = True
                            up_trend_ob = False
                        move_ob += difference_ob
    #----------


    # UP TREND ----------
                if up_trend_ob is True:
                    dwn_trend_ob = False

                    #move recognizer
                    move_ob = last_max_ob - last_min_ob
                    # if len(movements_cleaned) > 0:
                    #     average_move = nearest_quarter(Average(movements_cleaned))
                    #     if dynamic_M1 is True:
                    #         M1 = nearest_quarter(Average([M1_original, average_move]))


                        # if move <= average_move:
                        #     move_in_range = True
                        #     if last_avg_move_check != move_in_range:
                        #         # print('Move in avg range')
                        #         last_avg_move_check = move_in_range
                        # else:
                        #     move_in_range = False
                        #     if last_avg_move_check != move_in_range:
                        #         if start_time <= now.time() <= end_time:
                        #             print('\n')
                        #             print(now.time())
                        #             print('Avg move:', average_move)
                        #             print('!!! Move out of avg range !!!')
                        #         last_avg_move_check = move_in_range

                    rev_move_ob = current_price - last_max_ob

                    #### MOVE DURATION CHECK
                    # if len(times) > 0:
                    #     if done is False and go is True:
                    #         end_temp = time.time()
                    #         duration_check = end_temp - start
                    #         if duration_check > Average(times) and order_placed is True and executed is False:
                    #             self.cancelOrder(self.nextValidOrderId-1)
                    #             self.cancelOrder(self.nextValidOrderId-2)
                    #             self.cancelOrder(self.nextValidOrderId-3)
                    #             self.cancelOrder(self.nextValidOrderId-4)
                    #             self.cancelOrder(self.nextValidOrderId-5)
                    #             self.cancelOrder(self.nextValidOrderId-6)
                    #             order_placed = False
                    #             print(now.time())
                    #             print("Orders canceled because this movement is taking too long")
                    #             print("AVG moves time: ", strftime("%H:%M:%S",gmtime(Average(times))))
                    #             print("Current move time: ", strftime("%H:%M:%S",gmtime(duration_check)))

                    if rev_move_ob > -reverse_ob:
                        if current_price > last_max_ob:

                            rev_move_ob = 0


                    if rev_move_ob <= -reverse_ob:

                        #grabbing movements in the trading timeframe
                        # if move_ob > 5:
                        #     movements_cleaned_ob.append(move_ob)

                        if start_time <= now.time() <= end_time:
                            if now.time() > start_op_time:
                                movements_ob.append(move_ob) #### MOVEMENTS var used in operativity too!!!

                        last_min_ob = current_price

                        # if len(movements_cleaned) > 0:
                        #     average_move = nearest_quarter(Average(movements_cleaned))
                        #     if dynamic_M1 is True:
                        #         M1 = nearest_quarter(Average([M1_original, average_move]))
                        # if len(movements) > 0:
                        #     average_move = nearest_quarter(Average(movements))
                        #     ###ADJUST MM IN RELATION TO AVG MOVE
                        #     ##TO DO
                        #     if dynamic_M1 is True:
                        #         M1 = nearest_quarter(Average([M1_original, average_move]))


                        up_trend_ob = False
                        dwn_trend_ob = True

                        rev_move_ob = 0
    #----------


    # DOWN TREND ----------
                if dwn_trend_ob is True:
                    up_trend_ob = False

                    #move recognizer
                    move_ob = last_max_ob - last_min_ob
                    # if len(movements_cleaned) > 0:
                    #     average_move = nearest_quarter(Average(movements_cleaned))
                    #     if dynamic_M1 is True:
                    #         M1 = nearest_quarter(Average([M1_original, average_move]))


                        # if move <= average_move:
                        #     move_in_range = True
                        #     if last_avg_move_check != move_in_range:
                        #         # print('Move in avg range')
                        #         last_avg_move_check = move_in_range
                        # else:
                        #     move_in_range = False
                        #     if last_avg_move_check != move_in_range:
                        #         if start_time <= now.time() <= end_time:
                        #             print('\n')
                        #             print(now.time())
                        #             print('Avg move:', average_move)
                        #             print('!!! Move out of avg range !!!')
                        #         last_avg_move_check = move_in_range

                    rev_move_ob = current_price - last_min_ob

                    #### MOVE DURATION CHECK
                    # if len(times) > 0:
                    #     if done is False and go is True:
                    #         end_temp = time.time()
                    #         duration_check = end_temp - start
                    #         if duration_check > Average(times) and order_placed is True and executed is False:
                    #             self.cancelOrder(self.nextValidOrderId-1)
                    #             self.cancelOrder(self.nextValidOrderId-2)
                    #             self.cancelOrder(self.nextValidOrderId-3)
                    #             self.cancelOrder(self.nextValidOrderId-4)
                    #             self.cancelOrder(self.nextValidOrderId-5)
                    #             self.cancelOrder(self.nextValidOrderId-6)
                    #             order_placed = False
                    #             print(now.time())
                    #             print("Orders canceled because this movement is taking too long")
                    #             print("AVG moves time: ", strftime("%H:%M:%S",gmtime(Average(times))))
                    #             print("Current move time: ", strftime("%H:%M:%S",gmtime(duration_check)))

                    if rev_move_ob < reverse_ob:
                        if current_price < last_min_ob:

                            rev_move_ob = 0

                    if rev_move_ob >= reverse_ob:

                        #grabbing movements in the trading timeframe
                        # if move_ob > 5:
                        #     movements_cleaned_ob.append(move_ob)

                        if start_time <= now.time() <= end_time:
                            if now.time() > start_op_time:
                                movements_ob.append(move_ob)

                        last_max_ob = current_price

                        # if len(movements_cleaned) > 0:
                        #     average_move = nearest_quarter(Average(movements_cleaned))
                        #     if dynamic_M1 is True:
                        #         M1 = nearest_quarter(Average([M1_original, average_move]))
                        # if len(movements) > 0:
                        #     average_move = nearest_quarter(Average(movements))
                        #     if dynamic_M1 is True:
                        #         M1 = nearest_quarter(Average([M1_original, average_move]))


                        dwn_trend_ob = False
                        up_trend_ob = True

                        rev_move_ob = 0
    #----------

            # max movement recognizer ----------
            for mo in movements_ob:
                if start_time <= now.time() <= end_time:
                    if now.time() > start_op_time:
                        if mo > max_move:
                            max_move = mo

                            #save data in the database
                            conn = sqlite3.connect('database.db')
                            cur = conn.cursor()
                            if f_pom is True:
                                cur.execute("UPDATE f_pom SET max_movement= ? WHERE date= ?", (max_move, today))
                                conn.commit()
                            elif f_ser is True:
                                cur.execute("UPDATE f_ser SET max_movement= ? WHERE date= ?", (max_move, today))
                                conn.commit()
                            conn.close()

                else:
                    continue
            #----------

            #end of the loop!
            if up_trend_ob is False and dwn_trend_ob is False:
                # last_price = current_price
                pass


            count += 1
            time.sleep(0.1)


    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId

    # def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
    #     print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled, ", Remaining: ", remaining, ", LastFillPrice: ", lastFillPrice)
    #
    # def openOrder(self, orderId, contract, order, orderState):
    #     print("OpenOrder. ID:", orderId, contract.symbol, contract.secType, "@", contract.exchange, ":", order.action, order.orderType, order.totalQuantity, orderState.status)
    #
    # def execDetails(self, reqId, contract, execution):
    #     print("ExecDetails. ", reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)

    def BracketOrder(parentOrderId, action, quantity, limitPrice, takeProfitLimitPrice, stopLossPrice):
        #main or parent order
        parent = Order()
        parent.orderId = parentOrderId
        parent.action = action
        parent.orderType = "LMT"
        parent.totalQuantity = quantity
        parent.lmtPrice = limitPrice
        #The parent and children orders will need this attribute set to False to prevent accidental executions.
        #The LAST CHILD will have it set to True,
        parent.transmit = False

        takeProfit = Order()
        takeProfit.orderId = parent.orderId + 1
        takeProfit.action = "SELL" if action == "BUY" else "BUY"
        takeProfit.orderType = "LMT"
        takeProfit.totalQuantity = quantity
        takeProfit.lmtPrice = takeProfitLimitPrice
        takeProfit.parentId = parentOrderId
        takeProfit.transmit = False

        stopLoss = Order()
        stopLoss.orderId = parent.orderId + 2
        stopLoss.action = "SELL" if action == "BUY" else "BUY"
        stopLoss.orderType = "STP"
        #Stop trigger price
        stopLoss.auxPrice = stopLossPrice
        stopLoss.totalQuantity = quantity
        stopLoss.parentId = parentOrderId
        #In this case, the low side order will be the last child being sent. Therefore, it needs to set this attribute to True
        #to activate all its predecessors
        stopLoss.transmit = True

        bracketOrder = [parent, takeProfit, stopLoss]
        return bracketOrder

    def BracketOrderSTP(parentOrderId, action, quantity, limitPrice, takeProfitLimitPrice, stopLossPrice):
        #main or parent order
        parent = Order()
        parent.orderId = parentOrderId
        parent.action = action
        parent.orderType = "STP"
        parent.totalQuantity = quantity
        parent.auxPrice = limitPrice
        #The parent and children orders will need this attribute set to False to prevent accidental executions.
        #The LAST CHILD will have it set to True,
        parent.transmit = False

        takeProfit = Order()
        takeProfit.orderId = parent.orderId + 1
        takeProfit.action = "SELL" if action == "BUY" else "BUY"
        takeProfit.orderType = "LMT"
        takeProfit.totalQuantity = quantity
        takeProfit.lmtPrice = takeProfitLimitPrice
        takeProfit.parentId = parentOrderId
        takeProfit.transmit = False

        stopLoss = Order()
        stopLoss.orderId = parent.orderId + 2
        stopLoss.action = "SELL" if action == "BUY" else "BUY"
        stopLoss.orderType = "STP"
        #Stop trigger price
        stopLoss.auxPrice = stopLossPrice
        stopLoss.totalQuantity = quantity
        stopLoss.parentId = parentOrderId
        #In this case, the low side order will be the last child being sent. Therefore, it needs to set this attribute to True
        #to activate all its predecessors
        stopLoss.transmit = True

        bracketOrder = [parent, takeProfit, stopLoss]
        return bracketOrder

    def BUY(self):
        global entry_price
        global tp
        global sl
        global contratto
        global size

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId

        bracket = TestApp.BracketOrder(p_id, "BUY", size, entry_price, tp, sl)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            self.nextValidId(p_id)

    def BUY_STP(self):
        global entry_price
        global tp
        global sl
        global contratto
        global size

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId

        bracket = TestApp.BracketOrderSTP(p_id, "BUY", size, entry_price, tp, sl)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            self.nextValidId(p_id)

    def move_stp_up(self): ########
        global entry_price
        global tp
        global sl
        global contratto
        global size
        global emergency_size

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId-3

        bracket = TestApp.BracketOrder(p_id, "BUY", emergency_size, entry_price, tp, (entry_price + 0.25))
        print(bracket)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            # self.nextValidId(p_id)

    def SELL(self):
        global entry_price
        global tp
        global sl
        global contratto
        global size

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId

        bracket = TestApp.BracketOrder(p_id, "SELL", size, entry_price, tp, sl)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            self.nextValidId(p_id)

    def SELL_STP(self):
        global entry_price
        global tp
        global sl
        global contratto
        global size

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId

        bracket = TestApp.BracketOrderSTP(p_id, "SELL", size, entry_price, tp, sl)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            self.nextValidId(p_id)

    def move_stp_down(self): ########
        global entry_price
        global tp
        global sl
        global contratto
        global size
        global emergency_size

        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId-3

        bracket = TestApp.BracketOrder(p_id, "SELL", emergency_size, entry_price, tp, (entry_price - 0.25))
        print(bracket)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            # self.nextValidId(p_id)

    def close_order(parentOrderId, action, quantity):
        parent = Order()
        parent.orderId = parentOrderId
        parent.action = action
        parent.orderType = "MKT"
        parent.totalQuantity = quantity

        parent.transmit = True

        bracketOrder = [parent]
        return bracketOrder


    def close_long(self):
        global emergency_size
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId

        bracket = TestApp.close_order(p_id, "SELL", emergency_size) #replace "1" with "emergency_size"
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            self.nextValidId(p_id)

    def close_short(self):
        global emergency_size
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = contratto

        #place order
        p_id = self.nextValidOrderId

        bracket = TestApp.close_order(p_id, "BUY", emergency_size) #replace "1" with "emergency_size"
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
            p_id += 1
            self.nextValidId(p_id)

    def tickPrice(self, reqId, tickType, price, attrib):
        #print("Price:", price, end=' ')
        global current_price
        global last_price

        #grab the Price
        current_price = 0
        while current_price == 0:
            current_price = float(price)




    #def tickSize(self, reqId, tickType, size):
        #global order
        #print("")
        #print("---------->>> Order placed at: ", order )
        #print("Tick Size. Ticker Id:", reqId, "tickType:", TickTypeEnum.to_str(tickType), "Size:", size)


def main():
    global most_liquid
    global socket
    app = TestApp()

    app.connect("127.0.0.1", socket, 0)

    # input("Press enter to start ")
    print("I will work on:", contratto)
    print("Connecting...")
    time.sleep(5)
    #sound
    #winsound.PlaySound("sounds/connection.wav", winsound.SND_ASYNC)
    winsound.PlaySound("sounds/voice/Allison/connection.wav", winsound.SND_ASYNC)

    contract = Contract()

    contract.secType = "FUT"
    contract.exchange = "GLOBEX"
    contract.currency = "USD"
    contract.localSymbol = contratto




    app.reqMarketDataType(4) #to check because 1 should be for live data
    app.reqMktData(1, contract, "", False, False, [])

    reader_thread = threading.Thread(target=app.run)
    posc_thread = threading.Thread(target=app.position_check)
    security_thread = threading.Thread(target=app.security_system)
    trdlogic_thread = threading.Thread(target=app.trade_logic)
    # done_thread = threading.Thread(target=app.done_check)
    operating_thread = threading.Thread(target=app.operativity)
    observation_thread = threading.Thread(target=app.observation) #BETA

    # btn_thread = threading.Thread(target=app.switch_btn)
    #
    # btn_thread.start() ### Switch button manual/auto mode

    operating_thread.start()
    observation_thread.start() #BETA
    security_thread.start()
    trdlogic_thread.start()
    # done_thread.start()
    posc_thread.start()
    reader_thread.start()

    # app.run()


if __name__ == "__main__":
    if rest is False:
        main()
    else:
        print('Today is Holiday. Nothing to do here.')
        input(" --- Press ENTER to quit --- ")
