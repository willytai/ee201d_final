import sys, argparse
import math
from parser import parse_info, parse_constraints

def main(args):
    # parse design info (ex: riscv_soc_io.rep)
    info = parse_info(args.design_info)
    # parse tech constraint (ex: tech_const_1.txt)
    constraints = parse_constraints(args.tech_const)

    ################
    # for IO bumps #
    ################
    # give an pessimistic estimation of how many IO bumps are required per side
    # round up
    ioCellNumPerSide = info['ioCount'] // 4
    if abs(info['ioCount']/4.0 - ioCellNumPerSide) > 1e-6: ioCellNumPerSide += 1


    ################
    # for PG bumps #
    ################
    # want most compact area, calculate bump current with min area
    # this calculates the min bumps required to satisfy the power and current density constraints
    currPerBump = constraints['bumpPitchSoC'] * constraints['bumpPitchSoC'] # um^2
    currPerBump = currPerBump * 1e-8 * constraints['currDen']               # um^2 to cm^2 to A
    targetCurr = info['designPower'] / 1.0                                  # VDD is 1.0,
    pgBumps = targetCurr // currPerBump + 1
    if pgBumps == 1: pgBumps += 1
    # 1:1 pgBumps
    pgBumps *= 2
    # find the smallest square value that is greater than pgBumps
    pgBumpsRow = math.sqrt(pgBumps)
    if abs(int(pgBumpsRow)-pgBumpsRow) > 1e-6: pgBumpsRow += 1
    pgBumpsRow = int(pgBumpsRow)
    pgBumpsCol = int(pgBumpsRow)


    #################
    # for floorplan #
    #################
    # spacing to fit IO cells
    spacing = constraints['ioCellHeight'] * 2
    # raw dimension (including io boundary)
    rawDim = math.ceil(math.sqrt(info['designArea']))
    # core dimension (subtract spacing)
    coreDim = rawDim - spacing


    ####################
    # final tcl script #
    ####################
    fp_tcl = '''# utilization
set UTIL {0}

#############
# floorPlan #
#############
floorPlan -site FreePDK45_38x28_10R_NP_162NW_34O -s {1} {1} {2} {2} {2} {2}
floorPlan -keepShape $UTIL

################
# for IO bumps #
################
set ioCellNumX {3}
set ioCellNumY {3}
set ioBumpBudgetX [expr [dbGet top.fPlan.box_sizex]-2.1*{4}]
set ioBumpBudgetY [expr [dbGet top.fPlan.box_sizey]-2.1*{4}]
set ioBumpPitchX [max {5} [expr $ioBumpBudgetX / [expr $ioCellNumX-1.0]]]
set ioBumpPitchY [max {5} [expr $ioBumpBudgetY / [expr $ioCellNumY-1.0]]]

# recalculate pitch so that bumps distribute evenly
set ioBumpPitchX [expr $ioBumpBudgetX / [expr floor($ioBumpBudgetX / $ioBumpPitchX)]]
set ioBumpPitchY [expr $ioBumpBudgetY / [expr floor($ioBumpBudgetY / $ioBumpPitchY)]]

# create IO bumps
set ioMarginX {4}
set ioMarginY {4}
create_bump -cell BUMPCELL -pitch [list [expr $ioBumpPitchX] [expr $ioBumpPitchY]] -pattern_side [list left [expr $ioBumpBudgetX / $ioBumpPitchX + 1]] \\
            -edge_spacing [list [expr $ioMarginX] [expr $ioMarginY] [expr $ioMarginX] [expr $ioMarginY]]

# assign IO bumps and delete the floating bumps
assignBump
deleteBumps -floating


################
# for PG bumps #
################
create_bump -cell BUMPCELL -pitch [list [expr $ioBumpPitchX] [expr $ioBumpPitchY]] -pattern_center {{{6} {7}}}
assignPGBumps -nets {{VDD VSS}} -floating -checkerboard


##########################################
# RDL Routing between IO cells and bumps #
##########################################
setFlipChipMode -route_style 45DegreeRoute
fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0
'''.format(info['targetUtil'],
           coreDim,
           spacing,
           ioCellNumPerSide,
           constraints['ioCellHeight'],
           constraints['bumpPitchSoC'],
           pgBumpsRow,
           pgBumpsCol)

    return fp_tcl


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--design-info', required=True, type=str)
    parser.add_argument('--tech-const', required=True, type=str)
    return parser.parse_args()

if __name__ == '__main__':
    with open('fp_soc.tcl', 'w') as f:
        f.write(main(parse()))
