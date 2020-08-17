#!/usr/bin/python3
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
from fc import archive as ac, standards as std


# DEFINITIONS ##################################################################
class Mapper:
    """
    Abstracts the grid mapping as a bijection between two coordinate spaces:
    network coordinates K with ordered pairs (s, f) and indices k and
    grid coordinates G with ordered triples (l, r, c) and indices g.
    """
    SPLITTER_CELL = ','
    SPLITTER_LAYER = '-'

    def __init__(self, archive):
        """
        - archive := FCArchive instance.
        """
        self.archive = archive
        self._buildMappings()

    # API ----------------------------------------------------------------------
    def index_KG(self, k):
        """
        Given a k-index, return the corresponding g-index.
        """
        return self.KG[k]

    def index_GK(self, g):
        """
        Given a g-index, return the corresponding k-index.
        """
        return self.GK[g]

    def tuple_KG(self, s, f):
        """
        Given a k-tuple (s, f), return the corresponding g-tuple (l, r, c).
        """
        k = s*self.maxFans + f
        g = self.KG[k]
        l = g//self.RC
        r = (g%self.RC)//self.C
        c = (g%self.RC)%self.C
        return l, r, c

    def tuple_GK(self, l, r, c):
        """
        Given a g-tuple (l, r, c), return the corresponding k-tuple (s, f).
            """
        g = l*self.RC + r*self.C + c
        k = self.GK[g]
        s = k//n_f
        f = k%n_f
        return s, f

    def profileChange(self):
        self._buildMappings()

    def getSize_G(self):
        return self.size_g

    def getSize_K(self):
        return self.size_k

    def getZero_K(self):
        """
        Return a zero-vector of size K*2.
        """
        return [0]*(2*self.getSize_K())

    def getZero_K(self):
        """
        Return a zero-vector of size G*2.
        """
        return [0]*(2*self.getSize_G())

    # Internal methods ---------------------------------------------------------

    def _buildMappings(self):
        """
        Build the mapping data structure. Must be called before using the
        Mapper instance and can be called later to update the mapping when
        the loaded profile changestd.
        """

        self.array = self.archive[ac.fanArray]
        self.L = self.array[ac.FA_layers]
        self.R = self.array[ac.FA_rows]
        self.C = self.array[ac.FA_columns]
        self.RC = self.R*self.C

        slaves = self.archive[ac.savedSlaves]
        self.nslaves = len(slaves)
        self.maxFans = self.archive[ac.maxFans]

        self.size_k = self.nslaves*self.maxFans
        self.KG = [std.PAD]*(self.size_k)

        self.size_g = self.L*self.R*self.C
        self.GK = [std.PAD]*(self.size_g)

        for s, slave in enumerate(slaves):
            row_base, column_base = slave[ac.MD_row], slave[ac.MD_column]
            nrows_slave = slave[ac.MD_rows]
            ncolumns_slave = slave[ac.MD_columns]
            mapping = slave[ac.MD_mapping]

            base_KG = s*self.maxFans
            base_GK = column_base + row_base*self.C

            for i_cell, cell in enumerate(mapping.split(self.SPLITTER_CELL)):
                for layer, fan in enumerate(cell.split(self.SPLITTER_LAYER)):

                    row_cell = i_cell//ncolumns_slave
                    column_cell = i_cell%ncolumns_slave


                    if fan != '' and row_cell + row_base < self.R \
                        and column_cell + column_base < self.C:

                        index_KG = base_KG + int(fan)
                        index_GK = layer*self.RC + base_GK \
                            + row_cell*self.C + column_cell

                        self.KG[index_KG] = index_GK
                        self.GK[index_GK] = index_KG

        # FIXME debug

    def _testMapping(self):
        print("** Testing FC mapping for profile '{}'".format(archive[ac.name]))

        print("* Building mappingstd... ", end = '')
        f_GK = self.tuple_GK
        A = self.archive[ac.fanArray]
        archive = self.archive
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
