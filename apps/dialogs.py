from Tkinter import *

class GridDialog(Toplevel):
    def __init__(self, parent, title=None):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.grid(padx=5, pady=5)

        self.wait_visibility()
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        if self.parent is not None:
            self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                      parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    def cancel(self):
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

    def body(self, master):
        pass

    def validate(self):
        pass
        return 1

    def destroy(self):
        '''Destroy the window'''
        self.initial_focus = None
        Toplevel.destroy(self)

    def ok(self, event=None):
        if not self.validate():
                self.initial_focus.focus_set()
                return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()


