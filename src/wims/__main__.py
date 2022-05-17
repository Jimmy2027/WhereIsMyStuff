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

    flags = parser.parse_args()

    wims = WIMS()

    if flags.add:
        new_element = Element(item_name=flags.add, location=flags.location, categories=flags.categories or None,
                              description=flags.description or None)

        wims.add_element(element=new_element)
    elif flags.info:
        wims.get_info(flags.info)


if __name__ == '__main__':
    sys.exit(main())
