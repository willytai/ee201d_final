def genTimingCheckScript(netlistbot, netlisttop):
    botTSVs = list()
    topTSVs = list()
    with open(netlistbot) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV'):
                tsv = line.split()[1].split('(')[0]
                if tsv[0] != 'p':
                    botTSVs.append(tsv)
    with open(netlisttop) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV'):
                tsv = line.split()[1].split('(')[0]
                if tsv[0] != 'p':
                    topTSVs.append(tsv)
    botTSVs = sorted(botTSVs)
    topTSVs = sorted(topTSVs)
    assert botTSVs == topTSVs
    tsvlist = topTSVs

    checkbot = ''
    checktop = ''
    for tsv in tsvlist:
        checktop += f'puts [format "{tsv} rise_delay %s" [get_property [get_timing_paths -rise_from {tsv}/in] arrival_mean]]\n'
        checktop += f'puts [format "{tsv} fall_delay %s" [get_property [get_timing_paths -fall_from {tsv}/in] arrival_mean]]\n'
        checkbot += f'puts [format "{tsv} rise_delay %s" [get_property [get_timing_paths -rise_to {tsv}/out] arrival_mean]]\n'
        checkbot += f'puts [format "{tsv} fall_delay %s" [get_property [get_timing_paths -fall_to {tsv}/out] arrival_mean]]\n'

    return checkbot, checktop

def checkTiming(botrpt, toprpt, clk):
    timeBot = dict()
    timeTop = dict()
    with open(botrpt, 'r') as f:
        for line in f:
            line = line.strip().split()
            tsv = line[0]
            arrival = float(line[-1]) if len(line) == 3 else None
            if tsv not in timeBot:
                timeBot[tsv] = arrival
            elif timeBot[tsv] is not None:
                timeBot[tsv] = (timeBot[tsv] + arrival ) / 2.0
    with open(toprpt, 'r') as f:
        for line in f:
            line = line.strip().split()
            tsv = line[0]
            arrival = float(line[-1]) if len(line) == 3 else None
            if tsv not in timeTop:
                timeTop[tsv] = arrival
            elif timeTop[tsv] is not None:
                timeTop[tsv] = (timeTop[tsv] + arrival ) / 2.0
    timeCrossDie = dict()
    for tsv, arr in timeBot.items():
        botDelay = timeBot[tsv]
        topDelay = timeTop[tsv]
        if botDelay is not None and topDelay is not None:
            timeCrossDie[tsv] = botDelay + topDelay
        elif botDelay is not None:
            timeCrossDie[tsv] = 2*botDelay
        elif topDelay is not None:
            timeCrossDie[tsv] = 2*topDelay
        else:
            timeCrossDie[tsv] = None
    timingClosureMet = True
    count = 0
    for tsv, crossDieDelay in timeCrossDie.items():
        if crossDieDelay is None: continue
        if crossDieDelay > clk:
            timingClosureMet = False
            count += 1
            print (f'   1 or more signals that pass through TSV: {tsv} has negative setup slack: {clk:.2f}(required) - {crossDieDelay:.2f}(arrival) = {clk-crossDieDelay:.2f} (ns)')
    print (f'{count} paths greater than clock cycle')
    return timingClosureMet

if __name__ == '__main__':
    print ('f2b')
    checkTiming('f2b_bot_output/tsv_timing.check', 'f2b_top_output/tsv_timing.check', 5)
    print ('f2f')
    checkTiming('f2f_bot_output/tsv_timing.check', 'f2f_top_output/tsv_timing.check', 5)
