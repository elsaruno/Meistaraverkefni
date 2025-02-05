#tkinter
from tkinter import Tk
from classes.Config import Config
from ui_components.Title import Title
from ui_components.AppCanvas import AppCanvas
from classes.LocalSensorManager import LocalSensorManager
import classes.Params as p
import os, sys, signal

# main application class
class MainApplication(Tk):
    def __init__(self):
        super().__init__()

        self.sensor_manager = LocalSensorManager()
        # application specific configuration
        self.c = Config()
        params = p.Parameters()

        self.sensor_manager.initialise_sdk()

        # screen setup
        self.width =  Tk.winfo_screenwidth(self)
        self.height = Tk.winfo_screenheight(self)
        self.geometry(f"{self.width}x{self.height}")
        self.title("powered by Right Step")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.canvas = AppCanvas(self, self.sensor_manager, self.c, params)
        self.title_label = Title(self, text="Joint Kinematics - Reykjavík University")
        

    def on_keyboard_interrupt(self, event):
            print("killing app", event)
            #self.sensor_manager.manager.stop_thread()
            app.destroy()
            os._exit(0)

if __name__ == "__main__":
    app = MainApplication()
    app.bind("<Control-c>", app.on_keyboard_interrupt)
    app.mainloop()
    

