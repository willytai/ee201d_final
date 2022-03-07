import argparse, os
import math
from parser import parse_info, parse_constraints

def soc(design_info, tech_const, script_dir):
    # parse design info (ex: riscv_soc_io.rep)
    info = parse_info(design_info)
    # parse tech constraint (ex: tech_const_1.txt)
    constraints = parse_constraints(tech_const)


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
    print (f'{pgBumps=}')


    #################
    # for floorplan #
    #################
    minTotalBumps = pgBumps + info['ioCount']
    minSize4Bumps = math.sqrt(minTotalBumps)
    if abs(int(minSize4Bumps)-minSize4Bumps) > 1e-6: minSize4Bumps += 1
    minArea1 = ((minSize4Bumps-1)*constraints['bumpPitchSoC'])**2
    # spacing to fit IO cells
    minSpacing = constraints['ioCellHeight']*2
    targetCoreSize = math.ceil(math.sqrt(info['designArea']/info['targetUtil']))
    coreDim = round(targetCoreSize)
    minArea2 = (coreDim+minSpacing*2)**2
    finalArea = max(minArea1, minArea2)
    spacing = round((math.sqrt(finalArea)-coreDim)/2, 2)
    print (f'{coreDim=}')
    print (f'{spacing=}')


    ###############
    # bump script #
    ###############
    dieDim = coreDim + spacing*2 - constraints['ioCellHeight']*0.5
    pitch = constraints['bumpPitchSoC']
    bumpPerSide = 2
    while (bumpPerSide-1)*pitch < dieDim:
        bumpPerSide += 1
    bumpPerSide -= 1
    pitch = math.floor(dieDim / (bumpPerSide -1) * 100) / 100
    bumpTcl = '''\
create_bump -cell BUMPCELL -pitch [list {0} {0}] -pattern_side [list left {1}]\\
            -edge_spacing [list [expr {2}] [expr {2}] [expr {2}] [expr {2}]]'''.format(pitch, bumpPerSide, constraints['ioCellHeight'])
    print (f'{bumpPerSide=}')


    ####################
    # final tcl script #
    ####################
    fp_tcl = '''\
#############
# floorPlan #
#############
floorPlan -site FreePDK45_38x28_10R_NP_162NW_34O -s {0} {0} {1} {1} {1} {1}

#############
# for bumps #
#############
{2}
assignBump
assignPGBumps -nets {{VDD VSS}} -floating -checkerboard


##########################################
# RDL Routing between IO cells and bumps #
##########################################
setFlipChipMode -route_style 45DegreeRoute
fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0
'''.format(coreDim,
           spacing,
           bumpTcl)

    with open(os.path.join(script_dir, 'fp_soc.tcl'), 'w') as f:
        f.write(fp_tcl)

    return finalArea, constraints['defectDens']


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--design-info', required=True, type=str)
    parser.add_argument('--tech-const', required=True, type=str)
    parser.add_argument('--script-dir', required=False, type=str, default='./')
    return parser.parse_args()

def main(args):
    return soc(args.design_info, args.tech_const, args.script_dir)

if __name__ == '__main__':
    finalArea, defectDensity = main(parse())
    print ('Die Area: {} (um^2)'.format(finalArea))
    print ('Defect Density: {} (per cm^2)'.format(defectDensity))
