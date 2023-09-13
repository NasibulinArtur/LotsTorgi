import time
import sqlite3
import pyproj

import logging
#logging.disable(logging.CRITICAL)

import folium
from rosreestr2coord import Area


from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

center_only=True
with_proxy=True
area_type = 7

map = folium.Map(location=[64.6863136, 97.7453061], zoom_start=2)


###Cоздание бд
conn = sqlite3.connect(r'torgi.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS info(
   link Text,
   Kadastr TEXT,
   lowPrice TEXT,
   hightPrice TEXT,
   time Text);
""")
conn.commit()


def Parser():
    driver = webdriver.Chrome()
    driver.get("https://torgi.gov.ru/new/public/lots/reg")
    input()

    countOfLots = driver.find_element(By.CLASS_NAME, 'registry-items-amount').text
    intCountOfLots = countOfLots.replace(" ", "")
    pages = int(intCountOfLots) // 10
    print(f"Количество страниц {pages} ")
    for i in range(1, pages-2):
        time.sleep(3)
        print(f"Текущая страница {i} ")
        delta_y = 5500
        ActionChains(driver)\
            .scroll_by_amount(0, delta_y)\
            .perform()
        driver.find_element(By.CLASS_NAME, 'more').click()


    cards = driver.find_elements(By.CLASS_NAME, "lotCard")
    for element in cards:
        lotChars = element.find_element(By.CLASS_NAME, "lotChars")
        rightInfo = lotChars.find_element(By.CLASS_NAME, "right")
        kadastr = rightInfo.find_element(By.XPATH, ".//div[2]").text

        description = element.find_element(By.CLASS_NAME, "lotDescription")
        link = description.find_element(By.CLASS_NAME, "lotLink").get_attribute("href")
        price = element.find_elements(By.CLASS_NAME, "lotPrice")

        e = 0
        for i in price:
            e+=1
            if e==1:
                priceLow = i.find_element(By.XPATH, ".//div[1]").text
            else:
                priceHight= i.find_element(By.XPATH, ".//div[1]").text

        endtime = element.find_element(By.CLASS_NAME, "lotTime").text

        cur.execute("SELECT kadastr FROM info WHERE kadastr = ?", (kadastr,))
        if cur.fetchone() is None:
            priceHight = 0
            data = (link, kadastr, priceLow, priceHight, endtime)
            cur.execute("INSERT INTO info VALUES(?, ?, ?, ?, ?);", data)
            conn.commit()
            #print(link, priceLow, priceHight, endtime, kadastr)


def RosreestrApi():
    cur.execute("""SELECT kadastr, link, lowPrice, time from info""")
    numbers = cur.fetchall()
    for inf in numbers:
        print(inf)
        area = Area(inf[0])
        link = inf[1]
        price = inf[2]
        endTime = inf[3]
        openStreatMap = area.get_buffer_extent_list()
        try:
            xmin = openStreatMap[0]
            ymin = openStreatMap[1]
            xmax = openStreatMap[2]
            ymax = openStreatMap[3]

            # Определение проекции для EPSG:3857 (Web Mercator)
            mercator = pyproj.Proj('epsg:3857')

            # Определение проекции для EPSG:4326 (WGS 84)
            wgs84 = pyproj.Proj('epsg:4326')

            # Создание объекта Transformer для преобразования координат
            transformer = pyproj.Transformer.from_proj(mercator, wgs84)

            # Преобразование из EPSG:3857 в EPSG:4326
            lat_min, lon_min = transformer.transform(xmin, ymin)
            lat_max, lon_max = transformer.transform(xmax, ymax)

            folium.Rectangle([(lat_min, lon_min), (lat_max, lon_max)], color="red").add_to(map)
        except:
            print()
        try:
            openStreatMapCord = area.get_coord()
            openStreatMap = area.get_attrs()
            print(inf[0])
            print(openStreatMapCord)
            try:
                address = openStreatMap['address']
                cad_cost = openStreatMap['cad_cost']
                y = openStreatMapCord[0][0][0][0]
                x =openStreatMapCord[0][0][0][1]


                html = f"<b>Адресс:</b> {address}<br>" \
                       f"<br>" \
                       f"<b>Кадастровая стоимость:</b> {cad_cost}<br>" \
                       f"<b>Кадастровый номер:</b> {inf[0]}<br>" \
                       f"<br>" \
                       f"Цена - {price}<br>" \
                       f"<a href=''  target='_blank' rel='noopener noreferrer'>{link}</a><br>" \
                       f"<br>" \
                       f"{endTime}<br>"
                iframe = folium.IFrame(html)
                popup = folium.Popup(iframe,
                                     min_width=300,
                                     max_width=300)
                marker = folium.Marker([x, y],
                                       popup=popup).add_to(map)
            except:
                print("")


        except:
            print("Нет кординат")

#Parser()
RosreestrApi()

map.save('torgi.html')
# driver.close()