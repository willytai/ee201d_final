# 0.5 is a good ratio
TSV2CoreBoxSpacingRatio = 0.5
TSV2ioCellSpacingRatio = 0.5
TSVWIDTH = 6

class box():
    def __init__(self, blx, bly, size):
        self.blx = blx
        self.bly = bly
        self.urx = blx+size
        self.ury = bly+size

    def __str__(self):
        return '({} {}) ({} {})'.format(self.blx, self.bly, self.urx, self.ury)

    def contains(self, x, y):
        if x <= self.blx: return False
        if y <= self.bly: return False
        if x+TSVWIDTH >= self.urx: return False
        if y+TSVWIDTH >= self.ury: return False
        return True

def tsvTCL(netlist, tsvPitch, ioCellHeight, coreDim, spacing, pgTSVs, f2b, start=None):
    tsvPool = list()
    with open(netlist, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV_'):
                tsvModule = line.split()[1]
                tsvName = tsvModule.split('(')[0]
                tsvPool.append(tsvName)

    # boundary
    endx, endy = coreDim+2*spacing+ioCellHeight-tsvPitch*TSV2ioCellSpacingRatio, coreDim+2*spacing+ioCellHeight-tsvPitch*TSV2ioCellSpacingRatio
    if start is not None:
        startx, starty = start, start
    else:
        startx, starty = ioCellHeight+tsvPitch*TSV2ioCellSpacingRatio, ioCellHeight+tsvPitch*TSV2ioCellSpacingRatio
    # forbidden box (core area)
    forbidden = box(spacing+ioCellHeight-tsvPitch*TSV2CoreBoxSpacingRatio,
                    spacing+ioCellHeight-tsvPitch*TSV2CoreBoxSpacingRatio,
                    coreDim+tsvPitch*2*TSV2CoreBoxSpacingRatio)

    # helper function
    # state: right, up, left, down
    #        0      1   2     3
    def nextPos(x, y, state, startx, starty):
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
            return nextPos(x, y, state, startx, starty)
        if y+TSVWIDTH > endy:
            y -= tsvPitch
            state = 2
            return nextPos(x, y, state, startx, starty)
        if x < startx:
            x += tsvPitch
            state = 3
            return nextPos(x, y, state, startx, starty)
        if y <= starty and state == 3:
            startx, starty = startx+tsvPitch, starty+tsvPitch
            x, y = startx, starty
            state = 0
        if forbidden.contains(x, y):
            print (x, y, 'is contained in', forbidden)
            raise ValueError
        return x, y, state, startx, starty
    
    tsvTcl = ''
    uBumpTcl = ''
    x, y = startx-tsvPitch, starty
    state = 0
    for tsv in tsvPool:
        x, y, state, startx, starty = nextPos(x, y, state, startx, starty)
        tsvTcl += 'placeInstance {} {} {} -placed\n'.format(tsv, x, y)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -loc {} {}\n'.format(x+TSVWIDTH/2, y+TSVWIDTH/2)

    # required pg tsv and ubumps
    uniqueID = 0
    for _ in range(0, pgTSVs, 2):
        # TODO probably need to tell innovus how to connect VDD and VSS to these tsvs later
        #      or connect the ubumps to the pg tsv (how the fuck do i do this?)
        #      globalNetConnect VDD/VSS -sinst <instance name> -pin <pin name>
        #      (pg tsv and pg ubumps are named)
        x, y, state, startx, starty = nextPos(x, y, state, startx, starty)
        tsvTcl += 'addInst -cell TSVD_IN -inst ptsv{} -loc {{{} {}}} -status placed\n'.format(uniqueID, x, y)
        tsvTcl += 'globalNetConnect VDD -type pgpin -sinst ptsv{} -pin in\n'.format(uniqueID)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format pubump{} -loc {} {}\n'.format(uniqueID, x+TSVWIDTH/2, y+TSVWIDTH/2)
        uniqueID += 1

        x, y, state, startx, starty = nextPos(x, y, state, startx, starty)
        tsvTcl += 'addInst -cell TSVD_IN -inst gtsv{} -loc {{{} {}}} -status placed\n'.format(uniqueID, x, y)
        tsvTcl += 'globalNetConnect VSS -type pgpin -sinst gtsv{} -pin in\n'.format(uniqueID)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format gubump{} -loc {} {}\n'.format(uniqueID, x+TSVWIDTH/2, y+TSVWIDTH/2)
        uniqueID += 1

    # fill the rest of the space with pg tsvs (no harm)
    try:
        ctype = 'p'
        while True:
            tsvTcl += 'addInst -cell TSVD_IN -inst {}tsv{} -loc {{{} {}}} -status placed\n'.format(ctype, uniqueID, x, y)
            if ctype == 'p':
                tsvTcl += 'globalNetConnect VDD -type pgpin -sinst ptsv{} -pin in\n'.format(uniqueID)
            else:
                tsvTcl += 'globalNetConnect VSS -type pgpin -sinst gtsv{} -pin in\n'.format(uniqueID)
            uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format {}ubump{} -loc {} {}\n'.format(ctype, uniqueID, x+TSVWIDTH/2, y+TSVWIDTH/2)
            x, y = nextPos(x, y)
            uniqueID += 1
            if ctype == 'p': ctype = 'g'
            else: ctype = 'p'
    except Exception as e:
        pass

    if f2b:
        return tsvTcl, uBumpTcl
    else:
        return tsvTcl, None
