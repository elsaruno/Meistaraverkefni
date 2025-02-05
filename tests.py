from tkinter import LabelFrame,Frame,Label, Button, DISABLED,messagebox
from tkinter import TclError
from tkinter import Tk


def keydown(e):
    print(e)
    print ('down', e.char)

root = Tk()
frame = Frame(root, width=100, height=100)
frame.bind("<KeyPress>", keydown)
#frame.bind("<KeyRelease>", keyup)
frame.pack()
frame.focus_set()
root.mainloop()