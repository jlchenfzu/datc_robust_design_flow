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


def change_cell_name(token):
    """ token should be <FUNCTION>_<SIZE> """

    function = token[0:4]
    function_dict = {
        'in01'  :     'INV',
        'na02'  :     'NAND2',
        'na03'  :     'NAND3',
        'na04'  :     'NAND4',
        'no02'  :     'NOR2',
        'no03'  :     'NOR3',
        'no04'  :     'NOR4',
        'ao12'  :     'AOI21',
        'ao22'  :     'AOI22',
        'oa12'  :     'OAI21',
        'oa22'  :     'OAI22',
        'ms00'  :     'DFF'
    }

    try:
        function = function_dict[function]
    except KeyError:
        sys.stderr.write("(W) Cannot change cell name %s\n" % (function))
        return token

    return function + "_X1"

def change_pin_name(pin_string, cell_name):
    gate_type = cell_name.split("_")[0]

    pins = list()

    if gate_type == 'DFF':
        for pin in pin_string:    # silly code..
            p, n = extract_pin_and_net(pin)
            if p == 'd':
                pins.append(".D(%s)" % (n))
            elif p == 'o':
                pins.append(".Q(%s)" % (n))
            elif p == 'ck':
                pins.append(".CK(clk)")
            else:
                # Skips the other pins
                continue

    elif gate_type in ('AOI21', 'OAI21'):
        for pin in pin_string:    # silly code..
            p, n = extract_pin_and_net(pin)
            if p == 'a':
                pins.append(".A(%s)" % (n))
            elif p == 'b':
                pins.append(".B1(%s)" % (n))
            elif p == 'c':
                pins.append(".B2(%s)" % (n))
            elif p in ('o'):
                pins.append(".ZN(%s)" % (n))
            else:
                pins.append(pin.strip(','))

    elif gate_type in ('AOI22', 'OAI22'):
        for pin in pin_string:    # silly code..
            p, n = extract_pin_and_net(pin)
            if p == 'a':
                pins.append(".A1(%s)" % (n))
            elif p == 'b':
                pins.append(".A2(%s)" % (n))
            elif p == 'c':
                pins.append(".B1(%s)" % (n))
            elif p == 'd':
                pins.append(".B2(%s)" % (n))
            elif p in ('o'):
                pins.append(".ZN(%s)" % (n))
            else:
                pins.append(pin.strip(','))

    elif gate_type in ('INV'):
        for pin in pin_string:    # silly code..
            p, n = extract_pin_and_net(pin)
            if p == 'a':
                pins.append(".A(%s)" % (n))
            elif p in ('o'):
                pins.append(".ZN(%s)" % (n))
            else:
                pins.append(pin.strip(','))

    else:
        for pin in pin_string:    # silly code..
            p, n = extract_pin_and_net(pin)
            if p == 'a':
                pins.append(".A1(%s)" % (n))
            elif p == 'b':
                pins.append(".A2(%s)" % (n))
            elif p == 'c':
                pins.append(".A3(%s)" % (n))
            elif p == 'd':
                pins.append(".A4(%s)" % (n))
            elif p in ('o'):
                pins.append(".ZN(%s)" % (n))
            else:
                pins.append(pin.strip(','))

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
                #  0   1   2    3       4       5       6
                # DFF INST ( .D(net), .Q(net), .CK(net) );
                pin_string = tokens[3:-1]
                pins = change_pin_name(pin_string, 'DFF')

                f.write("DFF_X1 %s ( " % (tokens[1]))
                f.write("%s );\n" % (', '.join(pins)))

            # Cell instantiations
            elif len(tokens) > 4:
                cell_name = change_cell_name(tokens[0])
                instance_name = tokens[1]
                pin_string = tokens[3:-1]
                pins = change_pin_name(pin_string, cell_name)

                f.write("%s %s ( " % (cell_name, instance_name))
                f.write("%s );\n" % (', '.join(pins)))

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

