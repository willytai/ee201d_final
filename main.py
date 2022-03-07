import argparse, os, subprocess, sys
from gen_fp_soc import soc
from gen_fp_3d_f2b import f2b
from gen_fp_3d_f2f import f2f
from yield_model import *
from runInnovus import runInnovusSoC, runInnovusF2B, runInnovusF2F

endcolor = '\033[0m'
red      = '\033[1;31m'
green    = '\033[1;32m'
yellow   = '\033[1;33m'
blue     = '\033[1;34m'
magenta  = '\033[1;35m'

def main(args):
    print ('---------------------------SoC---------------------------') 
    SoCArea, SoCDefectDensity = soc(args.soc, args.tech_const, args.script_dir)
    print (f'{SoCArea=}')
    print (f'{SoCDefectDensity=}')
    print ('---------------------------------------------------------') 

    print ('---------------------------f2b---------------------------') 
    f2bArea, f2bDefectDensity, f2bTSVs, f2bWireBonds = f2b(args.f2b_bot, args.f2b_top, args.tech_const, args.f2b_bot_netlist, args.script_dir)
    print (f'{f2bArea=} (both top and bottom die)')
    print (f'{f2bDefectDensity=}')
    print (f'{f2bTSVs=}')
    print (f'{f2bWireBonds=}')
    print ('---------------------------------------------------------') 

    print ('---------------------------f2b---------------------------') 
    f2fArea, f2fDefectDensity, f2fTSVs, f2fWireBonds = f2f(args.f2f_bot, args.f2f_top, args.tech_const, args.f2f_bot_netlist, args.script_dir)
    print (f'{f2fArea=} (both top and bottom die)')
    print (f'{f2fDefectDensity=}')
    print (f'{f2fTSVs=}')
    print (f'{f2fWireBonds=}')
    print ('---------------------------------------------------------') 

    print ('--------------------------Yield--------------------------') 
    SoCYield = yieldSoC(SoCArea, SoCDefectDensity)
    f2bYield = yield3D(f2bArea, f2bDefectDensity, f2bTSVs, f2bWireBonds)
    f2fYield = yield3D(f2fArea, f2fDefectDensity, f2fTSVs, f2fWireBonds)
    print (f'{blue}', end ='')
    print (f'=> SoC yield: {SoCYield:.6f}')
    print (f'=> F2B yield: {f2bYield:.6f}')
    print (f'=> F2F yield: {f2fYield:.6f}')
    print (f'{endcolor}', end ='')

    choices = list()
    choices.append((SoCYield, 'soc'))
    choices.append((f2bYield, 'f2b'))
    choices.append((f2fYield, 'f2f'))
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
    elif flow == 'exit':
        sys.exit()
    else:
        print (f'{yellow}=> Unrecognized option: {flow}, using default: {choices[0][1]}{endcolor}')
        flow = choices[0][1]

    #gui  = input(f'{yellow}=> Show GUI? [yes/no] (hit enter for default: no): {endcolor}').strip().lower()
    #if gui == 'yes' or gui == 'y':
    #    gui = True
    #elif gui == 'no' or gui == 'n' or gui == '':
    #    gui = False
    #else:
    #    print (f'{yellow}=> Unrecognized option: {gui}, gui disabled{endcolor}')
    gui = False


    # invoke innovus with subprocess
    if flow == 'soc':
        runInnovusSoC(gui)
    elif flow == 'f2b':
        runInnovusF2B(gui)
    elif flow == 'f2f':
        runInnovusF2F(gui)

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
