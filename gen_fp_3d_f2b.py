import sys, argparse, math, os
from parser import parse_info, parse_constraints
from gen_tsv_f2b import box, TSVWIDTH, TSV2ioCellSpacingRatio, TSV2CoreBoxSpacingRatio


def tsvTCL(tsvPool, tsvPitch, spacing, pgTSVs, start, dieDim, coreDim, ioCellHeight):
    # boundary
    endx, endy = dieDim - start, dieDim - start
    startx, starty = start, start
    # forbidden box (core area)
    forbidden = box(spacing+ioCellHeight, spacing+ioCellHeight, coreDim)

    # helper function
    # state: right, up, left, down
    #        0      1   2     3
    def nextPos(x, y, state, startx, starty, endx, endy):
        if state == 0:
            x += tsvPitch
        elif state == 1:
            y += tsvPitch
        elif state == 2:
            x -= tsvPitch
        elif state == 3:
            y -= tsvPitch
        # check if valid
        if x+TSVWIDTH > endx:
            x -= tsvPitch
            state = 1
            return nextPos(x, y, state, startx, starty, endx, endy)
        if y+TSVWIDTH > endy:
            y -= tsvPitch
            state = 2
            return nextPos(x, y, state, startx, starty, endx, endy)
        if x < startx:
            x += tsvPitch
            state = 3
            return nextPos(x, y, state, startx, starty, endx, endy)
        if y <= starty and state == 3:
            startx, starty = startx+tsvPitch, starty+tsvPitch
            endx, endy = endx-tsvPitch, endy-tsvPitch
            x, y = startx, starty
            state = 0
        if forbidden.contains(x, y) or forbidden.contains(x+TSVWIDTH, y) or forbidden.contains(x, y+TSVWIDTH) or forbidden.contains(x+TSVWIDTH, y+TSVWIDTH):
            print (x, y, 'is contained in', forbidden)
            raise ValueError
        return x, y, state, startx, starty, endx, endy
    
    tsvCount = 0
    tsvTcl = ''
    uBumpTcl = ''
    x, y = startx-tsvPitch, starty
    state = 0
    for tsv in tsvPool:
        x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
        tsvTcl += 'placeInstance {} {} {} -placed\n'.format(tsv, x-TSVWIDTH/2, y-TSVWIDTH/2)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -loc {} {}\n'.format(x, y)
        tsvCount += 1

    # required pg tsv and ubumps
    uniqueID = 0
    for _ in range(0, pgTSVs, 2):
        x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
        tsvTcl += 'addInst -cell TSVD_IN -inst ptsv{} -loc {{{} {}}} -status placed\n'.format(uniqueID, x-TSVWIDTH/2, y-TSVWIDTH/2)
        tsvTcl += 'globalNetConnect VDD -type pgpin -sinst ptsv{} -pin in\n'.format(uniqueID)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format pubump{} -loc {} {}\n'.format(uniqueID, x, y)
        uniqueID += 1
        tsvCount += 1

        x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
        tsvTcl += 'addInst -cell TSVD_IN -inst gtsv{} -loc {{{} {}}} -status placed\n'.format(uniqueID, x-TSVWIDTH/2, y-TSVWIDTH/2)
        tsvTcl += 'globalNetConnect VSS -type pgpin -sinst gtsv{} -pin in\n'.format(uniqueID)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format gubump{} -loc {} {}\n'.format(uniqueID, x, y)
        uniqueID += 1
        tsvCount += 1

    # fill the rest of the space with pg tsvs (no harm)
    # harms yield
    # try:
    #     ctype = 'p'
    #     while True:
    #         x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
    #         tsvTcl += 'addInst -cell TSVD_IN -inst {}tsv{} -loc {{{} {}}} -status placed\n'.format(ctype, uniqueID, x-TSVWIDTH/2, y-TSVWIDTH/2)
    #         tsvCount += 1
    #         if ctype == 'p':
    #             tsvTcl += 'globalNetConnect VDD -type pgpin -sinst ptsv{} -pin in\n'.format(uniqueID)
    #         else:
    #             tsvTcl += 'globalNetConnect VSS -type pgpin -sinst gtsv{} -pin in\n'.format(uniqueID)
    #         uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format {}ubump{} -loc {} {}\n'.format(ctype, uniqueID, x, y)
    #         uniqueID += 1
    #         if ctype == 'p': ctype = 'g'
    #         else: ctype = 'p'
    # except Exception as e:
    #     pass

    return tsvTcl, uBumpTcl, tsvCount


def f2b(design_info_bot, design_info_top, tech_const, design_netlist, script_dir):
    botInfo = parse_info(design_info_bot)
    topInfo = parse_info(design_info_top)
    constraints = parse_constraints(tech_const)
    bumpPitch = constraints['bumpPitchSoC']
    tsvPitch = constraints['tsvPitchF2B']
    ioCellHeight = constraints['ioCellHeight']
    margin = 30


    ##################
    # core area size #
    ##################
    # found to multiple of bump pitch
    botCoreArea = botInfo['designArea'] / botInfo['targetUtil']
    topCoreArea = topInfo['designArea'] / topInfo['targetUtil']
    targetCoreSize = math.sqrt(max(botCoreArea, topCoreArea))
    coreDim = math.ceil(targetCoreSize / bumpPitch) * bumpPitch
    print (f'{coreDim=}')


    #########
    # bumps #
    #########
    # want most compact area, calculate bump current with min area
    # this calculates the min bumps required to satisfy the power and current density constraints
    # bottom die needs to provide power to the top die
    currPerBump = constraints['bumpPitchSoC'] * constraints['bumpPitchSoC'] # um^2
    currPerBump = currPerBump * 1e-8 * constraints['currDen']               # um^2 to cm^2 to A
    targetCurr = (botInfo['designPower']+topInfo['designPower']) / 1.0      # VDD is 1.0,
    pgBumps = targetCurr // currPerBump + 1
    if pgBumps == 1: pgBumps += 1
    # 1:1 pgBumps
    pgBumps = int(pgBumps * 2)
    ioBumps = botInfo['ioCount']
    minTotalBumps = pgBumps + ioBumps
    # round total bumps to a square value
    finalTotalBumps = int(math.ceil(math.sqrt(minTotalBumps)) ** 2)
    bumpsPerSide = int(math.sqrt(finalTotalBumps))
    print (f'{pgBumps=}')
    print (f'{ioBumps=}')
    print (f'{minTotalBumps=} (pgBumps + ioBumps)')
    print (f'{finalTotalBumps=} (to square value)')
    print (f'{bumpsPerSide=}')


    ############
    # die size #
    ############
    dieDim = (bumpsPerSide - 1)*bumpPitch + 2*margin
    while dieDim < coreDim:
        bumpsPerSide += 1
        dieDim += bumpPitch
    print (f'{bumpsPerSide=} (after die size adjustment)')
    print (f'{dieDim=}')


    ###############
    # for PG TSVs #
    ###############
    # these TSVs need to provide power to the top die
    currPerTSV = constraints['tsvPitchF2B'] * constraints['tsvPitchF2B'] # um^2
    currPerTSV = currPerTSV * 1e-8 * constraints['currDen']              # um^2 to cm^2 to A
    targetCurr = topInfo['designPower'] / 1.0                            # VDD is 1.0,
    pgTSVs = targetCurr // currPerTSV + 1
    if pgTSVs == 1: pgTSVs += 1
    # 1:1 pgTSVs
    pgTSVs = int(pgTSVs * 2)
    print (f'{pgTSVs=}')


    #################
    # for floorplan #
    #################
    # increase dieDim by bumpPitch each round until all TSV fits
    tsvPool = list()
    with open(design_netlist, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV_'):
                tsvModule = line.split()[1]
                tsvName = tsvModule.split('(')[0]
                tsvPool.append(tsvName)
    flag = True
    while flag:
        try:
            print (f'{bumpsPerSide=} {dieDim=}')
            flag = False
            spacing = (dieDim - coreDim - 2*ioCellHeight) / 2
            tsvTcl, uBumpTcl, tsvCount = tsvTCL(tsvPool, tsvPitch, spacing, pgTSVs, margin, dieDim, coreDim, ioCellHeight)
        except Exception as e:
            flag = True
            dieDim += bumpPitch
            bumpsPerSide += 1
    finalArea = dieDim**2
    print (f'{spacing=}')


    ############################
    # Gen TSV and ubump script #
    ############################
    with open(os.path.join(script_dir, 'riscv_core_tsv_f2b.tcl'), 'w') as f:
        f.write('{}'.format(tsvTcl))
    with open(os.path.join(script_dir, 'riscv_core_ubump_f2b.tcl'), 'w') as f:
        f.write('{}'.format(uBumpTcl))


    ###############
    # bump script #
    ###############
    bumpTcl = 'create_bump -cell BUMPCELL -pitch [list {0} {0}] -pattern_array [list {1} {1}] -loc [list {2} {2}]'.format(bumpPitch, bumpsPerSide, margin)


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
source "scripts_own/riscv_core_tsv_f2b.tcl"


#############
# for bumps #
#############
{2}
# assign IO bumps
# the remaining floating bumps are guaranteed to be sufficient for pgBumps since the area is already pre-calculated
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

    fp_tcl_top = '''\
#############
# floorPlan #
#############
floorPlan -site FreePDK45_38x28_10R_NP_162NW_34O -s {0} {0} {1} {1} {1} {1}

##############
# Place TSVs #
##############
source "scripts_own/riscv_core_tsv_f2b.tcl"

##############
# for ubumps #
##############
source "scripts_own/riscv_core_ubump_f2b.tcl"
assignPGBumps -nets {{VDD}} -bumps {{pubump*}}
assignPGBumps -nets {{VSS}} -bumps {{gubump*}}
assignBump

##########################################
# RDL Routing between IO cells and bumps #
##########################################
setFlipChipMode -route_style 45DegreeRoute
fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0
'''.format(coreDim,
           spacing)

    with open(os.path.join(script_dir, 'fp_3d_f2b_bottom.tcl'), 'w') as f:
        f.write(fp_tcl_bot)
    with open(os.path.join(script_dir, 'fp_3d_f2b_top.tcl'), 'w') as f:
        f.write(fp_tcl_top)

    # return finalArea, defectDensity, tsvCount, wireBonds
    return finalArea, constraints['defectDens'], tsvCount, botInfo['ioCount']


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--design-info-bot', required=True, type=str)
    parser.add_argument('--design-info-top', required=True, type=str)
    parser.add_argument('--design-netlist', required=True, type=str)
    parser.add_argument('--tech-const', required=True, type=str)
    parser.add_argument('--script-dir', required=False, type=str, default='./')
    return parser.parse_args()

def main(args):
    return f2b(args.design_info_bot, args.design_info_top, args.tech_const, args.design_netlist, args.script_dir)

if __name__ == '__main__':
    finalArea, defectDensity, tsvCount = main(parse())
    print ('Bot Die Area: {} (um^2)'.format(finalArea))
    print ('Top Die Area: {} (um^2)'.format(finalArea))
    print ('Total TSVs: {}'.format(tsvCount))
    print ('Defect Density: {} (per cm^2)'.format(defectDensity))

