from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Iterable, Optional

import pandas as pd
from modun.file_io import json2dict
from pymongo import MongoClient
from fuzzywuzzy import fuzz


def markdown2df(md_fn: Path):
    # Read a markdown file, getting the header from the first row and index from the second column
    # Drop the left-most and right-most null columns
    # Drop the header underline row

    df = pd.read_table(
        md_fn, sep="|", header=0, index_col=1, skipinitialspace=True, skip_blank_lines=True
    ).dropna(axis=1, how='all').iloc[1:]
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes('object'):
        df[col] = df[col].str.strip()

    return df


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
    config_dict: dict = None

    def __post_init__(self):
        self.config_dict = json2dict(self.json_config_fn)
        self.collection = self.connect()

    def connect(self):
        mongodb_uri = self.config_dict['mongodb_URI']
        client = MongoClient(mongodb_uri)
        db = client.ppb
        return db.wims

    def add_element(self, element: Element):
        pprint(f'Adding element: {element.__dict__}')
        self.collection.insert_one(element.__dict__)

    def get_element_info(self, element_name: str):
        df = pd.DataFrame({'item_name': [e['item_name'] for e in self.collection.find()]})
        df['fuzzy_match'] = df.apply(lambda x: fuzz.ratio(x.item_name, element_name), axis=1)
        df = df.sort_values(by='fuzzy_match', ascending=False)
        for item in self.collection.find({'item_name': df['item_name'].to_list()[0]}):
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

    def remove_element(self, which_element: str):
        self.collection.delete_one({'item_name': which_element})

    def sync_wims_table(self, overwrite: bool = False):
        """
        Sync the csv file with the wims database.
        Since the md file gets updated at every change of the db, if there is a discrepancy,
         it can only mean that the md file was updated.
        """
        md_path = Path(self.config_dict['wims_md_path']).expanduser()
        db_df = self.db2df(return_df=True).drop(columns=['_id', 'location_history'])

        if md_path.exists() and not overwrite:
            md_df: pd.DataFrame = markdown2df(md_path).dropna(subset=['item_name'])

            db_items = set(db_df['item_name'])

            for idx, row in md_df.iterrows():
                # if new element was added to md, add it to the db
                if row['item_name'] not in db_items:
                    new_element = Element(item_name=row.item_name, location=row.location, categories=row.categories,
                                          description=row.description)
                    self.add_element(new_element)

                # otherwise, if a value was updated in the md, update it also in the db
                elif {
                    # eval(v) is done to convert the string representation of the list to a list
                    k: v if k != 'categories' else eval(v) for k, v in row.to_dict().items()
                } != db_df.loc[db_df['item_name'] == row.item_name].iloc[0].to_dict():
                    self.update_element(
                        which_element=row.item_name,
                        new_loc=row.location,
                        new_categories=row.categories,
                        new_description=row.description,
                    )

        db_df.to_markdown(md_path)

    def db2df(self, return_df: bool = False) -> Optional[pd.DataFrame]:
        def df_maker():
            yield from self.collection.find({})

        df = pd.DataFrame(data=df_maker())
        if return_df:
            return df
        pprint(df.set_index('item_name'))

    def lend(self, which_element: str, recipient: str):
        """
        Update location and location history to the recipients name.
        Add "lent" to categories.
        """
        print('lending')
        curr_categories = self.connect().find_one({'item_name': which_element})['categories']
        new_categories = list({*curr_categories, 'lent'})
        self.update_element(
            which_element=which_element,
            new_loc=recipient,
            new_categories=new_categories
        )

    def unlend(self, which_element: str):
        """
        Update location and location history to the location before lending.
        """
        element_dict = self.connect().find_one({'item_name': which_element})

        # get the location before the lending
        previous_loc = element_dict['location_history'][list(element_dict['location_history'])[1]]

        self.update_element(
            which_element=which_element,
            new_loc=previous_loc,
            new_categories=list(set(element_dict['categories']) - {'lent'})
        )

    def rename_element(self, which_element: str, new_name: str):
        element_dict = self.connect().find_one({'item_name': which_element})
        element_dict['item_name'] = new_name
        self.collection.update_one({'_id': element_dict['_id']}, {"$set": {'item_name': new_name}})
        self.sync_wims_table(overwrite=True)


if __name__ == '__main__':
    wims = WIMS()
    wims.get_element_info('headlamp')
    # wims.lend("woko wäschechip 1", "John")
    # wims.rename_element('key', 'stolen bike key')
    # wims.sync_wims_table()
