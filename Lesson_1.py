from pathlib import Path
import requests
import time
import json


# params = {
#     'records_per_page': 12,
#     'page': 1
# }
# url = 'https://5ka.ru/api/v2/special_offers/'
# headers = {
#     "Accept": "application/json",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
#                   "88.0.4324.41 YaBrowser/21.2.0.1097 Yowser/2.5 Safari/537.36"
# }
# response = requests.get(url, params=params, headers = headers)
# html_temp = Path(__file__).parent.joinpath('temp.html')
# json_temp = Path(__file__).parent.joinpath('temp.json')
# json_temp.write_text(response.text, encoding='UTF-8')

class ParseURL:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
                      "/88.0.4324.41 YaBrowser/21.2.0.1097 Yowser/2.5 Safari/537.36",
    }

    def __init__(self, start_url: str, products_path: Path):
        self.start_url = start_url
        self.products_path = products_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.products_path.joinpath(f"{product['id']}.json")
            self._save(product, product_path)

    def _parse(self, url_data):
        while url_data:
            response = self._get_response(url_data)
            data = response.json()
            url_data = data["next"]
            for product in data["results"]:
                yield product

    @staticmethod
    def _save(data: dict, file_path):
        jdata = json.dumps(data, ensure_ascii=False)
        file_path.write_text(jdata, encoding="UTF-8")

    @staticmethod
    def _save(data: dict, file_path):
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='UTF-8')


class CategoriesParser(ParseURL):
    def __init__(self, categories_url: str, *args, **kwargs):
        self.categories_url = categories_url
        super().__init__(*args, **kwargs)

    def _get_categories(self) -> list:
        response = self._get_response(self.categories_url)
        data = response.json()
        return data

    def run(self):
        for category in self._get_categories():
            category["products"] = []
            url_data = f"{self.start_url}?categories={category['parent_group_code']}"
            file_path = self.products_path.joinpath(f"{category['parent_group_code']}.json")
            category["products"].extend(list(self._parse(url_data)))
            self._save(category, file_path)


def get_dir_path(dirname: str) -> Path:
    dir_path = Path(__file__).parent.joinpath(dirname)
    if not dir_path.exists():
        dir_path.mkdir()
    return dir_path


if __name__ == '__main__':
    url = 'https://5ka.ru/api/v2/special_offers/'
    categories_path = get_dir_path("categories")
    categories_url = 'https://5ka.ru/api/v2/categories/'
    cat_parser = CategoriesParser(categories_url, url, categories_path)
    cat_parser.run()
