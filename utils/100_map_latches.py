'''
    File name      : 100_map_latches.py
    Author         : Jinwook Jung (jinwookjungs@gmail.com)
    Created on     : Mon 07 Aug 2017 02:41:23 PM KST
    Last modified  : 2017-08-09 00:19:21
    Description    : Map latches of an ABC netlist to the specified lib cell.
'''

from time import gmtime, strftime
from textwrap import wrap
import sys, math, argparse

from latch_mapper import *

def parse_cl():
    """ Parse command line and return dictionary. """
    parser = argparse.ArgumentParser(
                description='Map all latches of the ABC synthesis result.')

    # Add arguments
    parser.add_argument('-i', dest='src_v', required=True)
    parser.add_argument('--latch', dest='latch_cell', required=True)
    parser.add_argument('--latch_in', dest='latch_in', required=True)
    parser.add_argument('--latch_out', dest='latch_out', required=True)
    parser.add_argument('--latch_ck', dest='latch_ck', required=True)
    parser.add_argument('--tie_hi', dest='tie_hi', default="vcc")
    parser.add_argument('--tie_hi_out', dest='tie_hi_out', required=True)
    parser.add_argument('--tie_lo', dest='tie_lo', default="vss")
    parser.add_argument('--tie_lo_out', dest='tie_lo_out', required=True)
    parser.add_argument('--clock', dest='clock_port')
    parser.add_argument('--sdc', dest='input_sdc')
    parser.add_argument('-o', dest='dest_v', default='out_lmapped.v')
    opt = parser.parse_args()

    if opt.input_sdc is None and opt.clock_port is None:
        parser.error("Either --sdc or --clock is required.")
        raise SystemExit(-1)

    elif opt.input_sdc is not None:
        try:
            # Example: create_clock [get_port <clock_port>] ...
            create_clock = [x.rstrip() for x in open(opt.input_sdc, 'r') \
                                        if x.startswith('create_clock')][0]
            tokens = create_clock.split()
            opt.clock_port = tokens[tokens.index('[get_ports') + 1][:-1]

        except ValueError:
            parser.error("Cannot find the clock port in %s." % (opt.input_sdc))
            raise SystemExit(-1)

        except TypeError:
            parser.error("Cannot open file %s." % (opt.input_sdc))
            raise SystemExit(-1)

    else:   # opt.clock_port is not None
        pass    # Nothing done.

    return opt


if __name__ == '__main__':
    opt = parse_cl()
    src_v = opt.src_v
    latch_cell = opt.latch_cell
    latch_in, latch_out, latch_ck = opt.latch_in, opt.latch_out, opt.latch_ck
    tie_hi, tie_lo = opt.tie_hi, opt.tie_lo
    tie_hi_out, tie_lo_out = opt.tie_hi_out, opt.tie_lo_out
    clock_port = opt.clock_port
    dest_v = opt.dest_v

    print ("Input file:  " + src_v)
    print ("Latch cell:  " + latch_cell)
    print ("Latch pins:  {}/{}/{}".format(latch_in, latch_out, latch_ck))
    print ("Tie cells:   {}/{}".format(tie_hi, tie_lo))
    print ("Clock port:  " + clock_port)
    print ("Output file: " + dest_v)
    sys.stdout.flush()

    mapper = LatchMapper(clock_port, latch_cell, latch_in, latch_out, latch_ck,
                         tie_hi, tie_hi_out, tie_lo, tie_lo_out)
    mapper.read_verilog(src_v)
    mapper.map_latches(dest_v)

