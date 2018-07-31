"""
    Usage: python3 create_genlib.py -i <src_lib> -o <dest_genlib>
    Translate a given liberty library of ICCAD2015 contest format,
    into a genlib format. Currently, latch information isn't extracted,
    so the resulting genlib only contains combinational cell information.
    Jinwook Jung (jinwookjungs@gmail.com)
    Last modification: 08/30/15
"""

from __future__ import print_function, division
from time import gmtime, strftime
from copy import deepcopy
import sys

#FUNCTION_DELIM = "_"
FUNCTION_DELIM = "x"

def parse_cl():
    import argparse
    """ parse and check command line options
    @return: dict - optinos key/value
    """
    parser = argparse.ArgumentParser(
                description='Create a genlib from the given liberty file.')

    # Add arguments
    parser.add_argument(
            '-i', action="store", dest='src_lib', required=True)
    parser.add_argument(
            '-o', action="store", dest='dest_genlib', default='out.genlib')
    parser.add_argument(
            '--lef', action="store", dest='lef')

    opt = parser.parse_args()

    return opt


class LibertyLibraryInfo(object):
    """ Liberty library information extracted from the given liberty file. """
    pvt = ['N/A'] * 3
    units = ['N/A'] * 6


class LibertyGate(object):
    """ liberty gate """
    def __init__(self, name, gate_type):
        self.name = name
        self.area = 0.0
        self.function = None 
        self.gate_type = gate_type        # GATE | LATCH
        self.pin_list = list()

    def __str__(self):
        gate_info = "Gate " + self.name \
                        + ', area: ' + str(self.area) \
                        + ', type: ' + self.gate_type \
                        + ', function: ' + self.function
        pin_info = [p.__str__() for p in self.pin_list]
        return "\n".join([gate_info] + pin_info) + "\n"

    def add_pin(self, pin):
        self.pin_list.append(pin)


class LibertyPin(object):
    """ Pin information got from the source liberty """
    def __init__(self, name):
        self.name = name
        self.direction = None
        self.function = None
        self.related_power_pin, self.related_ground_pin = 'VDD', 'VSS'
        self.capacitance = 0.0

        # Comb output pin
        self.max_capacitance = 999.9999
        self.min_capacitance = 0.0
        self.function = None

        self.is_clock = False    # True | False
        self.timing_info_list = list()    # timing() block information

    def __str__(self):
        timing_info_string = [i.__str__() for i in self.timing_info_list]
        return "\tPin - " + self.name \
                + "\n\t\tdirection: " + self.direction \
                + "\n\t\tcapacitance: " + str(self.capacitance) \
                + "\n\t\tmax_capacitance: " + str(self.max_capacitance) \
                + "\n\t\tfunction: " + str(self.function) \
                + "\n\t\tclock: " + str(self.is_clock) \
                + "\n\t\ttiming_info:\n" + "\n".join(timing_info_string)


class LibertyPinTimingInfo(object):
    """ Extract timing information from timing() block. The extract information
    will be (rdelay, rslope, fdelay, fslope) or (rconst, fconst). """
    def __init__(self):
        self.related_pin = None
        self.when = None
        self.sdf_cond = None
        self.timing_sense = None    # positive_unate | negative_unate | non_unate

        self.cell_fall_intrinsic = 0.0
        self.cell_fall_slope = 0.0
        self.cell_rise_intrinsic = 0.0
        self.cell_rise_slope = 0.0

        # Seq pin
        self.timing_type = None    # hold_rising | setup_rising
                                # | min_pulse_width
                                # | rising_edge | falling_edge
        self.fall_constraint = 0.0
        self.rise_constraint = 0.0

        # Delay: ("rise", intrinsic, slope) | ("fall", intrinsic, slope)
        # Constraint: ("setup", setup_time) | ("fall", fall_time)
        self.delay_value = list()        # list of tuple

    def __str__(self):
        return "\t\t\trelated_pin: " + str(self.related_pin) \
                + "\n\t\t\twhen: " + str(self.when) \
                + "\n\t\t\tsdf_cond: " + str(self.sdf_cond) \
                + "\n\t\t\ttiming_sense: " + str(self.timing_sense) \
                + "\n\t\t\ttiming_type: " + str(self.timing_type) \
                + "\n\t\t\tfall_intrinsic_delay: " + str(self.cell_fall_intrinsic) \
                + "\n\t\t\tfall_slope: " + str(self.cell_fall_slope) \
                + "\n\t\t\trise_intrinsic_delay: " + str(self.cell_rise_intrinsic) \
                + "\n\t\t\trise_slope: " + str(self.cell_rise_slope) \
                + "\n\t\t\tfall_constraint: " + str(self.fall_constraint) \
                + "\n\t\t\trise_constraint: " + str(self.rise_constraint) + "\n"

    def set_delay_value (self, rise_or_fall, intrinsic, slope):
        if rise_or_fall == 'fall':
            self.cell_fall_intrinsic, self.cell_fall_slope = intrinsic, slope
        else:
            self.cell_rise_intrinsic, self.cell_rise_slope = intrinsic, slope

    def set_constraint_value (self, rise_or_fall, value):
        if rise_or_fall == 'fall':
            self.fall_constraint = value
        else:
            self.rise_constraint = value


def is_tie(gate_type):
    return True if gate_type.startswith('TIE') else False


def is_latch(gate_type):
    return True if gate_type.startswith('DFF') else False


def strip_unnecessary_char(token):
    char = ('"', '(', ')', ';', ',')
    for c in char:
        token = token.replace(c, '')
    return token


def parse_pin_info(lines_iter, pin):
    parse_level = 0;

    while True:
        line = next(lines_iter)
        tokens = line.split()

        if tokens[-1] == "{":
            parse_level += 1
        elif tokens[-1] == "}":
            parse_level -= 1
            if parse_level < 0:
                return

        if tokens[0] == 'direction':
            pin.direction = tokens[2].replace(';', '')

        elif tokens[0] == 'function':
            pin.function = ''.join([t.replace('"', '') for t in tokens[2:]])
            pin.function = pin.function.replace(';', '')

        elif tokens[0] == 'capacitance':
            try:
                pin.capacitance = float(strip_unnecessary_char(tokens[2]))
            except UnboundLocalError:
                pass

        elif tokens[0] == 'max_capacitance':
            pin.max_capacitance = float(tokens[2].replace(';', ''))
        elif tokens[0] == 'min_capacitance':
            pin.min_capacitance = float(tokens[2].replace(';', ''))

        elif tokens[0] == 'timing':
            pin.timing_info_list.append(LibertyPinTimingInfo())
            cur_timing_info = pin.timing_info_list[-1]
            parse_timing_info(lines_iter, cur_timing_info)
            parse_level -= 1

        # DFF
        elif tokens[0] == 'clock':
            is_clock = strip_unnecessary_char(tokens[2])
            pin.is_clock = True if is_clock == "true" else False

        elif tokens[0] == 'nextstate_type':
            pass

        else:
            pass

def parse_timing_info(lines_iter, timing_info):
    parse_level = 0;

    while True:
        line = next(lines_iter)
        tokens = line.split()

        if tokens[-1] == "{":
            parse_level += 1;
        elif tokens[-1] == "}":
            parse_level -= 1;
            if parse_level < 0:
                return

        if tokens[0].startswith(('cell_fall', 'cell_rise')):
            # Pick the third row of the table --> third index of the transition time
            # Load delay: the first element
            # Slope =  (2nd_delay - 1st_delay) / (2nd_cap - 1st_cap)
            offset = tokens[0].find('_') + 1
            delay_type = tokens[0][offset:offset+4] # rise/fall
            cap_list = [next(lines_iter) for _ in range(2)][-1].lstrip().split(',')
            delay_list = [next(lines_iter) for _ in range(3)][-1].lstrip().split(',')

            cap_1 =   float(cap_list[0].lstrip('index_2 ("'))
            cap_2 =   float(cap_list[1].rstrip('");'))
            delay_1 = float(delay_list[0].lstrip('"'))
            delay_2 = float(delay_list[1].rstrip('"'))

            intrinsic = delay_1
            slope = (delay_2 - delay_1) / (cap_2 - cap_1)

            timing_info.set_delay_value( delay_type, intrinsic, slope )

        # Timing table - constraint (setup, hold for seq elements)
        elif tokens[0].startswith(('fall_constraint', 'rise_constraint')):
            if timing_info.timing_type == 'min_pulse_width':
                continue
            # Pick the (0,0) element -- currently I don't have any criteria
            offset = tokens[0].find('_') + 1
            delay_type = tokens[0][0:offset-1]
            if tokens[1] == "scalar":   # ICCAD benchmark
                tokens = next(lines_iter).split()
                delay = float(tokens[3])
            else:
                continue
                # delay_list = [next(lines_iter) for _ in range(3)][-1].lstrip().split(',')
                # delay = float(delay_list[0].lstrip('values ("'))

            timing_info.set_constraint_value( delay_type, delay )

        elif tokens[0] == 'timing_sense':
            timing_sense = strip_unnecessary_char(tokens[2])
            timing_info.timing_sense = timing_sense

        elif tokens[0] == 'related_pin':
            related_pin = strip_unnecessary_char(tokens[2])
            timing_info.related_pin = related_pin

        else:
            pass


def parse_liberty_text(lines_iter, lef=None):
    """ Parse liberty library and get information to generate genlib gates. """
    gate_list = list()

    try:    # Start parsing
        for line in lines_iter:
            tokens = line.split()

            if len(tokens) < 2: continue

            """ Library information """
            if tokens[0] == 'process_corner':
                LibertyLibraryInfo.pvt[0] = tokens[2]
            elif tokens[0] == 'voltage':
                LibertyLibraryInfo.pvt[1] = tokens[2]
            elif tokens[0] == 'temperature':
                LibertyLibraryInfo.pvt[2] = tokens[2]

            elif tokens[0] == 'time_unit':
                LibertyLibraryInfo.units[0] = "1ps"
                time_unit = strip_unnecessary_char(tokens[2])

            elif tokens[0] == 'leakage_power_unit':
                LibertyLibraryInfo.units[1] = strip_unnecessary_char(tokens[2])
            elif tokens[0] == 'voltage_unit':
                LibertyLibraryInfo.units[2] = strip_unnecessary_char(tokens[2])
            elif tokens[0] == 'current_unit':
                LibertyLibraryInfo.units[3] = strip_unnecessary_char(tokens[2])
            elif tokens[0] == 'pulling_resistance_unit':
                LibertyLibraryInfo.units[4] = strip_unnecessary_char(tokens[2])
            elif tokens[0] == 'capacitive_load_unit':
                LibertyLibraryInfo.units[5] = tokens[1]

            elif tokens[0] == 'cell':
                name = strip_unnecessary_char(tokens[1])
                type_str = name[:name.find(FUNCTION_DELIM)]

                if is_tie(type_str):
                    while True: # Find valid cell
                        tokens = next(lines_iter).split()
                        try:
                            if tokens[0] == 'cell':
                                name = strip_unnecessary_char(tokens[1])
                                type_str = name[:name.find(FUNCTION_DELIM)]
                                if is_tie(type_str) == False:
                                    break
                        except IndexError: 
                            continue

                gate_type = "LATCH" if is_latch(name[:name.find(FUNCTION_DELIM)]) else "GATE"
                gate_list.append( LibertyGate(name, gate_type) )

                if lef is not None:
                    gate_list[-1].area = area_dict[name]
                else:
                    gate_list[-1].area = 0.0

            elif tokens[0] == 'area':   # ICCAD lib doesn't have area information
                gate_list[-1].area = float(tokens[2].replace(';', ''))

            elif tokens[0] == 'pin':    # name of the pin
                pin_string = strip_unnecessary_char(tokens[1])
                gate_list[-1].add_pin( LibertyPin(pin_string) )
                cur_pin = gate_list[-1].pin_list[-1]

                parse_pin_info(lines_iter, cur_pin)

    except StopIteration:
        pass

    return gate_list


# Genlib.py
class GenlibGate(object):
    """ Genlib gate """
    def __init__(self, name, area, function, gate_type='GATE'):
        self.name, self.area, self.function, self.gate_type \
            = name, area, function, gate_type
        self.pin_list = list()

    def print_gate(self):
        print ("%s %s %.4f %s;" \
                % (self.gate_type, self.name, self.area, self.function))
        [print ("\t" + p.__str__()) for p in self.pin_list if not p.is_output]
        print ("")


class GenlibLatch(GenlibGate):
    """ Genlib latch """
    def __init__(self, name, area, function, gate_type='LATCH'):
        super(self.__class__, self).__init__(name, area, function, gate_type)
        self.constraint_list = list()

    def print_gate(self):
        print ("# %s %s %.4f %s;" \
                % (self.gate_type, self.name, self.area, self.function))
        [print ("\t" + p.__str__()) for p in self.pin_list if not p.is_output]
        [print ("\t" + c.__str__()) for c in self.constraint_list[:-1]]
        print ("")


class GenlibPin(object):
    """ Genlib pin """
    def __init__(self, name, input_load=0.0, max_load=999.0, is_output=False):
        self.name, self.input_load, self.max_load = name, input_load, max_load
        self.is_output = is_output

        self.phase = ''
        self.rise_delay = 0.0
        self.rise_slope = 0.0
        self.fall_delay = 0.0
        self.fall_slope = 0.0

    def __str__(self):
        return ("PIN %s %s %.4f %.4f %.4f %.4f %.4f %.4f" % \
                (self.name, self.phase, \
                 self.input_load, self.max_load, \
                 self.rise_delay, self.rise_slope, \
                 self.fall_delay, self.fall_slope))


# For latches
class GenlibSeqPin(GenlibPin):
    """ Genlib SEQ pin """
    def __init__(self, name, input_load=0.0, max_load=999.0, is_output=False):
        super(self.__class__, self).__init__(name, input_load, max_load, is_output)
        self.is_output = True
        self.latch_type = ''

    def __str__(self):
        return ("SEQ %s ANY %s" % (self.name, self.latch_type))


class GenlibControlPin(GenlibPin):
    """ Genlib CONTROL pin """
    def __init__(self, name, input_load=0.0, max_load=999.0, is_output=False):
        super(self.__class__, self).__init__(name, input_load, max_load, is_output)
        self.is_clock_pin = True

    def __str__(self):
        return ("CONTROL %s %.4f 999.9999 %.4f %.4f %.4f %.4f" % \
                    (self.name, self.input_load, \
                     self.rise_delay, self.rise_slope, \
                     self.fall_delay, self.fall_slope))


class Constraint(object):
    """ Genlib CONSTRAINT statement """
    def __init__(self, name, setup_time, hold_time):
        self.pin_name = name
        self.setup_time = 0.0
        self.hold_time = 0.0

    def __str__(self):
        return ("CONSTRAINT %s %.4f %.4f" % \
                    (self.name, self.setup_time, self.hold_time))


def generate_genlib_gate(liberty_gate):
    """ Generate a GenlibGate object from the given LibertyGate.
    Currently, this function only handles combinational gates. """
    name, area, gate_type = liberty_gate.name, liberty_gate.area, \
                            liberty_gate.gate_type

    if gate_type == "GATE":        # If a combinational gate
        # The function will be populated later.
        cur_gate = GenlibGate(name, area, "")
        pin_list = cur_gate.pin_list

        # Create pin
        opins = [p for p in liberty_gate.pin_list if p.direction == "output"]
        assert len(opins) == 1

        function = "{0} = {1}".format(opins[0].name, opins[0].function)
        cur_gate.function = function

        for p in liberty_gate.pin_list:
            name, direction, capacitance = p.name, p.direction, p.capacitance

            pin_list.append( GenlibPin(name, capacitance) )
            cur_pin = pin_list[-1]

            if direction == 'output':
                cur_pin.is_output = True
                max_load = p.max_capacitance
                timing_info_list = p.timing_info_list

        # Extract timing information
        timing_info_dict = dict()

        for t in timing_info_list:
            related_pin = t.related_pin
            timing_sense = t.timing_sense
            rise = (t.cell_rise_intrinsic, t.cell_rise_slope)
            fall = (t.cell_fall_intrinsic, t.cell_fall_slope)

            if related_pin in timing_info_dict:
                timing_info_dict[related_pin].append( (timing_sense, rise, fall) )
            else:
                timing_info_dict[related_pin] = [ (timing_sense, rise, fall) ]

        for input_pin_name, timing_info in timing_info_dict.items():
            input_pin = [p for p in cur_gate.pin_list if p.name == input_pin_name][0]

            input_pin.max_load = max_load
            # Timing sense
            timing_sense = [i[0] for i in timing_info]
            if set(timing_sense).__len__() == 2: input_pin.phase = 'UNKNOWN'
            elif timing_sense[0] == 'positive_unate': input_pin.phase = 'NONINV'
            elif timing_sense[0] == 'negative_unate': input_pin.phase = 'INV'
            else: input_pin.phase = 'UNKNOWN'

            # Rise/fall delay
            rise = max([i[1] for i in timing_info], key=lambda x: x[0])
            fall = max([i[2] for i in timing_info], key=lambda x: x[0])

            (input_pin.rise_delay, input_pin.rise_slope) = rise
            (input_pin.fall_delay, input_pin.fall_slope) = fall

    else:
        cur_gate = GenlibLatch(name, area, "Q=D")
        # Add pins and constraints

    return cur_gate


def create_genlib(src, dest, lef):
    # Open file
    lines = [x.strip() for x in open(src, 'r')]

    liberty_gate_list = parse_liberty_text(iter(lines), lef)

    print("Num liberty gates: %d" % len(liberty_gate_list))
    genlib_gate_list = [generate_genlib_gate(i) for i in liberty_gate_list]

    stdout = sys.stdout
    sys.stdout = open(dest, 'w')

    #[print (g) for g in liberty_gate_list]
    # Write genlib
    print ('#-----------------------------------------------------------------------------#')
    print ('# Generated by create_genlib_iccad15.py, ' + strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    print ('#     Liberty:  ' + src)
    print ('#     PVT corners:  ' + ', '.join([i.rstrip(';') for i in LibertyLibraryInfo.pvt]))
    print ('#     Units:  ' + ', '.join([i.rstrip(';') for i in LibertyLibraryInfo.units]))
    print ('#-----------------------------------------------------------------------------#')
    print ("# A combinatorial gate is specified in the following format:")
    print ("#   GATE <cell-name> <cell-area> <cell-logic-function>")
    print ("#   <pin-info>")
    print ("#   ...")
    print ("#   <pin-info>")
    print ("")
    print ("# Each pin-info has the following format:")
    print ("# PIN <pin-name> <phase> <input-load> <max-load> \\")
    print ("#     <rise-block-delay> <rise-fanout-delay> <fall-block-delay> <fall-fanout-delay>")

    print ("\n# Combinatorial gates")
    [g.print_gate() for g in genlib_gate_list if g.gate_type == "GATE"]
    print ("\n# Sequential gates")
    [g.print_gate() for g in genlib_gate_list if g.gate_type == "LATCH"]

    print ("\n#--")
    print ("GATE zero 0 o=CONST0;")
    print ("GATE one 0 o=CONST1;")
    print ("")


if __name__ == '__main__':
    opt = parse_cl()

    src = opt.src_lib
    dest = opt.dest_genlib
    if opt.lef is None:
        print("Warning: Gates may have no area information.")
    lef = opt.lef

    print ("Input file:  " + src)
    print ("Output file: " + dest)

    create_genlib(src, dest, lef)

