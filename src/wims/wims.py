from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from modun.file_io import json2dict
from pymongo import MongoClient
import pprint


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

    def connect(self):
        mongodb_config = json2dict(self.json_config_fn)
        mongodb_uri = mongodb_config['mongodb_URI']
        client = MongoClient(mongodb_uri)
        db = client.ppb
        return db.wims

    def add_element(self, element: Element):
        collection = self.connect()
        print(f'Adding element: {element.__dict__}')
        collection.insert_one(element.__dict__)

    def get_info(self, element_name: str):
        # todo: add verbose flag?
        collection = self.connect()
        pprint.pprint(collection.find_one({'item_name': element_name}))
