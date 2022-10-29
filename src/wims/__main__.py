import argparse
import sys

from wims.wims import WIMS, Element


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--info', '-i', default='', type=str,
                        help="Give info about one object, category or location.")
    parser.add_argument('--add', '-a', default='', type=str,
                        help="Add element with given name to database."
                             "Example: wims -a 'veloversicherun karte' -l 'zurich' -c 'veloversicherung' -d 'Im blauem Ordner'")
    parser.add_argument('--description', '-d', default='', type=str,
                        help="Add or specify description of an element or location.")
    parser.add_argument('--categories', '-c', default='', type=str, help="specify the category/ies of an object.")
    parser.add_argument('--location', '-l', default='', type=str,
                        help="Goes together with the --add flag. Used to specify location of an object.")
    parser.add_argument('--show', '-s', action='store_true', dest='show',
                        help="Show database as a dataframe.")
    parser.add_argument('--update', '-u', default='', type=str,
                        help="Set this flag to update attributes of an existing element.")
    parser.add_argument(
        '--lend', default='', type=str,
        help="When lending an object to someone, location and location history are updated to that persons name."
             " Example usage: 'wims -u laptop --lend John'."
    )
    parser.add_argument('--unlend', default='', type=str,
                        help="When receiving a lent object, location and location history "
                             "are updated to the location before lending.")

    parser.add_argument(
        '--remove', default=False, action="store_true",
        help="To remove an element, type: wims -u element2remove --remove.")

    flags = parser.parse_args()

    wims = WIMS()

    if flags.add:
        for item in {'location', 'categories', 'description'}:
            if not getattr(flags, item):
                setattr(flags, item, input(f"{item}: \n"))

        new_element = Element(item_name=flags.add,
                              location=flags.location,
                              categories=flags.categories.split('|') or None,
                              description=flags.description or None)

        wims.add_element(element=new_element)

    elif flags.update:
        if flags.lend:
            wims.lend(which_element=flags.update, recipient=flags.lend)
        elif flags.remove:
            wims.remove_element(which_element=flags.update)
        else:
            for item in {'location', 'categories', 'description'}:
                if not getattr(flags, item):
                    setattr(flags, item, input(f"{item}: \n"))

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

    elif flags.unlend:
        wims.unlend(which_element=flags.unlend)

    elif flags.categories:
        wims.get_all_categories()

    wims.sync_wims_table(overwrite=True)


if __name__ == '__main__':
    sys.exit(main())
