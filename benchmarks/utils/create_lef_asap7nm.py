'''
    File name      : create_lef_asap7nm.py
    Author         : Jinwook Jung
    Created on     : Wed 01 Aug 2018 12:47:04 PM KST
    Last modified  : 2018-08-01 12:47:18
    Description    :
'''

from __future__ import print_function, division
from time import gmtime, strftime
from copy import deepcopy
import sys

def parse_cl():
    import argparse
    """ parse and check command line options
    @return: dict - optinos key/value
    """
    parser = argparse.ArgumentParser(description='Create a subset of lef file.')

    # Add arguments
    parser.add_argument('--lib', action="store", dest='lib', required=True)
    parser.add_argument('--lef', action="store", dest='lef', required=True)
    parser.add_argument('-o', action="store", dest='new_lef', default='out.lef')

    opt = parser.parse_args()

    return opt


def strip_unnecessary_char(token):
    char = ('"', '(', ')', ';', ',')
    for c in char:
        token = token.replace(c, '')
    return token


def get_gate_list(lines_iter):
    """ Parse liberty library and get a list of gates. """
    gate_list = list()

    try:    # Start parsing
        for line in lines_iter:
            tokens = line.split()

            if len(tokens) < 2: continue

            if tokens[0] == 'cell':
                name = strip_unnecessary_char(tokens[1])
                gate_list.append(name)

    except StopIteration:
        pass

    return gate_list


class LefMacro:
    def __init__(self, name):
        self.name = name
        self.lines = list()

def read_lef(lef, gate_list):
    # Read the file while keepng the original indent
    lines = [_ for _ in (l.rstrip() for l in open(lef, 'r')) if _]
    lines_iter = iter(lines)

    lef_macros = list()

    def populate_lef_macro(lef_macro, lines_iter):
        while True:
            l = next(lines_iter)
            tokens = l.split()
            try:
                if tokens[0] == "END" and tokens[1] == lef_macro.name:
                    break
            except IndexError:
                pass
            lef_macro.lines.append(l)

    for l in lines_iter:
        tokens = l.split()

        if tokens[0] == "MACRO" and tokens[1] in gate_list:
            lef_macro = LefMacro(tokens[1])
            populate_lef_macro(lef_macro, lines_iter)
            lef_macros.append(lef_macro)

    return lef_macros


def write_lef(lef_macros, new_lef):
    with open(new_lef, 'w') as f:
        f.write("VERSION 5.8 ;\n")
        f.write("BUSBITCHARS \"[]\" ;\n")
        f.write("DIVIDERCHAR \"/\" ;\n\n")

        for m in lef_macros:
            f.write("MACRO {}\n".format(m.name))
            [f.write(_ + "\n") for _ in m.lines]
            f.write("END {}\n\n".format(m.name))

        f.write("END LIBRARY ;\n\n")

def create_lef(lib, lef, new_lef):
    # Open Liberty library
    lines = [_ for _ in (l.strip() for l in open(lib, 'r')) if _]
    gate_list = get_gate_list(iter(lines))

    lef_macros = read_lef(lef, gate_list)

    write_lef(lef_macros, new_lef)

if __name__ == '__main__':
    opt = parse_cl()

    lib, lef = opt.lib, opt.lef
    new_lef = opt.new_lef

    print ("Input Liberty file: " + lib)
    print ("Input LEF file    : " + lef)
    print ("Output LEF file   : " + new_lef)

    create_lef(lib, lef, new_lef)

