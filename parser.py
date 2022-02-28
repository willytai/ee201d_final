
def parse_info(filename):
    info = dict()
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip().split()
            if len(line) == 0: continue
            if line[0][0] == '#': continue
            key = line[0]
            val = line[-1]
            if val[-1] == ';': val = val[:-1]
            if key == 'designArea': val = float(val)
            if key == 'designPower': val = float(val)
            if key == 'designPeriod': val = float(val)
            if key == 'ioCount': val = int(val)
            if key == 'tsvCount': val = int(val)
            if key == 'targetUtil': val = float(val)
            info[key] = val
    return info

def parse_constraints(filename):
    info = dict()
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip().split()
            if len(line) == 0: continue
            if line[0][0] == '#': continue
            key = line[0]
            val = line[-1]
            if val[-1] == ';': val = val[:-1]
            if key == 'bumpPitchSoC': val = int(val)
            if key == 'bumpPitchF2F': val = int(val)
            if key == 'tsvPitchF2B': val = int(val)
            if key == 'tsvPitchF2F': val = int(val)
            if key == 'ioCellWidth': val = float(val)
            if key == 'ioCellHeight': val = float(val)
            if key == 'defectDens': val = float(val)
            if key == 'currDen': val = float(val)
            info[key] = val
    return info
