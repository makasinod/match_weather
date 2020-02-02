from selenium import webdriver
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import requests

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


def selenium_get_weather():
    driver = webdriver.Chrome("/home/kd/chrome/chromedriver")
    list_of_cities = ['Полтава', 'Ровно', 'Одесса']
    gismeteo_address = "https://www.gismeteo.ua"
    ten_days_xpath = "//a[contains(.,'10 дней')]"
    max_temp_xpath = "//div[@class='maxt']/span[@class = 'unit unit_temperature_c']"

    selenium_ready_dict = {}
    driver.get(gismeteo_address)
    driver.find_element_by_xpath(ten_days_xpath).click()
    for item in list_of_cities:
        driver.find_element_by_xpath("//div[@class = 'cities_item']/a/span[text() = '%s']/.." % item).click()
        ready_list = []
        all_result = driver.find_elements_by_xpath(max_temp_xpath)
        for res in all_result:
            ready_list.append(str(res.text).replace('+', ''))
        selenium_ready_dict[item] = ready_list[1:4]
    driver.quit()
    return selenium_ready_dict


def api_get_weather():
    today = datetime.now()
    three_days_list = []
    for item in range(1, 4):
        day = datetime.timestamp(today + timedelta(days=item))
        three_days_list.append(int(day))

    cities = {'Полтава': '49.34,34.34', 'Ровно': '50.37,26.15', 'Одесса': '46.28,30.44'}
    api_ready_dict = {}
    for k, v in cities.items():
        api_temp_list = []
        for item in three_days_list:
            correct_url = "https://api.darksky.net/forecast/657d096183e84dfa79654b3a3b25f8be/%s," \
                          "%d?units=si&lang=ru" % (v, item)
            url_of_weather = requests.get(correct_url)
            api_temp_list.append(str(int(url_of_weather.json()['daily']['data'][0]['temperatureMax'])))
        api_ready_dict[k] = api_temp_list
    return api_ready_dict


def write_to_es(id, body):
    es.index(index='makasin_corp', doc_type='weather_info', id=id, body=body)


def read_from_es(id):
    return es.get(index='makasin_corp', doc_type='weather_info', id=id)


write_to_es(1, api_get_weather())
write_to_es(2, selenium_get_weather())

res_api = read_from_es(1)['_source']
res_gis = read_from_es(2)['_source']

ans_list = []
ans_dict = {}
for k, v in res_api.items():
    ans_list = []

    first_list = res_gis[k]
    second_list = res_api[k]
    for i in range(0, 3):
        if first_list[i] == second_list[i]:
            ans_list.append('True')
        else:
            ans_list.append('False')
    ans_dict[k] = ans_list

print(ans_dict)