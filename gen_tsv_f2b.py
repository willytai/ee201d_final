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

def tsvTCL(netlist, tsvPitchF2B, ioCellHeight, coreDim, spacing, pgTSVs, f2b):
    tsvPool = list()
    with open(netlist, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV_'):
                tsvModule = line.split()[1]
                tsvName = tsvModule.split('(')[0]
                tsvPool.append(tsvName)

    # boundary
    endx, endy = coreDim+2*spacing+ioCellHeight-tsvPitchF2B*TSV2ioCellSpacingRatio, coreDim+2*spacing+ioCellHeight-tsvPitchF2B*TSV2ioCellSpacingRatio
    startx, starty = ioCellHeight+tsvPitchF2B*TSV2ioCellSpacingRatio, ioCellHeight+tsvPitchF2B*TSV2ioCellSpacingRatio
    # forbidden box (core area)
    forbidden = box(spacing+ioCellHeight-tsvPitchF2B*TSV2CoreBoxSpacingRatio,
                    spacing+ioCellHeight-tsvPitchF2B*TSV2CoreBoxSpacingRatio,
                    coreDim+tsvPitchF2B*2*TSV2CoreBoxSpacingRatio)

    # helper function
    def nextPos(x, y):
        x += tsvPitchF2B
        # check if valid
        if x+TSVWIDTH >= endx:
            return nextPos(startx-tsvPitchF2B, y+tsvPitchF2B)
        if y+TSVWIDTH >= endy:
            raise ValueError
        if forbidden.contains(x, y):
            return nextPos(x, y)
        return x, y
    
    tsvTcl = ''
    uBumpTcl = ''
    x, y = startx, starty
    for tsv in tsvPool:
        tsvTcl += 'placeInstance {} {} {} -placed\n'.format(tsv, x, y)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -loc {} {}\n'.format(x+TSVWIDTH/2, y+TSVWIDTH/2)
        x, y = nextPos(x, y)

    # required pg tsv and ubumps
    uniqueID = 0
    for _ in range(0, pgTSVs, 2):
        # TODO probably need to tell innovus how to connect VDD and VSS to these tsvs later
        #      or connect the ubumps to the pg tsv (how the fuck do i do this?)
        #      globalNetConnect VDD/VSS -sinst <instance name> -pin <pin name>
        #      (pg tsv and pg ubumps are named)
        tsvTcl += 'addInst -cell TSVD_IN -inst ptsv{} -loc {{{} {}}} -status placed\n'.format(uniqueID, x, y)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format pubump{} -loc {} {}\n'.format(uniqueID, x+TSVWIDTH/2, y+TSVWIDTH/2)
        x, y = nextPos(x, y)
        uniqueID += 1

        tsvTcl += 'addInst -cell TSVD_IN -inst gtsv{} -loc {{{} {}}} -status placed\n'.format(uniqueID, x, y)
        uBumpTcl += 'create_bump -cell BUMPCELL_TSV -name_format gubump{} -loc {} {}\n'.format(uniqueID, x+TSVWIDTH/2, y+TSVWIDTH/2)
        x, y = nextPos(x, y)
        uniqueID += 1

    # fill the rest of the space with pg tsvs (no harm)
    try:
        ctype = 'p'
        while True:
            tsvTcl += 'addInst -cell TSVD_IN -inst {}tsv{} -loc {{{} {}}} -status placed\n'.format(ctype, uniqueID, x, y)
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
