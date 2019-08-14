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
_LEFT_DRAG = 7
_RIGHT_DRAG = 8

ALT_COLOR_0 = "#e2e2e2"
ALT_COLOR_1 = "#bfbfbf"

## MAIN ########################################################################
class BaseGrid(tk.Frame):
    """ Interactive 2D grid widget that supports clicking, dragging, and live
        cell color changes. """

    GRID_ROW = 0
    GRID_COLUMN = 0

    GRID_WEIGHT = 1

    CALLBACK_CODES = {
        _LEFT_CLICK : '<ButtonPress-1>',
        _LEFT_DOUBLE : '<Double-Button-1>',
        _LEFT_RELEASE : '<ButtonRelease-1>',
        _RIGHT_CLICK : '<ButtonPress-3>',
        _RIGHT_DOUBLE : '<Double-Button-3>',
        _RIGHT_RELEASE : '<ButtonRelease-3>',
        _LEFT_DRAG : '<B1-Motion>',
        _RIGHT_DRAG : '<B3-Motion>'
    }


    def __init__(self, master, R, C, cursor = 'crosshair', empty = "white",
        border = 1, outline = "black", minCell = 10):
        """
        Initialize an R row and C column 2D grid as a TKinter widget with parent
        MASTER.

        MARGIN adds padding (in pixels) between the grid's outer borders and the
        TKinter frame's border.

        NOTE: This widget uses, appropriately, the grid layout. The grid itself
        is built on class attributes GRID_ROW and GRID_COLUMN. To add other
        widgets using the grid layout, you may modify these attributes through
        inheritance, or you may increment them when you call the grid layout
        manager if the grid can be kept on the top-left corner.
        """

        """
        -- NOTE ON REPRESENTATION ----------------------------------------------
        Here, we will use NumPy arrays to store the Grid's data. In particular,
        the RxC grid will be represented as an array of length R*C, where each
        cell with row r and column c is represented at index r*C + c. Notice the
        top-left item is at index 0*C + 0 = 0, and the bottom-right item is at
        index (R-1)*C + C - 1 = R*C - 1.

        For each cell, the following data needs to be stored:
        - The cell's "Item ID" (IID) for Tkinter Canvas operations
        - The cell's current "value" (duty cyle in this implementation)
        - Whether the cell is selected or not
        - Whether the cell is active
        - The cell's index in these arrays, given its IID's
        - The cell's stored color, border width, and border color

        """
        # TODO: Implement everything above

        tk.Frame.__init__(self, master)
        self.config(cursor = cursor)

        self.grid_rowconfigure(self.GRID_ROW, weight = self.GRID_WEIGHT)
        self.grid_columnconfigure(self.GRID_COLUMN, weight = self.GRID_WEIGHT)

        self.canvasFrame = tk.Frame(self)
        self.canvasFrame.grid(row = self.GRID_ROW, column = self.GRID_COLUMN,
            sticky = "NEWS")

        self.master = master
        self.R = R
        self.C = C
        self.minCell = minCell

        self.canvas = None
        self.empty = empty
        self.width = border
        self.outline = outline

        self.callbacks = {
            _LEFT_CLICK : None,
            _LEFT_DOUBLE : None,
            _LEFT_RELEASE : None,
            _RIGHT_CLICK : None,
            _RIGHT_DOUBLE : None,
            _RIGHT_RELEASE : None,
            _LEFT_DRAG : None,
            _RIGHT_DRAG : None
        }

        self.is_built = False
        self.size = R*C
        self.iids = [0]*self.size
        self._temp_tiids = [0]*self.size # FIXME
        self._temp_tmaps = [[]]*self.size # FIXME
        self.fills = [self.empty]*self.size
        self.outlines = [self.outline]*self.size
        self.widths = [self.width]*self.size
        self.indices = {}

    # Widget operations --------------------------------------------------------
    def i(self, r, c):
        """
        Return the index that corresponds to row R and column C.
        """
        return r*self.C + c

    def _temp_setmap(self, i, s, f):
        # FIXME
        self.canvas.itemconfig(
            self._temp_tiids[i], text = "{}\ns{}f{}".format(i, s, f),
                fill = "white")
        self._temp_tmaps[i] = [s, f]
        print("** ---------- temp:")
        print("[...")
        for i, p in enumerate(self._temp_tmaps):
            if len(p) > 0:
                print("\t{} {};".format(*p), end="")
            if i%11 == 0:
                print("")

        print("]")

    def draw(self, cellLength = None, margin = 1):
        """
        Build the grid. CELLLENGTH forces a cell size to use.
        """
        self.is_built = False

        if self.canvas != None:
            self.canvas.destroy()

        self.canvas = tk.Canvas(self.canvasFrame)
        self.canvas.pack(fill = tk.BOTH, expand = True)

        self.winfo_toplevel().update_idletasks()
        self.margin = margin
        self.maxWidth = self.canvas.winfo_width() - self.margin*2
        self.maxHeight = self.canvas.winfo_height() - self.margin*2

        if self.maxWidth <= 0 or self.maxHeight <= 0:

            self.config(width = self.minCell*self.C,
                height = self.minCell*self.R)

            self.maxWidth = self.winfo_reqwidth() - self.margin*2
            self.maxHeight = self.winfo_reqheight() - self.margin*2

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

        # To get xmargin:
        #   get extra space and divide it by two
        # To get total space get max space and subtract cell length times cells

        xmargin = max(int((self.maxWidth - self.C*self.cellLength)/2), margin)
        ymargin = max(int((self.maxHeight - self.R*self.cellLength)/2), margin)

        x, y = xmargin, ymargin
        l = self.cellLength

        for col in range(self.C):
            self.canvas.create_text(
                x + l/2, ymargin/2, font = "TkFixedFont 5", text = f"{col + 1}",
                    fill = "darkgray", angle = 0)
            x += l

        x = xmargin
        for row in range(self.R):
            self.canvas.create_text(
                xmargin/2, y + l/2, font = "TkFixedFont 5", text = f"{row + 1}",
                    fill = "darkgray", angle = 0)
            for col in range(self.C):
                index = row*self.C + col
                iid = self.canvas.create_rectangle(
                    x, y, x + l, y + l, fill = self.fills[index],
                    outline = self.outlines[index], width = self.widths[index])
                self.indices[iid] = index
                self.iids[index] = iid

                # FIXME
                self._temp_tiids[index] = self.canvas.create_text(
                    x + l/2, y + l/2, font = "TkFixedFont 7")

                for key, callback in self.callbacks.items():
                    if callback is not None:
                        self.canvas.tag_bind(iid, self.CALLBACK_CODES[key],
                            self._wrapper(key))

                x += l
            x = xmargin
            y += l


        # TODO show variables:
        self.canvas.create_text(
            xmargin + l/2, l*self.R + ymargin*3/2,
            font = "TkFixedFont 6", text = f"   ",
            fill = "darkgray", angle = 0)

        self.xmargin = xmargin
        self.ymargin = ymargin

        self.is_built = True

    def filli(self, i, fill):
        """
        Set the cell at 'index' I to color FILL.
        """
        if self.canvas:
            self.fills[i] = fill
            self.canvas.itemconfig(
                self.iids[i], fill = fill)

    def fillc(self, r, c, fill):
        """
        Set the cell at row R and column C to color FILL.
        """
        self.filli(r*self.C + c, fill)

    def outlinei(self, i, outline, width):
        """
        Set the border of the cell at 'index' I to color OUTLINE and width
        WIDTH.
        """
        if self.canvas:
            self.outlines[i] = outline
            self.widths[i] = width
            self.canvas.itemconfig(
                self.iids[i], outline = outline, width = width)

    def outlinec(self, r, c, outline, width):
        """
        Set the border of the cell at row R and column Cto color OUTLINE and
        width WIDTH.
        """
        self.outlinei(r*self.C + c, outline, width)

    def seti(self, fill, outline, width):
        """
        Configure grid cell at index I.
        """
        self.filli(i, fill)
        self.outlinei(i, outline, width)

    def seta(self, fill, outline, width):
        """
        Configure all grid cells to have fill FILL and an outline of color
        OUTLINE and WIDTH pixels thick.
        """
        for i in range(self.size):
            self.seti(i, fill, outline, width)

    def setLeftClick(self, f):
        self.callbacks[_LEFT_CLICK] = f
        if self.built():
            self.draw()

    def setLeftDoubleClick(self, f):
        self.callbacks[_LEFT_DOUBLE] = f
        if self.built():
            self.draw()

    def setLeftRelease(self, f):
        self.callbacks[_LEFT_RELEASE] = f
        if self.built():
            self.draw()

    def setRightClick(self, f):
        self.callbacks[_RIGHT_CLICK] = f
        if self.built():
            self.draw()

    def setRightDoubleClick(self, f):
        self.callbacks[_RIGHT_DOUBLE] = f
        if self.built():
            self.draw()

    def setRightRelease(self, f):
        self.callbacks[_RIGHT_RELEASE] = f
        if self.built():
            self.draw()

    def setLeftDrag(self, f):
        self.callbacks[_LEFT_DRAG] = f
        if self.built():
            self.draw()

    def setRightDrag(self, f):
        self.callbacks[_RIGHT_DRAG] = f
        if self.built():
            self.draw()

    def setCursor(self, cursor):
        self.config(cursor = cursor)

    def built(self):
        return self.is_built

    def _wrapper(self, C):
        """
        Generate a wrapper around the event callback with code C. The wrapper
        will call the callback and pass this grid as an object, as well as the
        index of the cell being clicked or None if the index could not be
        found
        """
        def wrapper(event):
            if self.callbacks[C] is not None:
                iid = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]
                index = self.indices[iid] if iid in self.indices else None
                self.callbacks[C](self, index)
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
