################################################################################
## Project: Fanclub Mark IV "Master" profile GUI  ## File: profile.py         ##
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
 + GUI Component in charge of displaying and manipulating FC profiles.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk

from fc import archive as ac, printer as pt
from fc.builtin import profiles as btp
from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import loader as ldr

## AUXILIARY GLOBALS ###########################################################
TAG_SUB = "M"
TAG_PRIMITIVE = "P"
TAG_LIST = "L"

## MAIN ########################################################################
class ProfileDisplay(tk.Frame, pt.PrintClient):
    SYMBOL = "[PD]"

    def __init__(self, master, archive, callback, pqueue):
        """
        Build an empty FC profile display in container MASTER.
        - master := Tkinter parent widget
        - archive := FC Archive instance
        - callback := method to call without arguments to apply profile changes
        - pqueue := Queue object to use for I-P printing
        """
        tk.Frame.__init__(self, master = master)
        pt.PrintClient.__init__(self, pqueue, self.SYMBOL)

        # TODO:
        # - means by which to automatically update values here if the archive
        #   is modified elsewhere (should this be allowed?)

        # Core setup ...........................................................
        self.archive = archive
        self.callback = callback
        self.map = {}
        self.root = ''

        # Grid:
        self.grid_rowconfigure(0, weight = 0)
        self.grid_rowconfigure(1, weight = 0)
        self.grid_rowconfigure(2, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(2, weight = 1)
        self.numcolumns = 3

        # Callbacks:
        # FIXME
        self.applyCallback = self._nothing

        # File I/O:
        self.loader = ldr.Loader(self, (("Fan Club Profile",".fcp"),))

        # Build top bar ........................................................
        self.topBar = tk.Frame(self)
        self.topBar.grid(row = 0, columnspan = self.numcolumns, sticky = "EW")

        self.topLabel = tk.Label(self.topBar, text = "Profile:   ",
            justify = tk.LEFT)
        self.topLabel.pack(side = tk.LEFT)

        self.defaultButton = tk.Button(self.topBar, text = "Default",
            command = self._default)
        self.defaultButton.pack(side = tk.LEFT)

        self.loadButton = tk.Button(self.topBar, text = "Load",
            command = self._load)
        self.loadButton.pack(side = tk.LEFT)

        self.saveButton = tk.Button(self.topBar, text = "Save",
            command = self._save)
        self.saveButton.pack(side = tk.LEFT)

        self.applyButton = tk.Button(self.topBar, text = "Apply",
            command = self.applyCallback)
        self.applyButton.pack(side = tk.LEFT)

        # Built-in menu:
        self.builtin = btp.PROFILES
        builtinkeys = ("N/A",) + tuple(self.builtin.keys())
        self.builtinFrame = tk.Frame(self.topBar)
        self.builtinFrame.pack(side = tk.RIGHT)
        self.builtinLabel = tk.Label(self.builtinFrame,
            text = "Built-in: ")
        self.builtinLabel.pack(side = tk.LEFT)
        self.builtinMenuVar = tk.StringVar()
        self.builtinMenuVar.trace('w', self._onBuiltinMenuChange)
        self.builtinMenuVar.set(builtinkeys[0])
        self.builtinMenu = tk.OptionMenu(self.builtinFrame, self.builtinMenuVar,
            *builtinkeys)
        self.builtinMenu.pack(side = tk.LEFT, expand = True)

        # Build display ........................................................
        self.displayFrame = tk.Frame(self)
        self.displayFrame.grid(row = 2, column = 0, sticky = "NEWS", pady = 10)

        self.font = tk.font.Font(font = "TkDefaultFont 16 bold")

        self.display = ttk.Treeview(self.displayFrame)
        self.display.configure(columns = ("Attribute", "Value"))
        self.display.column("#0", width = self.font.measure("    "),
            stretch = False)
        self.display.column("Attribute")
        self.display.column("Value")
        self.display.heading("Attribute", text = "Attribute")
        self.display.heading("Value", text = "Value")
        self.display.pack(fill = tk.BOTH, expand = True)

        self.display.tag_configure(TAG_SUB, font = "TkDefaultFont 7 bold")
        self.display.tag_configure(TAG_LIST, font = "TkDefaultFont 7 bold")

        for event in ("<ButtonRelease-1>", "<KeyRelease-Up>",
            "<KeyRelease-Down>"):
            self.display.bind(event, self._check_editability)

        for event in ("<KeyRelease-Return>", "<Double-Button-1>"):
            self.display.bind(event, self._on_double)

        # Build editor ........................................................
        self.editorFrame = tk.Frame(self, relief = tk.RIDGE, bd = 1)
        self.editorFrame.grid(row = 2, column = 2, sticky = "NEWS", pady = 10)

        self.editor = PythonEditor(self.editorFrame,
            add_callback = self._on_add, edit_callback = self._on_edit,
            remove_callback = self._on_remove,
            printx = self._nothing, printr = self._nothing)
        self.editor.pack(fill = tk.BOTH, expand= True)


        # Scrollbar:
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.grid(row = 2, column = 1, pady = 10, sticky = "NS")
        self.scrollbar.config(command = self.display.yview)
        self.display.config(yscrollcommand = self.scrollbar.set)

        self.build()

    # API ----------------------------------------------------------------------
    def build(self):
        """
        Rebuild the displayed values based on the current profile attributes in
        the loaded archive.
        """
        self.clear()
        self.root = \
            self._addModule(self.archive[ac.name], self.archive.profile(), 0)
        self.display.item(self.root, open = True)

    def clear(self):
        """
        Remove all entries from the display.
        """
        if self.root:
            self.display.delete(self.root)
            self.map = {}

    # Internal methods ---------------------------------------------------------
    def _addModule(self, name, module, precedence, parent = ''):
        """
        Add MODULE to the display
        """
        iid = self.display.insert(parent, precedence, values = (name, ''),
            tag = TAG_SUB)
        for child in module:
            meta = self.archive.meta[child]
            if meta[ac.TYPE] is ac.TYPE_LIST:
                self._addList(meta[ac.NAME], module[child], meta[ac.PRECEDENCE],
                iid)
            elif meta[ac.TYPE] is ac.TYPE_SUB:
                self._addModule(meta[ac.NAME], module[child],
                meta[ac.PRECEDENCE], iid)
            elif meta[ac.TYPE] is ac.TYPE_MAP:
                self._addMap(meta[ac.NAME], module[child], meta[ac.PRECEDENCE],
                    iid)
            else:
                self._addPrimitive(meta[ac.NAME], module[child],
                    meta[ac.PRECEDENCE], iid)
        # FIXME: map?
        return iid


    def _addPrimitive(self, name, value, precedence, parent = ''):
        iid = self.display.insert(parent, precedence, values = (name,
            repr(value)))
        # FIXME: map?
        return iid

    def _addMap(self, name, M, precedence, parent = ''):
        iid = self.display.insert(parent, precedence, values = (name, ''),
            tag = TAG_SUB)
        for key in M:
            iid_c = self.display.insert(iid, 0, values = (key, M[key]))
        return iid

    def _addList(self, name, iterable, precedence, parent = ''):
        iid = self.display.insert(parent, precedence, values = (name, ''),
            tag = TAG_LIST)

        indexer = self.archive.defaults[ac.INVERSE[name]][ac.INDEXER]
        for element in iterable:
            # FIXME
            self._addModule(indexer(element), element, indexer(element), iid)
            #self._addPrimitive(indexer(element), element, indexer(element),iid)
            # FIXME: map?
        return iid

    # Callbacks ----------------------------------------------------------------
    def _default(self, event = None):
        """
        Switch to the default profile and display it.
        """
        self.archive.default()
        self.build()
        self.callback()

    def _save(self, event = None):
        """
        Save the current profile.
        """
        name = self.loader.saveDialog("fan_array_profile")
        if name:
            self.archive.save(name)

    def _load(self, event = None):
        """
        Load a new profile.
        """
        name = self.loader.loadDialog()
        if name:
            self.archive.load(name)
            self.build()
            self.callback()

    def _check_editability(self, event = None):
        """
        To be called when a new attribute is selected. Checks whether the
        attribute can be edited and, if so, how (by changing it, adding to it,
        or deleting it)

        See:
        https://stackoverflow.com/questions/30614279/
            python-tkinter-tree-get-selected-item-values

        """


        iid = self.display.focus()
        if iid == self.root:
            self.editor._untouchable()
            return

        parent_iid = self.display.parent(iid)
        parent_key = ac.INVERSE[self.display.item(parent_iid)['values'][0]] if \
            parent_iid != self.root else None
        T_parent = self.archive.meta[parent_key][ac.TYPE] if parent_key \
            else None

        name, value = self.display.item(iid)['values']

        if T_parent is ac.TYPE_MAP:
            self.editor._map_item_editable(name, value)
            return

        if T_parent is ac.TYPE_LIST:
            self.editor._list_item_editable(name, value)
            return

        key = ac.INVERSE[name]
        meta = self.archive.meta[key]
        T = meta[ac.TYPE]

        if T is ac.TYPE_PRIMITIVE:
            self.editor._editable(meta[ac.EDITABLE], value)
            self.editor._addable(False)
            self.editor._removable(False)
            return
        elif T is ac.TYPE_LIST:
            self.editor._list_editable()
            return
        elif T is ac.TYPE_MAP:
            self.editor._map_editable()
            return

        self.editor._untouchable()

    def _on_double(self, event = None):
        """
        To be called on double clicks. Checks whether an item is editable and,
        if so, edits it.
        """
        self._nothing()


    def _on_add(self, value, key = None):
        """
        Callback for when an "addition" to a list is evaluated. Adds the given
        value to the currently selected list (or map) attribute.
        """
        iid = self.display.focus()
        name = self.display.item(iid)['values'][0]
        key = ac.INVERSE[name]

        #self.archive.meta[key][ac.VALIDATOR](value) FIXME

        value = self.archive[self.archive.defaults[key][ac.KEY]]
        self.archive.add(key, value)

        #iid = self.display.insert(iid, 0,
        #    values = ('', value), tag = TAG_PRIMITIVE)
        self.build()

    def _on_edit(self, value):
        """
        Callback for when an attribute's new value is evaluated. Validates the
        given value and stores it within the currently selected attribute.
        """
        iid = self.display.focus()
        name = self.display.item(iid)['values'][0]
        key = ac.INVERSE[name]
        self.archive.meta[key][ac.VALIDATOR](value)
        self.archive.set(key, value)
        self.display.item(iid, values = (name, value))

    def _on_remove(self, event = None):
        """
        Callback for when the Remove button is pressed. Removes the currently
        selected attribute.
        """
        # FIXME
        pass


    # Auxiliary ----------------------------------------------------------------
    def _nothing(*args):
        """
        Placeholder for unnasigned callbacks.
        """
        pass

    def _loadBuiltin(self, name):
        """
        Load the given built-in profile.
        - name := String, name of the built-in profile, as defined in
            fc.builtin.profiles.
        """
        # FIXME TODO GGG
        self.archive.profile(self.builtin[name])
        self.build()
        self.callback()
        return

    def _onBuiltinMenuChange(self, *event):
        """
        Callback for changes to the built-in profile menu.
        """
        name = self.builtinMenuVar.get()
        if name != "N/A":
            self._loadBuiltin(name)

    # Editors ------------------------------------------------------------------
    def _edit_generic(self, attribute, current = None):
        """
        Return the result of evaluating a Python expression to get a value for
        ATTRIBUTE, enforcing the corresponding validator. CURRENT is the current
        value of said attribute, if any.
        """
        print("[WARNING] _edit_generic not yet implemented")
        # TODO
        print(attribute, current)
        self.editor.preset(current)


class PythonEditor(tk.Frame):

    OUTPUT_ERROR_CONFIG = {'bg' : "#510000", 'fg' : "red"}
    OUTPUT_NORMAL_CONFIG = {'bg' : "white", 'fg' : "black"}

    def __init__(self, master, add_callback, edit_callback, remove_callback,
        printr, printx):
        tk.Frame.__init__(self, master)

        self.add_callback = add_callback
        self.edit_callback = edit_callback
        self.remove_callback = remove_callback
        self.printr = printr
        self.printx = printx

        self.grid_columnconfigure(1, weight = 1)
        row = 0

        self.topLabel = tk.Label(self, text = \
            "Value editor (as Python 3.7 expression):", anchor = tk.W)
        self.topLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1

        self.font = tk.font.Font(font = "Courier 12 bold")
        self.tabstr = "  "
        self.tabsize = self.font.measure(self.tabstr)
        self.realtabs = "    "

        # Input ................................................................
        self.grid_rowconfigure(row, weight = 1)
        self.input = tk.Text(self, font = self.font,
            width = 30, height = 2, padx = 10, pady = 0, bg = 'black',
            fg = 'lightgray', insertbackground = "#ff6e1f",
            tabs = self.tabsize)
        self.input.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.input_scrollbar = tk.Scrollbar(self)
        self.input_scrollbar.grid(row = row, column = 2, rowspan = 1,
            sticky = "NS")
        self.input_scrollbar.config(command = self.input.yview)
        self.input.config(yscrollcommand = self.input_scrollbar.set)
        row += 1

        # Buttons ..............................................................
        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.grid(row = row, column = 0, columnspan = 2,
            sticky = "WE")
        self.editButtons = []

        self.addButton = tk.Button(self.buttonFrame, text = "Add to",
            command = self._add)
        self.addButton.pack(side = tk.LEFT)
        self.editButtons.append(self.addButton)

        self.editButton = tk.Button(self.buttonFrame, text = "Edit",
            command = self._edit)
        self.editButton.pack(side = tk.LEFT)
        self.editButtons.append(self.editButton)

        self.removeButton = tk.Button(self.buttonFrame, text = "Remove",
            command = self._remove)
        self.removeButton.pack(side = tk.LEFT)
        self.editButtons.append(self.removeButton)

        row += 1

        # Output ...............................................................
        self.grid_rowconfigure(row, weight = 1)
        self.output = tk.Text(self, font = self.font,
            width = 30, height = 2, padx = 10, pady = 0, tabs = self.tabsize,
            state = tk.DISABLED, **self.OUTPUT_NORMAL_CONFIG)
        self.output.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.output_scrollbar = tk.Scrollbar(self)
        self.output_scrollbar.grid(row = row, column = 2, rowspan = 1,
            sticky = "NS")
        self.output_scrollbar.config(command = self.output.yview)
        self.output.config(yscrollcommand = self.output_scrollbar.set)
        row += 1

    def _eval_error(self, e):
        """
        Handle the case of an exception happening during evaluation.
        """
        # TODO finish (prov)
        self._print("Evaluation error: " + str(e))
        self.output.config(**self.OUTPUT_ERROR_CONFIG)

    def clear(self):
        """
        Clear both text fields.
        """
        self.clear_input()
        self.clear_output()

    def clear_input(self):
        """
        Clear the input text field.
        """
        self.input.delete(1.0, tk.END)

    def clear_output(self):
        """
        Clear the output text field.
        """
        self.output.config(state = tk.NORMAL, **self.OUTPUT_NORMAL_CONFIG)
        self.output.delete(1.0, tk.END)
        self.output.config(state = tk.DISABLED)

    def preset(self, value):
        """
        Set the input to the expression that evaluates to VALUE.
        """
        self.clear()
        self.input.insert(tk.END, str(value) + "\n")

    def _eval(self, *E):
        """
        Evaluate the expression in the input field and return its value.
        """
        raw = self.input.get(1.0, tk.END)
        result = eval(raw)
        self._output(result)
        return result

    def _edit(self, *E):
        """
        To be called when the Edit button is clicked. Parse the expression and
        pass it to the given callback.
        """
        try:
            self.edit_callback(self._eval())
        except Exception as e:
            self._eval_error(e)

    def _add(self, event = None):
        try:
            self.add_callback(None)
        except Exception as e:
            self._eval_error(e)

    def _remove(self, event = None):
        try:
            self.clear()
            self.remove_callback()
        except Exception as e:
            self._eval_error(e)

    def _print(self, text):
        """
        Print TEXT to the output space.
        """
        try:
            self.clear_output()
            self.output.config(state = tk.NORMAL)
            self.output.insert(tk.END, text + "\n")
            self.output.config(state = tk.DISABLED)
        except Exception as e:
            self.printx("Exception when displaying Python output: ", e)

    def _output(self, value):
        """
        Display the generic Python value VALUE in the output space.
        """
        self._print(str(value))

    # Editability functions ----------------------------------------------------
    def _untouchable(self):
        """
        Disable all edit buttons.
        """
        for button in self.editButtons:
            button.config(state = tk.DISABLED)

    def _list_editable(self):
        """
        Enable buttons for a list attribute.
        """
        self._editable(False)
        self._addable(True)
        self._removable(False)

    def _map_editable(self):
        """
        Enable buttons for a map attribute.
        """
        self._editable(False)
        self._addable(True)
        self._removable(False)

    def _list_item_editable(self, index, value):
        """
        Enable buttons for a list item attribute.
        """
        self._editable(True, value)
        self._addable(False)
        self._removable(True)

    def _map_item_editable(self, key, value):
        """
        Enable buttons for a map item attribute.
        """
        self._editable(True,(key, value))
        self._addable(False)
        self._removable(True)

    def _editable(self, value, preset = None):
        """
        Set whether the currently selected value can be edited.
        """
        self.clear_output()
        self.editButton.config(state = tk.NORMAL if value else tk.DISABLED)
        if value and preset:
            self.preset(preset)
        else:
            self.clear_input()

    def _addable(self, value):
        """
        Set whether the currently selected value can be added-to.
        """
        self.addButton.config(state = tk.NORMAL if value else tk.DISABLED)

    def _removable(self, value):
        """
        Set whether the currently selected value can be removed.
        """
        self.removeButton.config(state = tk.NORMAL if value else tk.DISABLED)




## DEMO ########################################################################
