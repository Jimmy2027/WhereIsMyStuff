import argparse
import sys

from wims.wims import WIMS, Element


def main():
    parser = argparse.ArgumentParser()
    # todo add argument when lending an object to someone
    parser.add_argument('--info', '-i', default='', type=str,
                        help="Give info about one object, category or location.")
    parser.add_argument('--add', '-a', default='', type=str, help="Add element with given name to database.")
    parser.add_argument('--description', '-d', default='', type=str,
                        help="Add or specify description of an element or location.")
    parser.add_argument('--categories', '-c', default='', type=str, help="specify the category/ies of an object.")
    parser.add_argument('--location', '-l', default='', type=str,
                        help="Goes together with the --add flag. Used to specify location of an object.")
    parser.add_argument('--show', '-s', action='store_true', dest='show',
                        help="Show database as a dataframe.")
    parser.add_argument('--update', '-u', default='', type=str,
                        help="Set this flag to update attributes of an existing element.")

    flags = parser.parse_args()

    wims = WIMS()

    if flags.add:
        new_element = Element(item_name=flags.add,
                              location=flags.location,
                              categories=flags.categories.split('|') or None,
                              description=flags.description or None)

        wims.add_element(element=new_element)

    elif flags.update:
        wims.update_element(which_element=flags.update,
                            new_loc=flags.location,
                            new_categories=flags.categories.split('|') if flags.categories else None,
                            new_description=flags.description)

    elif flags.info:
        if flags.categories:
            wims.get_category_elements(flags.categories)
        else:
            wims.get_element_info(flags.info)

    elif flags.show:
        wims.db2df()


if __name__ == '__main__':
    sys.exit(main())
