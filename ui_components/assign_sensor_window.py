from tkinter import Toplevel, Label, Button
from tkinter.ttk import Combobox

class AssignSensorWindow(Toplevel):
    def __init__(self, master, address, assignment_ref, params,   **kwargs):
        super().__init__(master,  **kwargs)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        width = 300
        height = 150

        # Calculate the x and y coordinates
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        # Set the geometry of the Toplevel window
        self.geometry('%dx%d+%d+%d' % (width, height, x, y))
        self.title("Assign Sensor")
        #self.iconify()
        self.address = address
        self.params = params

        #self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)


        self.label = Label(self, text=f"{self.address}")
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.placement_select = Combobox(self, values=self.params.get_placements())
                                     #command=self.on_placement_select,) 
        self.placement_select.bind("<<ComboboxSelected>>", self.on_placement_select)
        self.placement_select.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.placement_select.set(self.params.get_placements()[0])
        self.placement_select.current(0)

        self.assignment_ref = assignment_ref

        self.on_placement_select(None)
        
        self.close_button = Button(self, text= "close", command=self.on_close_button_press)
        self.close_button.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
    
    def on_placement_select(self, placement):
        placement = self.placement_select.get()
        print(f"Placement: {placement}")
        self.assignment_ref(self.address, placement)
        self.assigned_label = Label(self, text=f"Assigned to {placement}")
        self.assigned_label.grid(row=2, column=0,padx=5, pady=5, sticky="nsew")

    def on_close_button_press(self):
        self.destroy()
