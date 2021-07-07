from pathlib import Path
import requests
from urllib.parse import urljoin
import bs4
import pymongo
import datetime


class MagnitParse:

    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client['data_mining']

    @staticmethod
    def _get_response(url_data):
        try:
            response = requests.get(url_data)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise SystemExit(e)
        else:
            return response

    def _get_soup(self, url_data):
        try:
            response = requests.get(url_data)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise SystemExit(e)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        if soup is None:
            raise SystemExit()
        return soup

    def _template(self):
        return {
            'url': lambda a: urljoin(self.start_url, a.attrs.get('href')),
            'promo_name': lambda a: a.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda a: a.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': lambda a: self._parse_float_price(
                a.find('div', attrs={'class': 'label__price label__price_old'})),
            'new_price': lambda a: self._parse_float_price(
                a.find('div', attrs={'class': 'label__price label__price_new'})),
            'image_url': lambda a: a.find('div', attrs={'class': 'card-sale__col card-sale__col_img'}).find(
                'picture').find('img')['data-src'],
            'date_from': lambda a: self._parse_date(
                a.find('div', attrs={'class': 'card-sale__date'}), 'с'),
            'date_to': lambda a: self._parse_date(
                a.find('div', attrs={'class': 'card-sale__date'}), 'до')

        }

    @staticmethod
    def _parse_float_price(list_to_parse):
        try:
            int_num = float(list_to_parse.find('span', attrs={'class': 'label__price-integer'}).text)
            try:
                dec_num = float(list_to_parse.find('span', attrs={'class': 'label__price-decimal'}).text)
            except ValueError:
                return int_num
        except ValueError:
            return None
        else:
            return int_num + dec_num/100

    def _parse_date(self, list_to_parse, start_word):
        result_date = {
            'month': None,
            'day': None
        }
        dates = list_to_parse.find_all('p')
        for date in dates:
            date_list = date.text.split()
            if date_list[0] == start_word:
                result_date['month'] = self._get_month_num(date_list[2])
                result_date['day'] = int(date_list[1])
        res_date = datetime.date(month=result_date['month'] + 1, day=result_date['day'],
                                 year=datetime.datetime.today().year)
        res_date = datetime.datetime.combine(res_date, datetime.time.min)
        return res_date

    @staticmethod
    def _get_month_num(month):
        month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                      'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return month_list.index(month)

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        for product_a in catalog.find_all('a', recursive=False):
            product_data = self._parse(product_a)
            self.save(product_data)

    def _parse(self, product_a: bs4.Tag) -> dict:
        product_data = {}
        for key, func in self._template().items():
            try:
                product_data[key] = func(product_a)
            except AttributeError:
                pass
        return product_data

    def save(self, data: dict):
        collection = self.db['magnit']
        collection.insert_one(data)


if __name__ == '__main__':
    url = 'https://magnit.ru/promo/?geo=moskva'
    db_client = pymongo.MongoClient('mongodb://localhost:27017/')
    parser = MagnitParse(url, db_client)
    parser.run()
"""
{
    "url": str,
    "promo_name": str,
    "product_name": str,
    "old_price": float,
    "new_price": float,
    "image_url": str,
    "date_from": "DATETIME",
    "date_to": "DATETIME",
}
"""
