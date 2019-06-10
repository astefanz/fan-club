
################################################################################
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Base class with behavior to decode MkIV fan array mappings.

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# IMPORTS ######################################################################
from . import archive as ac, standards as s


# DEFINITIONS ##################################################################
SPLITTER_CELL = ','
SPLITTER_LAYER = '-'

def mappings(archive):
    """
    Build the mappings between network coordinates "K" and the grid coordinates
    "G" based on the profile loaded in the FCArchive.

    - archive := FCArchive instance with the loaded profile to use.

    Returns a tuple of the form (f_KG_i, f_GK_i, f_KG_p, f_GK_p) where i
    functions take KG or GK indices and return the other and p functions take
    KG (s, f) pairs or GK (l, r, c) pairs and return the other.
    """
    KG, GK = _buildMappings(archive)
    L = archive[ac.fanArray][ac.FA_layers]
    R = archive[ac.fanArray][ac.FA_rows]
    C = archive[ac.fanArray][ac.FA_columns]
    RC = R*C
    n_f = archive[ac.maxFans]
    n_S = len(archive[ac.savedSlaves])

    def f_KG_i(i_KG):
        return KG[i_KG]

    def f_GK_i(i_GK):
        return GK[i_GK]

    def f_KG_p(s, f):
        k = s*n_f + f
        g = KG[k]
        l = g//RC
        r = (g%RC)//C
        c = (g%RC)%C
        return l, r, c

    def f_GK_p(l, r, c):
        g = l*RC + r*C + c
        k = GK[g]
        s = k//n_f
        f = k%n_f
        return s, f

    return (f_KG_i, f_GK_i, f_KG_p, f_GK_p)

def _buildMappings(archive):
    """
    Auxiliary function to build the mapping data structure. Separated from the
    main mapping function to save memory by only keeping relevant data in scope.

    - archive := FCArchive instance with the loaded profile to use.

    Returns a tuple of the form (KG, GK) where KG is the slaves -> grid mapping
    vector and GK is the grid -> slaves mapping vector.
    """

    array = archive[ac.fanArray]
    nlayers = array[ac.FA_layers]
    nrows = array[ac.FA_rows]
    ncolumns = array[ac.FA_columns]

    slaves = archive[ac.savedSlaves]
    nslaves = len(slaves)
    maxFans = archive[ac.maxFans]

    nfans = nslaves*maxFans
    KG = [s.PAD]*(nfans)

    gridSize = nlayers*nrows*ncolumns
    GK = [s.PAD]*(gridSize)

    for i_slave, slave in enumerate(slaves):
        row_base, column_base = slave[ac.MD_row], slave[ac.MD_column]
        nrows_slave = slave[ac.MD_rows]
        ncolumns_slave = slave[ac.MD_columns]
        mapping = slave[ac.MD_mapping]

        base_KG = i_slave*maxFans
        base_GK = column_base + row_base*ncolumns

        for i_cell, cell in enumerate(mapping.split(SPLITTER_CELL)):
            for layer, fan in enumerate(cell.split(SPLITTER_LAYER)):

                row_cell = i_cell//ncolumns_slave
                column_cell = i_cell%ncolumns_slave


                if fan != '' and row_cell + row_base < nrows \
                    and column_cell + column_base < ncolumns:

                    index_KG = base_KG + int(fan)
                    index_GK = layer*nlayers + base_GK \
                        + row_cell*ncolumns + column_cell

                    KG[index_KG] = index_GK
                    GK[index_GK] = index_KG

    return KG, GK

def _testMapping(archive):
    print("** Testing FC mapping for profile '{}'".format(archive[ac.name]))

    print("* Building mappings... ", end = '')
    _, _, f_KG, f_GK = mappings(archive)
    A = archive[ac.fanArray]
    L, R, C = A[ac.FA_layers], A[ac.FA_rows], A[ac.FA_columns]
    n_S = len(archive[ac.savedSlaves])
    n_f = archive[ac.maxFans]
    print("Done")

    print("* Printing Grid Mapping")
    for l in range(L):
        print("- Layer {}/{}:".format(l+1, L))
        print("___", end = '')
        for c in range(C):
            print("|__{:02d}__".format(c), end = '')
        print('')
        for r in range(R):
            print("{:02d}|".format(r), end = '')
            for c in range(C):
                # s,f -> _00:00_ (7)
                print(" {:02d}:{:02d} ".format(*f_GK(l, r, c)), end = '')
            print('')

