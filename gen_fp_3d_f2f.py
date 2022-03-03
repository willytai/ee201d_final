import sys, argparse, math
from parser import parse_info, parse_constraints
from gen_tsv_f2b import tsvTCL, TSVWIDTH, TSV2ioCellSpacingRatio, TSV2CoreBoxSpacingRatio


def main(args):
    botInfo = parse_info(args.design_info_bot)
    topInfo = parse_info(args.design_info_top)
    constraints = parse_constraints(args.tech_const)


    #######################
    # for to-top-die TSVs #
    #######################
    # give an pessimistic estimation of how many ubumps are required per side for connecting tsvs
    # at most 2 level
    # round up
    ubumpPerSide = botInfo['tsvCount'] // 4
    if abs(botInfo['tsvCount']/4.0 - ubumpPerSide) > 1e-6: ubumpPerSide += 1
    ubumpPerSide = math.ceil(ubumpPerSide * 0.9)
    print ('ubumpPerSide', ubumpPerSide)


    #################
    # for PG ubumps #
    #################
    # want most compact area, calculate bump current with min area
    # this calculates the min bumps required to satisfy the power and current density constraints
    # these bumps provide power to the top die in f2f flow
    currPerBump = constraints['bumpPitchF2F'] * constraints['bumpPitchF2F'] # um^2
    currPerBump = currPerBump * 1e-8 * constraints['currDen']               # um^2 to cm^2 to A
    targetCurr = topInfo['designPower'] / 1.0                               # VDD is 1.0,
    pgBumps = targetCurr // currPerBump + 1
    if pgBumps == 1: pgBumps += 1
    # 1:1 pgBumps
    pgBumps *= 2
    print ('pgBumps', pgBumps)


    ###############
    # for PG TSVs #
    ###############
    # these TSVs need to provide power to the bottom and top die
    currPerTSV = constraints['tsvPitchF2F'] * constraints['tsvPitchF2F'] # um^2
    currPerTSV = currPerTSV * 1e-8 * constraints['currDen']              # um^2 to cm^2 to A
    targetCurr = (botInfo['designPower']+topInfo['designPower']) / 1.0   # VDD is 1.0,
    pgTSVs = targetCurr // currPerTSV + 1
    if pgTSVs == 1: pgTSVs += 1
    # 1:1 pgTSVs
    pgTSVs *= 2
    print ('pgTSVs', pgTSVs)


    #################
    # for floorplan #
    #################
    # 1. min area for min number of total bumps
    #    min area for top die ubumps
    minTotalBumps = pgBumps + botInfo['tsvCount']
    minSize4Bumps = math.sqrt(minTotalBumps)
    if abs(int(minSize4Bumps)-minSize4Bumps) > 1e-6: minSize4Bumps += 1
    minArea1 = ((minSize4Bumps-1)*constraints['bumpPitchF2F'])**2
    print ('minArea1', minArea1)
    minArea1 = max(minArea1, ((ubumpPerSide-1)*constraints['bumpPitchF2F']+20*2)**2)
    print ('minArea1', minArea1)
    # 2. find the core size which is the max of top and bot die
    botCoreArea = botInfo['designArea'] / botInfo['targetUtil']
    topCoreArea = topInfo['designArea'] / topInfo['targetUtil']
    targetCoreSize = math.ceil(math.sqrt(max(botCoreArea, topCoreArea)))
    # 3. min area for accounting for min number of tsv
    #    round core size to the min value that is greater than orgianl size and is a multiple of tsv pitch
    tmp = (targetCoreSize // constraints['tsvPitchF2F']) * constraints['tsvPitchF2F']
    targetCoreSize = tmp+constraints['tsvPitchF2F'] if tmp < targetCoreSize else tmp
    targetTSVPlaceStartSize = targetCoreSize + 2*(TSV2CoreBoxSpacingRatio*constraints['tsvPitchF2F'])
    signalIOTSVs = 0
    with open(args.design_netlist, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV_'): signalIOTSVs += 1
    totalTSVs = signalIOTSVs + pgTSVs
    poolTSVs = int(totalTSVs)
    nRings4TSV = 0
    while poolTSVs > 0:
        poolTSVs -= (4*(targetTSVPlaceStartSize//constraints['tsvPitchF2F']) - 4)
        targetTSVPlaceStartSize += 2*constraints['tsvPitchF2F']
        nRings4TSV += 1
    targetTSVPlaceStartSize -= 2*constraints['tsvPitchF2F']
    minArea2 = (targetTSVPlaceStartSize+2*TSV2ioCellSpacingRatio*constraints['tsvPitchF2F']+2*constraints['io3DCellHeight'])**2
    # 4. adjust spacing
    if minArea1 > minArea2:
        spacing = (math.sqrt(minArea1) - targetCoreSize - constraints['io3DCellHeight']) / 2
    else:
        # final spacing to fit IO cells and tsv
        spacing = constraints['tsvPitchF2F']*(nRings4TSV-1) + constraints['tsvPitchF2F']*(TSV2ioCellSpacingRatio+TSV2CoreBoxSpacingRatio)# + TSVWIDTH
    print ('minArea1', minArea1)
    print ('minArea2', minArea2)
    print (targetCoreSize)
    print (nRings4TSV)
    print (spacing)
    # 5. final floorplan dimension
    coreDim = round(targetCoreSize)

    ###############
    # bump script #
    ###############
    dieDim = coreDim + spacing*2 - (20-constraints['io3DCellHeight'])*2
    pitch = constraints['bumpPitchF2F']
    bumpPerSide = 2
    while (bumpPerSide-1)*pitch < dieDim:
        bumpPerSide += 1
    bumpPerSide -= 1
    pitch = math.floor(dieDim / (bumpPerSide -1)*10) / 10
    bumpPerSide += 1
    uBumpTcl = '''\
create_bump -cell BUMPCELL_TSV -pitch [list {0} {0}] -pattern_side [list left {1}]\\
            -edge_spacing [list [expr {2}] [expr {2}] [expr {2}] [expr {2}]]'''.format(pitch, bumpPerSide, constraints['io3DCellHeight']+14)


    ####################
    # final tcl script #
    ####################
    fp_tcl_bot = '''\
#############
# floorPlan #
#############
floorPlan -site FreePDK45_38x28_10R_NP_162NW_34O -s {0} {0} {1} {1} {1} {1}


##############
# Place TSVs #
##############
source "scripts_own/riscv_core_tsv_f2f.tcl"


##############
# for ubumps #
##############
{2}

# assign IO bumps
# the remaining floating bumps are guaranteed to be sufficient for pgBumps since the area is already pre-calculated
assignBump
assignPGBumps -nets {{VDD VSS}} -floating -V


##########################################
# RDL Routing between IO cells and bumps #
##########################################
setFlipChipMode -route_style 45DegreeRoute
fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0
'''.format(coreDim,
           spacing,
           uBumpTcl)

    fp_tcl_top = '''\
#############
# floorPlan #
#############
floorPlan -site FreePDK45_38x28_10R_NP_162NW_34O -s {0} {0} {1} {1} {1} {1}

##############
# for ubumps #
##############
{2}

# assign IO bumps
# the remaining floating bumps are guaranteed to be sufficient for pgBumps since the area is already pre-calculated
assignBump
assignPGBumps -nets {{VDD VSS}} -floating -V

##########################################
# RDL Routing between IO cells and bumps #
##########################################
setFlipChipMode -route_style 45DegreeRoute
fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0
'''.format(coreDim,
           spacing,
           uBumpTcl)

    ##################
    # Gen TSV script #
    ##################
    # 1. parse in all required TSVs
    # 2. collect them into a set and gen placement script statically
    tsvTcl, _ = tsvTCL(args.design_netlist, constraints['tsvPitchF2F'], constraints['io3DCellHeight'], coreDim, spacing, int(pgTSVs), f2b=False)
    with open('riscv_core_tsv_f2f.tcl', 'w') as f:
        f.write(tsvTcl)

    return fp_tcl_bot, fp_tcl_top


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--design-info-bot', required=True, type=str)
    parser.add_argument('--design-info-top', required=True, type=str)
    parser.add_argument('--design-netlist', required=True, type=str)
    parser.add_argument('--tech-const', required=True, type=str)
    return parser.parse_args()

if __name__ == '__main__':
    bot, top = main(parse())
    with open('fp_3d_f2f_bottom.tcl', 'w') as f:
        f.write(bot)
    with open('fp_3d_f2f_top.tcl', 'w') as f:
        f.write(top)
