import math

def die_yeild(dieArea_um2, defectDensity_cm2):
    D_0 = defectDensity_cm2
    A = dieArea_um2 * 1e-8
    return pow(math.e, -D_0*A)


if __name__ == '__main__':
    print (die_yeild(126167.04, 0.1))
