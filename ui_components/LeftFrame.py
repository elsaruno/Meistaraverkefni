from tkinter import Button,Frame

from ui_components.SideBar import SideBar


class LeftFrame(Frame):
    def __init__(self, master, console_frame, s, c, p, plot_frame,  *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s=s
        self.c=c
        self.p = p
        self.plot_frame = plot_frame
        self.console_frame = console_frame
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.sidebar = SideBar(self,self.console_frame, self.s, self.c, self.p, self.plot_frame)