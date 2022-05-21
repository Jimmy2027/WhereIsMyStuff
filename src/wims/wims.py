from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
from modun.file_io import json2dict
from pymongo import MongoClient
from pprint import pprint


@dataclass
class Element:
    item_name: str
    location: str
    categories: Optional[Iterable[str]] = None
    description: Optional[str] = None
    location_history: dict = field(init=False)

    def __post_init__(self):
        self.location_history = {
            str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")): self.location
        }


@dataclass
class WIMS:
    json_config_fn = Path('~/.config/wims.json').expanduser()
    collection = None

    def __post_init__(self):
        self.collection = self.connect()

    def connect(self):
        mongodb_config = json2dict(self.json_config_fn)
        mongodb_uri = mongodb_config['mongodb_URI']
        client = MongoClient(mongodb_uri)
        db = client.ppb
        return db.wims

    def add_element(self, element: Element):
        pprint(f'Adding element: {element.__dict__}')
        self.collection.insert_one(element.__dict__)

    def get_element_info(self, element_name: str):
        # todo: add verbose flag?

        for item in self.collection.find({'item_name': element_name}):
            pprint(item)

    def get_category_elements(self, which_categories: str):
        which_categories = which_categories.split('|')

        def df_maker():
            yield from self.collection.find({'categories': {"$in": which_categories}})

        pprint(pd.DataFrame(data=df_maker()).set_index('item_name'))

    def update_element(self,
                       which_element: str,
                       new_loc: Optional[str] = None,
                       new_categories: Optional[str] = None,
                       new_description: Optional[str] = None):
        new_values = {
            'location': new_loc or None,
            'categories': new_categories or None,
            'description': new_description or None
        }

        if new_loc:
            # update location history
            new_values['location_history'] = {
                str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")): new_loc,
                **self.collection.find_one({'item_name': which_element})['location_history']
            }

        self.collection.update_one({'item_name': which_element}, {"$set": {k: v for k, v in new_values.items() if v}})

    def db2df(self):
        def df_maker():
            yield from self.collection.find({})

        df = pd.DataFrame(data=df_maker()).set_index('item_name')
        pprint(df)
