import math

def die_yield(dieArea_um2, defectDensity_cm2):
    D_0 = defectDensity_cm2
    A = dieArea_um2 * 1e-8
    return pow(math.e, -D_0*A)

'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6724718 tsv yield 99.2%'
def tsv_yield(nTSVs):
    return pow((1-0.00005), nTSVs)

def bonding_yield(ioCount):
    return pow(0.9999, ioCount)

def thinning_yield():
    return 0.95

def soc_yield(area, density):
    return die_yield(area, density)

def f2b_yield(area, density, tsvs, ios):
    return (die_yield(area, density)**2)*thinning_yield()*tsv_yield(tsvs)*bonding_yield(ios)

if __name__ == '__main__':
    dieYield = die_yield(126167.04, 0.1)
    tsvYield = tsv_yield(172)
    bondingYield = bonding_yield(34)
    thinningYield = thinning_yield()
    print (f'{dieYield=}')
    print (f'{tsvYield=}')
    print (f'{bondingYield=}')
    print (f'{thinningYield=}')
