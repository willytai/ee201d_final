import argparse, subprocess, os
from gen_fp_soc import soc
from gen_fp_3d_f2b import f2b
from yield_model import *

endcolor = '\033[0m'
red      = '\033[1;31m'
green    = '\033[1;32m'
yellow   = '\033[1;33m'
blue     = '\033[1;34m'
magenta  = '\033[1;35m'

def main(args):
    print ('---------------------------SoC---------------------------') 
    SoCArea, SoCDefectDensity = soc(args.soc, args.tech_const, args.script_dir)
    SoCYield = soc_yield(SoCArea, SoCDefectDensity)
    print (f'{SoCArea=}')
    print (f'{SoCDefectDensity=}')
    print (f'{blue}{SoCYield=}{endcolor}')
    print ('---------------------------------------------------------') 
    print ('---------------------------f2b---------------------------') 
    f2bArea, f2bDefectDensity, f2bTSVs, f2bWireBonds = f2b(args.f2b_bot, args.f2b_top, args.tech_const, args.f2b_bot_netlist, args.script_dir)
    f2bYield = f2b_yield(f2bArea, f2bDefectDensity, f2bTSVs, f2bWireBonds)
    print (f'{f2bArea=} (both top and bottom die)')
    print (f'{f2bDefectDensity=}')
    print (f'{f2bTSVs=}')
    print (f'{f2bWireBonds=}')
    print (f'{blue}{f2bYield=}{endcolor}')
    print ('---------------------------------------------------------') 

    choices = list()
    choices.append((SoCYield, 'soc'))
    choices.append((f2bYield, 'f2b'))
    choices.sort(key=lambda x: x[0], reverse=True)
    print (f'{yellow}=> The flow with the highest estimated yield is: {choices[0][1]} (yield={choices[0][0]}){endcolor}')
    flow = input(f'{yellow}=> Choose a flow to continue [soc/f2b/f2f] (hit enter for default: {choices[0][1]}): {endcolor}').strip().lower()
    if flow == '':
        print (f'{yellow}=> Using default: {choices[0][1]}{endcolor}')
        flow = choices[0][1]
    elif flow == 'soc':
        print (f'{yellow}=> Running {flow} flow{endcolor}')
    elif flow == 'f2b':
        print (f'{yellow}=> Running {flow} flow{endcolor}')
    elif flow == 'f2f':
        print (f'{yellow}=> Running {flow} flow{endcolor}')
    else:
        print (f'{yellow}=> Unrecognized option: {flow}, using default: {choices[0][1]}{endcolor}')
        flow = choices[0][1]

    # invoke innovus with subprocess
    if flow == 'soc':
        raise NotImplementedError('soc flow')
    elif flow == 'f2b':
        raise NotImplementedError('f2b flow')
    elif flow == 'f2f':
        raise NotImplementedError('f2f flow')

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--soc',             required=True, type=str, help='the synthesized report for the die in SoC design')
    parser.add_argument('--f2b-top',         required=True, type=str, help='the synthesis report for the top die in f2b design')
    parser.add_argument('--f2b-bot',         required=True, type=str, help='the synthesized report for the bottom die in f2b design')
    parser.add_argument('--f2b-bot-netlist', required=True, type=str, help='the netlist for the bottom die in f2b design (used for TSV generation)')
    parser.add_argument('--f2f-top',         required=True, type=str, help='the synthesized report for the top die in f2f design')
    parser.add_argument('--f2f-bot',         required=True, type=str, help='the synthesis report for the bottom die in f2f design')
    parser.add_argument('--f2f-bot-netlist', required=True, type=str, help='the netlist for the bottom die in f2f design (used for TSV generation)')
    parser.add_argument('--tech-const',      required=True, type=str, help='the technology constraint file')
    parser.add_argument('--script-dir',      required=True, type=str, help='the directory containing the scripts (script_own)')
    return parser.parse_args()

if __name__ == '__main__':
    main(parse())
