
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
    Build the mappings between the slave-space "S" and the grid-space
    "G" based on the profile loaded in the FCArchive.

    - archive := FCArchive instance with the loaded profile to use.

    Returns a tuple of the form (f_SG_i, f_GS_i, f_SG_p, f_GS_p) where i
    functions take SG or GS indices and return the other and p functions take
    SG (s, f) pairs or GS (l, r, c) pairs and return the other.
    """
    SG, GS = _buildMappings(archive)
    L = archive[ac.fanArray][ac.FA_layers]
    R = archive[ac.fanArray][ac.FA_rows]
    C = archive[ac.fanArray][ac.FA_columns]
    RC = R*C
    n_f = archive[ac.maxFans]
    n_S = len(archive[ac.savedSlaves])

    def f_SG_i(i_SG):
        return SG[i_SG]

    def f_GS_i(i_GS):
        return GS[i_GS]

    def f_SG_p(s, f):
        i_GS = SG[s*n_f + f]
        l = i_GS//RC
        r = (l%RC)//C
        c = (l%RC)%C
        return l, r, c

    def f_GS_p(l, r, c):
        i_SG = GS[l*RC + r*C + c]
        s = i_SG//n_f
        f = i_SG%n_f
        return s, f

    return (f_SG_i, f_GS_i, f_SG_p, f_GS_p)

def _buildMappings(archive):
    """
    Auxiliary function to build the mapping data structure. Separated from the
    main mapping function to save memory by only keeping relevant data in scope.

    - archive := FCArchive instance with the loaded profile to use.

    Returns a tuple of the form (SG, GS) where SG is the slaves -> grid mapping
    vector and GS is the grid -> slaves mapping vector.
    """

    array = archive[ac.fanArray]
    nlayers = array[ac.FA_layers]
    nrows = array[ac.FA_rows]
    ncolumns = array[ac.FA_columns]

    slaves = archive[ac.savedSlaves]
    nslaves = len(slaves)
    maxFans = archive[ac.maxFans]

    nfans = nslaves*maxFans
    SG = [s.RIP]*(nfans)

    gridSize = nlayers*nrows*ncolumns
    GS = [s.RIP]*(gridSize)

    for i_slave, slave in enumerate(slaves):
        row_base, column_base = slave[ac.MD_row], slave[ac.MD_column]
        nrows_slave = slave[ac.MD_rows]
        ncolumns_slave = slave[ac.MD_columns]
        mapping = slave[ac.MD_mapping]

        base_SG = i_slave*maxFans
        base_GS = column_base + row_base*ncolumns

        for i_cell, cell in enumerate(mapping.split(SPLITTER_CELL)):
            for layer, fan in enumerate(cell.split(SPLITTER_LAYER)):

                row_cell = i_cell//ncolumns_slave
                column_cell = i_cell%ncolumns_slave


                if fan != '' and row_cell + row_base < nrows \
                    and column_cell + column_base < ncolumns:

                    index_SG = base_SG + int(fan)
                    index_GS = layer*nlayers + base_GS \
                        + row_cell*ncolumns + column_cell

                    SG[index_SG] = index_GS
                    GS[index_GS] = index_SG

    return SG, GS

def _testMapping(archive):
    print("** Testing FC mapping for profile '{}'".format(archive[ac.name]))

    print("* Building mappings... ", end = '')
    _, _, f_SG, f_GS = mappings(archive)
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
                print(" {:02d}:{:02d} ".format(*f_GS(l, r, c)), end = '')
            print('')

