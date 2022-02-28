import sys, argparse
from parser import parse_info, parse_constraints

def main(args):
    # parse design info (ex: riscv_soc_io.rep)
    info = parse_info(args.design_info)
    # parse tech constraint (ex: tech_const_1.txt)
    constraints = parse_constraints(args.tech_const)

    print (info)
    print (constraints)

    # TODO:
    #       1. calculate the number of bumps required
    #       2. basically change the floorPlan and the create_bump command

    # want most compact area, calculate bump current with min area
    currPerBump = constraints['bumpPitchSoC'] * constraints['bumpPitchSoC'] # um^2
    currPerBump = currPerBump * 1e-8 * constraints['currDen']               # um^2 to cm^2 to A
    targetCurr = info['designPower'] / 1.0                                  # VDD is 1.0,
    nBumps = targetCurr // currPerBump + 1
    print ('currPerBump', currPerBump)
    print ('targetCurr', targetCurr)
    print ('nBumps (power)', nBumps)

    # 1:1 power, ground bump plus io bumps
    nBumps = nBumps * 2 + info['ioCount']
    print ('nBumps (after pg and io)', nBumps)

    fp_tcl = '''
# utilization
set UTIL {1}

# Read floorplan
floorPlan -site FreePDK45_38x28_10R_NP_162NW_34O -s 400.0 400.0 40.2 40.2 40.2 40.2

# Place TSVs
source "scripts_own/riscv_f2f_tsv.tcl"

# Flip-Chip Flow
# Create bumps on across the die
create_bump -cell BUMPCELL_TSV -pitch {{{0} {0}}} -loc {{20 20}} -pattern_array {{24 24}}
# Assign them to IO cells
assignBump
# Assign unused bumps to power nets
assignPGBumps -nets {{VDD VSS}} -floating -checkerboard
#
# RDL Routing between IO cells and bumps
# This is currently broken due to the IO/TSV LEF model obstructions. Will be fixed soon.
#setFlipChipMode -route_style 45DegreeRoute
#fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0
'''.format(constraints['bumpPitchF2F'], info['targetUtil'])
    print (fp_tcl)


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--design-info', required=True, type=str)
    parser.add_argument('--tech-const', required=True, type=str)
    return parser.parse_args()

if __name__ == '__main__':
    main(parse())
