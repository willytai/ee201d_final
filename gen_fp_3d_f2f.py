import argparse, math, os
from parser import parse_info, parse_constraints
from gen_tsv_f2b import box, TSVWIDTH, TSV2ioCellSpacingRatio, TSV2CoreBoxSpacingRatio
from timing_checker import genTimingCheckScript


def tsvTCL(tsvPool, tsvPitch, spacing, pgTSVs, start, dieDim, coreDim, bot=True):
    # boundary
    endx, endy = dieDim - start, dieDim - start
    startx, starty = start, start
    # forbidden box (core area)
    forbidden = box(spacing+TSVWIDTH, spacing+TSVWIDTH, coreDim)

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
    
    tsvCellType = 'TSVD_IN' if not bot else 'TSVD_OUT'
    tsvCount = 0
    tsvTcl = ''
    x, y = startx-tsvPitch, starty
    state = 0
    for tsv in tsvPool:
        x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
        tsvTcl += 'placeInstance {} {} {} -placed\n'.format(tsv, x-TSVWIDTH/2, y-TSVWIDTH/2)
        tsvCount += 1

    # required pg tsv and ubumps
    uniqueID = 0
    for _ in range(0, pgTSVs, 2):
        x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
        tsvTcl += 'addInst -cell {} -inst ptsv{} -loc {{{} {}}} -status placed\n'.format(tsvCellType, uniqueID, x-TSVWIDTH/2, y-TSVWIDTH/2)
        tsvTcl += 'globalNetConnect VDD -type pgpin -sinst ptsv{} -pin in\n'.format(uniqueID)
        uniqueID += 1
        tsvCount += 1

        x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
        tsvTcl += 'addInst -cell {} -inst gtsv{} -loc {{{} {}}} -status placed\n'.format(tsvCellType, uniqueID, x-TSVWIDTH/2, y-TSVWIDTH/2)
        tsvTcl += 'globalNetConnect VSS -type pgpin -sinst gtsv{} -pin in\n'.format(uniqueID)
        uniqueID += 1
        tsvCount += 1

    # fill the rest of the space with pg tsvs (no harm)
    # harms yield
    # try:
    #     ctype = 'p'
    #     while True:
    #         x, y, state, startx, starty, endx, endy = nextPos(x, y, state, startx, starty, endx, endy)
    #         tsvTcl += 'addInst -cell {} -inst {}tsv{} -loc {{{} {}}} -status placed\n'.format(tsvCellType, ctype, uniqueID, x-TSVWIDTH/2, y-TSVWIDTH/2)
    #         if ctype == 'p':
    #             tsvTcl += 'globalNetConnect VDD -type pgpin -sinst ptsv{} -pin in\n'.format(uniqueID)
    #         else:
    #             tsvTcl += 'globalNetConnect VSS -type pgpin -sinst gtsv{} -pin in\n'.format(uniqueID)
    #         uniqueID += 1
    #         if ctype == 'p': ctype = 'g'
    #         else: ctype = 'p'
    # except Exception as e:
    #     pass

    return tsvTcl, tsvCount


def f2f(design_info_bot, design_info_top, tech_const, design_netlist_bot, design_netlist_top, script_dir):
    botInfo = parse_info(design_info_bot)
    topInfo = parse_info(design_info_top)
    constraints = parse_constraints(tech_const)
    bumpPitch = constraints['bumpPitchF2F']
    tsvPitch = constraints['tsvPitchF2F']
    margin = 20


    ##################
    # core area size #
    ##################
    # found to multiple of bump pitch
    botCoreArea = botInfo['designArea'] / botInfo['targetUtil']
    topCoreArea = topInfo['designArea'] / topInfo['targetUtil']
    targetCoreSize = math.sqrt(max(botCoreArea, topCoreArea))
    coreDim = math.ceil(targetCoreSize / bumpPitch) * bumpPitch
    print (f'{coreDim=}')


    ##########
    # ubumps #
    ##########
    # want most compact area, calculate bump current with min area
    # this calculates the min bumps required to satisfy the power and current density constraints
    # these bumps provide power to the top die in f2f flow
    currPerBump = constraints['bumpPitchF2F'] * constraints['bumpPitchF2F'] # um^2
    currPerBump = currPerBump * 1e-8 * constraints['currDen']               # um^2 to cm^2 to A
    targetCurr = topInfo['designPower'] / 1.0                               # VDD is 1.0,
    pgBumps = targetCurr // currPerBump + 1
    if pgBumps == 1: pgBumps += 1
    # 1:1 pgBumps
    pgBumps = int(pgBumps * 2)
    ioBumps = botInfo['tsvCount']
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
    # these TSVs need to provide power to the bottom and top die
    currPerTSV = constraints['tsvPitchF2F'] * constraints['tsvPitchF2F'] # um^2
    currPerTSV = currPerTSV * 1e-8 * constraints['currDen']              # um^2 to cm^2 to A
    targetCurr = (botInfo['designPower']+topInfo['designPower']) / 1.0   # VDD is 1.0,
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
    with open(design_netlist_bot, 'r') as f:
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
            spacing = (dieDim - coreDim - 2*TSVWIDTH) / 2
            tsvTclBot, tsvCount = tsvTCL(tsvPool, tsvPitch, spacing, pgTSVs, margin, dieDim, coreDim, bot=False) # bot pgTSV gets power from subtrate (like a top layer)
        except Exception as e:
            flag = True
            dieDim += bumpPitch
            bumpsPerSide += 1
    if bumpPitch != 10:
        minSpacing = round((480.4 - coreDim)/2*10)/10
    else:
        minSpacing = spacing
    while spacing < minSpacing:
            dieDim += bumpPitch
            bumpsPerSide += 1
            print (f'{bumpsPerSide=} {dieDim=}')
            spacing = (dieDim - coreDim - 2*TSVWIDTH) / 2
            tsvTclBot, tsvCount = tsvTCL(tsvPool, tsvPitch, spacing, pgTSVs, margin, dieDim, coreDim, bot=False) # bot pgTSV gets power from subtrate (like a top layer)
    finalArea = dieDim**2
    spacing = minSpacing
    print (f'{spacing=}')


    ##############################
    # Gen pg/subtrate TSV script #
    ##############################
    with open(os.path.join(script_dir, 'riscv_core_tsv_f2f_bot.tcl'), 'w') as f:
        f.write(tsvTclBot)

    #####################
    # Gen IO TSV script #
    #####################
    # replicate placement to match connections
    # mirror the placement by x=mid
    botTSVs = list()
    topTSVs = list()
    with open(design_netlist_bot) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV'):
                tsv = line.split()[1].split('(')[0]
                if tsv[0] != 'p':
                    botTSVs.append(tsv)
    with open(design_netlist_top) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV'):
                tsv = line.split()[1].split('(')[0]
                if tsv[0] != 'p':
                    topTSVs.append(tsv)
    botTSVs = sorted(botTSVs)
    topTSVs = sorted(topTSVs)
    assert botTSVs == topTSVs
    tsvlist  = topTSVs
    botleft  = tsvlist[0:42]
    botbot   = tsvlist[42:84]
    botright = tsvlist[84:126]
    bottop   = tsvlist[126:168]
    topleft  = tsvlist[84:126]
    topright = tsvlist[0:42]
    topbot   = botbot[::-1]
    toptop   = bottop[::-1]
    tsvIObot = 'set startx [expr 0]\nset starty [expr 0]\nset endx [dbGet top.fPlan.box_urx]\nset endy [dbGet top.fPlan.box_ury]\nset ioPitchy [expr ($endy-18.0)/41]\nset ioPitchx [expr ($endx-18.0)/41]\n'
    tsvIOtop = 'set startx [expr 0]\nset starty [expr 0]\nset endx [dbGet top.fPlan.box_urx]\nset endy [dbGet top.fPlan.box_ury]\nset ioPitchy [expr ($endy-18.0)/41]\nset ioPitchx [expr ($endx-18.0)/41]\n'
    tsvIObot += 'set left {'
    tsvIOtop += 'set left {'
    for tsv in botleft: tsvIObot += f'{tsv} '
    for tsv in topleft: tsvIOtop += f'{tsv} '
    tsvIObot += '}\n'
    tsvIOtop += '}\n'
    tsvIObot += 'set right {'
    tsvIOtop += 'set right {'
    for tsv in botright: tsvIObot += f'{tsv} '
    for tsv in topright: tsvIOtop += f'{tsv} '
    tsvIObot += '}\n'
    tsvIOtop += '}\n'
    tsvIObot += 'set bot {'
    tsvIOtop += 'set bot {'
    for tsv in botbot: tsvIObot += f'{tsv} '
    for tsv in topbot: tsvIOtop += f'{tsv} '
    tsvIObot += '}\n'
    tsvIOtop += '}\n'
    tsvIObot += 'set top {'
    tsvIOtop += 'set top {'
    for tsv in bottop: tsvIObot += f'{tsv} '
    for tsv in toptop: tsvIOtop += f'{tsv} '
    tsvIObot += '}\n'
    tsvIOtop += '}\n'
    # place left
    tsvIObot += 'set xloc [expr $startx]\nset yloc [expr $starty+6.0]\n'
    tsvIObot += 'foreach tsv $left {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset yloc [expr $yloc+$ioPitchy]\n}\n'
    tsvIOtop += 'set xloc [expr $startx]\nset yloc [expr $starty+6.0]\n'
    tsvIOtop += 'foreach tsv $left {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset yloc [expr $yloc+$ioPitchy]\n}\n'
    # place right
    tsvIObot += 'set xloc [expr $endx-6.0]\nset yloc [expr $starty+6.0]\n'
    tsvIObot += 'foreach tsv $right {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset yloc [expr $yloc+$ioPitchy]\n}\n'
    tsvIOtop += 'set xloc [expr $endx-6.0]\nset yloc [expr $starty+6.0]\n'
    tsvIOtop += 'foreach tsv $right {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset yloc [expr $yloc+$ioPitchy]\n}\n'
    # place bottom
    tsvIObot += 'set xloc [expr $startx+6.0]\nset yloc [expr $starty]\n'
    tsvIObot += 'foreach tsv $bot {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset xloc [expr $xloc+$ioPitchx]\n}\n'
    tsvIOtop += 'set xloc [expr $startx+6.0]\nset yloc [expr $starty]\n'
    tsvIOtop += 'foreach tsv $bot {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset xloc [expr $xloc+$ioPitchx]\n}\n'
    # place top
    tsvIObot += 'set xloc [expr $startx+6.0]\nset yloc [expr $endy-6.0]\n'
    tsvIObot += 'foreach tsv $top {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset xloc [expr $xloc+$ioPitchx]\n}\n'
    tsvIOtop += 'set xloc [expr $startx+6.0]\nset yloc [expr $endy-6.0]\n'
    tsvIOtop += 'foreach tsv $top {\n\tplaceInstance $tsv $xloc $yloc -placed\n\tset xloc [expr $xloc+$ioPitchx]\n}\n'
    with open(os.path.join(script_dir, 'riscv_core_tsv_f2f_io_bot.tcl'), 'w') as f:
        f.write(tsvIObot)
    with open(os.path.join(script_dir, 'riscv_core_tsv_f2f_io_top.tcl'), 'w') as f:
        f.write(tsvIOtop)


    ###############
    # bump script #
    ###############
    uBumpTcl = 'create_bump -cell BUMPCELL_TSV -pitch [list {0} {0}] -pattern_array [list {1} {1}] -loc [list {2} {2}]'.format(bumpPitch, bumpsPerSide, margin)


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
source "scripts_own/riscv_core_tsv_f2f_bot.tcl"
source "scripts_own/riscv_core_tsv_f2f_io_bot.tcl"


##############
# for ubumps #
##############
{2}

# assign IO bumps
# the remaining floating bumps are guaranteed to be sufficient for pgBumps since the area is already pre-calculated
assignBump
assignPGBumps -nets {{VDD VSS}} -floating -checkerboard
#assignPGBumps -nets {{VDD VSS}} -floating -V


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
# Place TSVs #
##############
source "scripts_own/riscv_core_tsv_f2f_io_top.tcl"

##############
# for ubumps #
##############
{2}

# assign IO bumps
# the remaining floating bumps are guaranteed to be sufficient for pgBumps since the area is already pre-calculated
assignBump
assignPGBumps -nets {{VDD VSS}} -floating -checkerboard
#assignPGBumps -nets {{VDD VSS}} -floating -V

##########################################
# RDL Routing between IO cells and bumps #
##########################################
setFlipChipMode -route_style 45DegreeRoute
fcroute -type signal -designStyle pio -layerChangeBotLayer metal7 -layerChangeTopLayer metal10 -routeWidth 0

#############
# SRAM Cell #
#############
placeInstance riscv_cache/data_memory_bus_data_memory [dbGet top.fPlan.coreBox_llx] [dbGet top.fPlan.coreBox_lly] -placed
placeInstance riscv_cache/text_memory_bus_text_memory [expr [dbGet top.fPlan.coreBox_urx]-147.98] [expr [dbGet top.fPlan.coreBox_ury]-120.82] -placed
'''.format(coreDim,
           spacing,
           uBumpTcl)

    with open(os.path.join(script_dir, 'fp_3d_f2f_bottom.tcl'), 'w') as f:
        f.write(fp_tcl_bot)
    with open(os.path.join(script_dir, 'fp_3d_f2f_top.tcl'), 'w') as f:
        f.write(fp_tcl_top)

    timingCheckBot, timingCheckTop = genTimingCheckScript(design_netlist_bot, design_netlist_top)
    with open(os.path.join(script_dir, 'timing_check_f2f_bot.tcl'), 'w') as f:
        f.write(timingCheckBot)
    with open(os.path.join(script_dir, 'timing_check_f2f_top.tcl'), 'w') as f:
        f.write(timingCheckTop)

    return finalArea, constraints['defectDens'], tsvCount, 0, botInfo['designPeriod']


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--design-info-bot', required=True, type=str)
    parser.add_argument('--design-info-top', required=True, type=str)
    parser.add_argument('--design-netlist-bot', required=True, type=str)
    parser.add_argument('--design-netlist-top', required=True, type=str)
    parser.add_argument('--tech-const', required=True, type=str)
    parser.add_argument('--script-dir', required=False, type=str, default='./')
    return parser.parse_args()

def main(args):
    return f2f(args.design_info_bot, args.design_info_top, args.tech_const, args.design_netlist_bot, args.design_netlist_top, args.script_dir)

if __name__ == '__main__':
    finalArea, defectDensity, tsvCount, wireBonds, clk = main(parse())
    print ('Bot Die Area: {} (um^2)'.format(finalArea))
    print ('Top Die Area: {} (um^2)'.format(finalArea))
    print ('Total TSVs: {}'.format(tsvCount))
    print ('Defect Density: {} (per cm^2)'.format(defectDensity))
    print ('# Wire Bonds: {}'.format(wireBonds))
