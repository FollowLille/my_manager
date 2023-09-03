from dataclasses import dataclass
from datetime import date
import json


@dataclass
class LimitHandler:

    def __init__(self):
        with open('category.json') as file:
            self.categories = json.load(file)

    def __get_limits(self):
        with open('limits.json') as file:
            self.limits = json.load(file)

    def __add_limits(self, limits_dict: dict):
        self.__get_limits()
        with open('limits.json', 'w') as file:
            json.dump(limits_dict, file, ensure_ascii=False)

    def add_category_limit(self):
        list_of_categories = list(self.categories)

    def add_subcategory_limit(self, category):
        pass

    def get_my_limit(self):
        pass

    def delete_limit(self):
        pass
