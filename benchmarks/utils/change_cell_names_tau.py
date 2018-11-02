'''
    File name      : change_cell_names.py
    Author         : Jinwook Jung
    Created on     : Sun 06 Aug 2017 10:19:49 PM KST
    Last modified  : 2018-08-01 14:22:40
    Description    : Change cell names of ICCAD'14 TDP contest Verilogs.
'''

from time import gmtime, strftime
import sys, re, os


def extract_pin_and_net(token):
    """ token should be .PIN(NET), or .PIN(NET) """

    # replace ,.() with blank
    for c in ('.', ',', '(', ')'):
        token = token.replace(c, ' ')

    token = token.strip().split()
    pin, net = token[0], token[1]

    return pin, net


def change_pin_name(pin_string, cell_name):
    gate_type = cell_name.split("_")[0]
    assert gate_type == "DFF"

    pins = list()
    for pin in pin_string:    # silly code..
        p, n = extract_pin_and_net(pin)
        if p == 'D':
            pins.append(".D(%s)" % (n))
        elif p == 'Q':
            pins.append(".Q(%s)" % (n))
        elif p == 'CK':
            pins.append(".CK(clk)")
        else:
            # Skips the other pins
            continue

    return pins


def change_verilog(src, dest):
    with open(src, 'r') as f:
        lines = [line.rstrip() for line in f]

    with open(dest, 'w') as f:
        f.write(lines[0] + "\n")
        f.write("clk,\n")

        for line in lines[1:]:
            if line == "// Start PIs":
                f.write(line + '\n')
                f.write("input clk;\n")
                continue

            elif line.startswith('//'):
                f.write(line + '\n')
                continue

            tokens = line.split()

            if len(tokens) < 1:
                f.write(line + '\n')

            # remove clock buffer
            elif tokens[0].startswith('CLKBUF'):
                continue

            # Change dff cells
            elif tokens[0].startswith('DFF') or tokens[0].startswith('SDFF'):
                cell_name = "DFF_X1"
                pin_string = tokens[3:-1]
                pins = change_pin_name(pin_string, cell_name)

                f.write("%s %s ( " % (cell_name, tokens[1]))
                f.write("%s );\n" % (', '.join(pins)))

            # Cell instantiations
            elif len(tokens) > 4:
                f.write(line + '\n')

            else:
                f.write(line + '\n')

if __name__ == '__main__':
    def parse_cl():
        import argparse
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('-i', dest='src_v', required=True)
        parser.add_argument('-o', dest='dest_v', default='out.v')

        return parser.parse_args()

    opt = parse_cl()
    src = opt.src_v
    dest = opt.dest_v

    print ("Input file  : " + src)
    print ("Output file : " + dest)
    sys.stdout.flush()

    change_verilog(src, dest)

