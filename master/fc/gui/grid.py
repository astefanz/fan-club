################################################################################
## Project: Fanclub Mark IV "Master" base grid  ## File: grids.py             ##
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
 + Interactive 2D grid widget.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk

## AUXILIARY GLOBALS ###########################################################
# Callback names (for internal use only)
_LEFT_CLICK = 0
_LEFT_DOUBLE = 1
_LEFT_RELEASE = 3
_RIGHT_CLICK = 4
_RIGHT_DOUBLE = 5
_RIGHT_RELEASE = 6
_DRAG = 7

## MAIN ########################################################################
class BaseGrid(tk.Frame):
    """ Interactive 2D grid widget that supports clicking, dragging, and live
        cell color changes. """


    def __init__(self, master, R, C, cursor = 'crosshair', empty = "white"):
        """
        Initialize an R row and C column 2D grid as a TKinter widget with parent
        MASTER.

        MARGIN adds padding (in pixels) between the grid's outer borders and the
        TKinter frame's border.
        """
        tk.Frame.__init__(self, master)
        self.config(cursor = cursor)

        self.master = master
        self.R = R
        self.C = C

        self.canvas = None
        self.empty = empty

        self.callbacks = {
            _LEFT_CLICK : self._nothing,
            _LEFT_DOUBLE : self._nothing,
            _LEFT_RELEASE : self._nothing,
            _RIGHT_CLICK : self._nothing,
            _RIGHT_DOUBLE : self._nothing,
            _RIGHT_RELEASE : self._nothing,
            _DRAG : self._nothing
        }

    # Widget operations --------------------------------------------------------
    def draw(self, cellLength = None, margin = 1):
        """
        Build the grid. CELLLENGTH forces a cell size to use.
        """
        if self.canvas != None:
            self.canvas.destroy()

        self.canvas = tk.Canvas(self)
        self.canvas.pack(fill = tk.BOTH, expand = True)

        self.margin = margin
        self.maxWidth = self.master.winfo_width() - self.margin
        self.maxHeight = self.master.winfo_height() - self.margin

        self.cellLength = cellLength if cellLength is not None else int(
            min(self.maxHeight/self.R, self.maxWidth/self.C))

        if cellLength is None and (self.maxWidth <= 0 or self.maxHeight <= 0):
            raise RuntimeError("Margin too large for available size: "
                + "Have {} width and {} height.".format(
                    self.maxWidth, self.maxHeight))
        if self.cellLength <= 0:
            if cellLength is None:
                raise RuntimeError("Not enough pixels to display grid. "
                    + "Have {}x{} pixels for {}x{} cells.".format(
                        self.maxHeight, self.maxWidth, self.R, self.C))
            else:
                raise ValueError("Illegal cellLength {}".format(cellLength))

        self.cellToIID = {}
        self.IIDToCell = {}

        # To get xmargin:
        #   get extra space and divide it by two
        # To get total space get max space and subtract cell length times cells

        xmargin = max(int((self.maxWidth - self.C*self.cellLength)/2), margin)
        ymargin = max(int((self.maxHeight - self.R*self.cellLength)/2), margin)

        x, y = xmargin, ymargin
        l = self.cellLength
        for row in range(self.R):
            self.cellToIID[row] = {}
            for col in range(self.C):
                iid = self.canvas.create_rectangle(
                    x, y, x + l, y + l, fill = self.empty)
                self.cellToIID[row][col] = iid
                self.IIDToCell[iid] = (row, col)

                self.canvas.tag_bind(iid, '<ButtonPress-1>',
                    self._wrapper(_LEFT_CLICK))
                self.canvas.tag_bind(iid, '<Double-Button-1>',
                    self._wrapper(_LEFT_DOUBLE))
                self.canvas.tag_bind(iid, '<ButtonRelease-1>',
                    self._wrapper(_LEFT_RELEASE))

                self.canvas.tag_bind(iid, '<ButtonPress-3>',
                    self._wrapper(_RIGHT_CLICK))
                self.canvas.tag_bind(iid, '<Double-Button-3>',
                    self._wrapper(_RIGHT_DOUBLE))
                self.canvas.tag_bind(iid, '<ButtonRelease-3>',
                    self._wrapper(_RIGHT_RELEASE))

                self.canvas.tag_bind(iid, '<B1-Motion>', self._wrapper(_DRAG))

                x += l
            x = xmargin
            y += l

        self.xmargin = xmargin
        self.ymargin = margin

    def setCell(self, r, c, **kwargs):
        """
        Configure the cell at row R and column C with the TKinter Canvas
        keyword arguments KWARGS (see the TKinter Canvas itemconfig method)
        """
        self.canvas.itemconfig(
            self.cellToIID[r][c], **kwargs)

    def setAll(self, **kwargs):
        """
        Configure all grid cells to have fill FILL and an outline of color
        OUTLINE and WIDTH pixels thick.
        """
        for row in range(self.R):
            for col in range(self.C):
                self.setCell(row, col, **kwargs)

    def setLeftClick(self, f):
        self.callbacks[_LEFT_CLICK] = f

    def setLeftDoubleClick(self, f):
        self.callbacks[_LEFT_DOUBLE] = f

    def setLeftRelease(self, f):
        self.callbacks[_LEFT_RELEASE] = f

    def setRightClick(self, f):
        self.callbacks[_RIGHT_CLICK] = f

    def setRightDoubleClick(self, f):
        self.callbacks[_RIGHT_DOUBLE] = f

    def setRightRelease(self, f):
        self.callbacks[_RIGHT_RELEASE] = f

    def setDrag(self, f):
        self.callbacks[_DRAG] = f

    def setCursor(self, cursor):
        self.config(cursor = cursor)

    def _wrapper(self, C):
        """
        Generate a wrapper around the event callback with code C. The wrapper
        will call the callback and pass this grid as an object, as well as the
        row and column of the cell pointed to by the cursor.
        """
        def wrapper(event):
            iid = self.canvas.find_closest(
                self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y))[0]
            x, y = self.IIDToCell[iid]
            self.callbacks[C](self, x, y)
        return wrapper

    def _nothing(*args):
        """
        Placeholder method for unassigned callbacks.
        """
        pass

## TEST RUN ####################################################################
if __name__ == "__main__":

    import threading as mt

    print("FC Grid Demo run started")

    def r(g, r, c):
        g.draw()

    def c(g, r, c):
        g.setCell(r, c, fill='red',outline='blue')

    def d(g, r, c):
        g.setCell(r, c, fill ='yellow',outline='orange')

    def e(g, r, c):
        g.setCell(r, c, fill='black')

    def dd(g, r, c):
        g.setAll(width = 6 if g.G else 1)
        g.G = not g.G


    root = tk.Tk()
    root.winfo_toplevel().title('FC Base Grid demo')
    root.geometry('500x500')
    g = BaseGrid(root, 36, 36)
    g.G = False

    g.setRightClick(r)
    g.setLeftClick(c)
    g.setLeftRelease(e)
    g.setLeftDoubleClick(dd)
    g.setDrag(d)

    g.config(bg = 'red')
    g.pack(fill = tk.BOTH, expand = True)
    g.draw(20)

    root.mainloop()


    print("FC Grid Demo run finished")
