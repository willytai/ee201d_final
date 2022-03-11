def genTimingCheckScript(netlistbot, netlisttop):
    botTSVs = list()
    topTSVs = list()
    with open(netlistbot) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV'):
                tsv = line.split()[1].split('(')[0]
                dir = 'in' if line.split()[0][-2:] == 'IN' else 'out'
                if tsv[0] != 'p':
                    botTSVs.append((tsv, dir))
    with open(netlisttop) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TSV'):
                tsv = line.split()[1].split('(')[0]
                dir = 'in' if line.split()[0][-2:] == 'IN' else 'out'
                if tsv[0] != 'p':
                    topTSVs.append((tsv, dir))
    botTSVs = sorted(botTSVs)
    topTSVs = sorted(topTSVs)
    for botinfo, topinfo in zip(botTSVs, topTSVs):
        assert botinfo[0] == topinfo[0]
    tsvlist = topTSVs

    checkbot = ''
    checktop = ''
    for botinfo, topinfo in zip(botTSVs, topTSVs):
        tsv, botdir = botinfo
        _,   topdir = topinfo
        botsigtype = 'from' if botdir == 'in' else 'to'
        botpin = 'in' if botdir == 'in' else 'out'
        topsigtype = 'from' if topdir == 'in' else 'to'
        toppin = 'in' if topdir == 'in' else 'out'
        checktop += f'puts [format "{tsv} rise_delay %s" [get_property [get_timing_paths -rise_{topsigtype} {tsv}/{toppin}] arrival_mean]]\n'
        checktop += f'puts [format "{tsv} fall_delay %s" [get_property [get_timing_paths -fall_{topsigtype} {tsv}/{toppin}] arrival_mean]]\n'
        checktop += f'puts [format "{tsv} nets %s"       [get_property [get_property [get_timing_paths -fall_{topsigtype} {tsv}/{toppin}] nets] name]]\n'
        checkbot += f'puts [format "{tsv} rise_delay %s" [get_property [get_timing_paths -rise_{botsigtype} {tsv}/{botpin}] arrival_mean]]\n'
        checkbot += f'puts [format "{tsv} fall_delay %s" [get_property [get_timing_paths -fall_{botsigtype} {tsv}/{botpin}] arrival_mean]]\n'
        checkbot += f'puts [format "{tsv} nets %s"       [get_property [get_property [get_timing_paths -fall_{botsigtype} {tsv}/{botpin}] nets] name]]\n'

    return checkbot, checktop

def checkTiming(botrpt, toprpt, clk):
    timeBot = dict()
    timeTop = dict()
    netBot = dict()
    netTop = dict()
    with open(botrpt, 'r') as f:
        for line in f:
            line = line.strip().split()
            tsv = line[0]
            if line[1] == 'nets':
                netBot[tsv] = line[2:] if len(line) > 2 else []
                continue
            arrival = float(line[-1]) if len(line) == 3 else None
            if tsv not in timeBot:
                timeBot[tsv] = arrival
            elif timeBot[tsv] is not None:
                timeBot[tsv] = (timeBot[tsv] + arrival ) / 2.0
    with open(toprpt, 'r') as f:
        for line in f:
            line = line.strip().split()
            tsv = line[0]
            if line[1] == 'nets':
                netTop[tsv] = line[2:] if len(line) > 2 else []
                continue
            arrival = float(line[-1]) if len(line) == 3 else None
            if tsv not in timeTop:
                timeTop[tsv] = arrival
            elif timeTop[tsv] is not None:
                timeTop[tsv] = (timeTop[tsv] + arrival ) / 2.0
    timeCrossDie = dict()
    for tsv, arr in timeBot.items():
        # ignore treset and tclock, they are not signals that travels from bot to top or from top to bot
        if tsv == 'treset' or tsv == 'tclock': continue
        botDelay = timeBot[tsv]
        topDelay = timeTop[tsv]
        botNets = netBot[tsv]
        topNets = netTop[tsv]
        allNets = botNets + topNets
        startdie = 'bottom'
        enddie = 'top'
        if len(botNets) > 0 and len(topNets) > 0 and botNets[0] == topNets[-1]:
            botNets[0] += f' (signal crossing \'{tsv}\' from top die to bottom die)'
            allNets = topNets[:-1] + botNets
            startdie, enddie = enddie, startdie
        if len(botNets) > 0 and len(topNets) > 0 and botNets[-1] == topNets[0]:
            topNets[0] += f' (signal crossing \'{tsv}\' from bottom die to top die)'
            allNets = botNets[:-1] + topNets
        if len(allNets) > 0:
            allNets[0] += f' (starting net, {startdie})'
            allNets[-1] += f' (terminal net, {enddie})'
        if botDelay is not None and topDelay is not None:
            timeCrossDie[tsv] = (botDelay + topDelay, allNets)
        elif botDelay is not None:
            timeCrossDie[tsv] = (2*botDelay, allNets)
        elif topDelay is not None:
            timeCrossDie[tsv] = (2*topDelay, allNets)
        else:
            timeCrossDie[tsv] = None
    timingClosureMet = True
    count = 0
    for tsv, data in timeCrossDie.items():
        if data is None: continue
        crossDieDelay, nets = data
        if crossDieDelay > clk:
            timingClosureMet = False
            count += 1
            print (f'   A signal that passes through TSV: {tsv}, has arrival time: {crossDieDelay:.2f} (ns), which is greater than clock cycle: {clk:.2f} (ns)')
            print (f'       -------- nets --------')
            for net in nets:
                print (f'       - {net}')
            print (f'       ----------------------')
    print (f'{count} paths greater than clock cycle')
    return timingClosureMet

if __name__ == '__main__':
    print ('f2b')
    checkTiming('f2b_bot_output/tsv_timing.check', 'f2b_top_output/tsv_timing.check', 5)
    print ('f2f')
    checkTiming('f2f_bot_output/tsv_timing.check', 'f2f_top_output/tsv_timing.check', 5)
