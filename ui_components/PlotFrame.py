from tkinter import LabelFrame,Frame,Label, Button, DISABLED,messagebox, StringVar, OptionMenu
from tkinter import TclError
from matplotlib.pyplot import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)
from matplotlib import style
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
#style.use('fivethirtyeight')
style.use("dark_background")
from ui_components import assign_sensor_window as asw
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

class PlotFrame(LabelFrame):
    def __init__(self, master, console_frame, s, c, p, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s
        self.console_frame = console_frame
        self.c = c
        self.p = p
        self.rate = c.data_rate
        self.max_roll = 0
        self.max_pitch = 0
        self.max_yaw = 0
        self.configure(text="Visualisation",)

        self.list_of_timestamps = []
        self.connected_sensor_positions = {}
        self.timestamp_counter = 0

        self.grid_rowconfigure((2,), weight=1)
        self.grid_columnconfigure((0, 1), weight=1)  # Column weight

        self.s.set_stop_sensor_data_callback(self.stop_sensor_callback)
        self.s.set_battery_status_callback(self.battery_status_callback)
        self.s.set_sensor_button_press_callback(self.on_sensor_button_press)
        self.s.set_export_done_callback(self.export_to_csv_done_callback)
        self.s.set_sensor_disconnected_callback(self.on_sensor_disconnected)

        self.connected_sensor_actions = []
        self.assign_sensor_window = None

        self.connected_sensor_frame = Frame(self)
        self.connected_sensor_frame.grid(row=0, column=0, columnspan=7, sticky="new",)
        # self.connected_sensor_frame.grid_columnconfigure(6,weight=1)
        # self.connected_sensor_frame.grid_rowconfigure((0,1), weight=1)
        # self.connected_sensor_frame.grid_propagate(False)

        self.start_stop_frame = Frame(self)
        self.start_stop_frame.grid(row=1, column=0, columnspan=7, sticky="nsew")

        self.streaming_button = Button(self.start_stop_frame, text="Start Streaming", command=lambda: self.start_measuring_for_sensors())
        self.streaming_button.grid(row=1, column=0, padx=5, pady=5, sticky="nsw")
        self.streaming_button.configure(bg="green", fg="black")

        self.start_button = Button(self.start_stop_frame, text="Start Measuring", command=lambda: self.start_plotting())
        self.start_button.grid(row=1, column=1, padx=5, pady=5, sticky="nsw")
        self.start_button.configure(bg="blue", fg="black")

        self.stop_button = Button(self.start_stop_frame, text="Stop Measuring", command=lambda: self.stop_measuring_for_sensors())
        self.stop_button.grid(row=1, column=2, padx=5, pady=5, sticky="nsw")
        self.stop_button.configure(bg="orange", fg="black")

        self.timestamp_button = Button(self.start_stop_frame, text="Mark Timestamp", command=lambda: self.save_timestamp())
        self.timestamp_button.grid(row=1, column=3, padx=5, pady=5, sticky="nsw")
        self.timestamp_button.configure(bg="purple", fg="black")

        
        # Dropdown menu for choosing the shape
        self.shape_choice = StringVar(value="circle")  # Default value
        self.shape_dropdown = OptionMenu(self.start_stop_frame, self.shape_choice, "circle", "infinity", "trajectory")
        self.shape_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.difficulty_level = StringVar(value="easy")  # Default value
        self.difficulty_dropdown = OptionMenu(self.start_stop_frame, self.difficulty_level, "easy", "medium", "hard")
        self.difficulty_dropdown.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        # figures
        self.projected_angles = Figure()
        self.ax_proj = self.projected_angles.subplots()
        self.ax_proj.set_title(f"Projected Pitch and Yaw")
        self.ax_proj.set_xlim(-50, 50)
        self.ax_proj.set_ylim(-50, 50)
        self.ax_proj.spines['left'].set_position('center')
        self.ax_proj.spines['bottom'].set_position('center')
        self.ax_proj.spines['right'].set_color('none')
        self.ax_proj.spines['top'].set_color('none')
        self.ax_proj.xaxis.set_ticks_position('bottom')
        self.ax_proj.yaxis.set_ticks_position('left')
        self.ax_proj.autoscale(True)
        if self.timestamp_counter == 0:
            self.ax_proj.text(0.5, 1.1, 'Welcome, to begin connect the sensor and press start streaming button', transform=self.ax_proj.transAxes, ha='center', fontsize=12)
        elif self.timestamp_counter == 1:
            self.ax_proj.texts.clear()
            self.ax_proj.text(0.5, 1.1, 'Now let the sensor sit on the table for a few seconds and then press mark timestamp button', transform=self.ax_proj.transAxes, ha='center', fontsize=12)
        elif self.timestamp_counter == 2:
            self.ax_proj.texts.clear()
            self.ax_proj.text(0.5, 1.1, 'Now place the sensor and raise the hand as high as you can but not higher than 90°C and press start measuring', transform=self.ax_proj.transAxes, ha='center', fontsize=12)

        # try and draw a circle
        self.circle_x = 30 * np.sin(np.linspace(0, 2 * np.pi, 100))
        self.circle_y = 30 * np.cos(np.linspace(0, 2 * np.pi, 100))

        # try and draw a figure of 8 / infinity symbol
        t = np.linspace(0, 2 * np.pi, 100)  # 100 ensures a smooth shape

        # # ammend these so to make the shape what you want
        self.infinity_x = 50 * np.sin(t)
        self.infinity_y = 50 * np.sin(t) * np.cos(t) * 1.2

        # # Create a path for the figure of eight
        # vertices = np.column_stack([x, y])
        # codes = [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 1)
        # figure_of_eight_path = Path(vertices, codes)
        # figure_of_eight_patch = patches.PathPatch(figure_of_eight_path, edgecolor='orange', facecolor='none', linewidth=2)

        # # Add the patch to the axes
        # self.ax_proj.add_patch(figure_of_eight_patch)
        #TODO: Virkar til að sýna trajectory en kemur öfugt
        script_dir = os.path.dirname(__file__)
        file_x_path = os.path.join(script_dir, "trajectory_x.txt")
        file_y_path = os.path.join(script_dir, "trajectory_y.txt")
        file_x = open(file_x_path, "r")
        trajectory_x = file_x.read().splitlines()
        self.trajectory_x = np.array(trajectory_x, dtype=float)
        file_y = open(file_y_path, "r")
        trajectory_y = file_y.read().splitlines()
        self.trajectory_y = np.array(trajectory_y, dtype=float)
        self.trajectory_y = -self.trajectory_y

        self.trajectory_x = self.trajectory_x * 70
        self.trajectory_y = self.trajectory_y * 70

        vertices = np.column_stack([self.trajectory_x, self.trajectory_y])
        codes = [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 1)
        figure_of_eight_path = Path(vertices, codes)
        figure_of_eight_patch = patches.PathPatch(figure_of_eight_path, edgecolor='orange', facecolor='none', linewidth=2)

        # Add the patch to the axes
        self.ax_proj.add_patch(figure_of_eight_patch)
        self.projected_angles_canvas = FigureCanvasTkAgg(self.projected_angles, master=self)
        self.projected_angles_canvas.get_tk_widget().grid(row=2, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Initialize variables for tracing
        self.traced_x = []
        self.traced_y = []
        self.current_idx = 0

        self.init_key_press()

    # this now works but only if you are on focus

    def init_key_press(self):
        print("init key press")
        self.bind("<Key>", self.dectect_key_press)
        self.focus_set()
        # ensure focus is given back to the frame 
        self.bind('<Visibility>', self.focus_set())
    
    def on_sensor_disconnected(self, address):
        # need to remove all the buttons associated with connected and return to just connect
        pos = self.connected_sensor_positions[address]
        for widget in self.connected_sensor_frame.grid_slaves(row=pos):
            if(hasattr(widget, "identifier")): 
                if(widget.identifier == "indentify_btn"):
                    print("destroying indentify button")
                    if widget.winfo_exists():
                        widget.destroy()
                    else:
                        print("The button does not exist.")


                # error here for some unknown reason (on macos)
                elif(widget.identifier == "disconnect_btn"):
                    print("destroying disconnect button")
                    try:
                        if widget.winfo_exists():
                            widget.destroy()
                    except TclError as e:
                        print(f"Error while destroying the button: {e}")
                    
                elif(widget.identifier == "batt_status"):
                     widget.destroy()


                elif(widget.identifier == "data_rate"):
                     widget.destroy()
                
                elif(widget.identifier == "placement_label"):
                     widget.destroy()


                elif(widget.identifier == "address"):
                     widget.destroy()


        print(f"sensor {address} disconnected ")


        sensor_action = [sa for sa in self.connected_sensor_actions if sa["address"] == address][0]
        self.connected_sensor_actions.remove(sensor_action)
        self.console_frame.clear_console()
        self.console_frame.insert_text(f"sensor {address} disconnected")


    def append_sensor_actions(self, actions):
        print("appending sensor actions")
        self.connected_sensor_actions.append(actions)


    def set_sensor_position(self, address, position):
        self.connected_sensor_positions[address] = position


    def get_sensors_in_plot_frame(self):
        return len(self.connected_sensor_actions)

    def save_timestamp(self):
        print("saving timestamp")
        self.timestamp_counter += 1
        self.s.manager.send_message("timestamp_button_pressed", {})
        self.console_frame.insert_text(f"timestamp saved ..." + '\n\n')

        # Clear previous text and update it
        self.ax_proj.cla()  # Clear axis to remove old text
        self.ax_proj.set_title("Projected Pitch and Yaw")  # Reset title
        self.ax_proj.set_xlim(-50, 50)
        self.ax_proj.set_ylim(-50, 50)
        self.ax_proj.spines['left'].set_position('center')
        self.ax_proj.spines['bottom'].set_position('center')
        self.ax_proj.spines['right'].set_color('none')
        self.ax_proj.spines['top'].set_color('none')
        self.ax_proj.xaxis.set_ticks_position('bottom')
        self.ax_proj.yaxis.set_ticks_position('left')

        if self.timestamp_counter == 1:
            self.ax_proj.text(0.5, 1.1, 'Now let the sensor sit on the table for a few seconds and then press mark timestamp button',
                            transform=self.ax_proj.transAxes, ha='center', fontsize=12)
        elif self.timestamp_counter == 2:
            self.ax_proj.text(0.5, 1.1, 'Now place the sensor and raise the hand as high as you can but not higher than 90° and press start measuring',
                            transform=self.ax_proj.transAxes, ha='center', fontsize=12)
        # Redraw canvas
        self.projected_angles_canvas.draw()

    def dectect_key_press(self, event):
        #<KeyPress event keysym=space keycode=822083616 char=' ' x=256 y=222>
        if(event.keysym == "space"):
            self.timestamp_counter += 1
            self.s.manager.send_message("space_key_pressed", {})
            # send a message to the sensor manager?
            #save a timestamp for both sensors
            
    def set_max_pitch(self, pitch):
        self.max_pitch = pitch
    
    def set_max_roll(self, roll):
        self.max_roll = roll
    
    def set_max_yaw(self, yaw):
        self.max_yaw = yaw

#callbacks
    def update_stream_plot(self):
        colors = ["blue", "orange", "grey"]

        self.ax_proj.clear()
        self.ax_proj.set_title(f"Projected Pitch and Roll")
        self.ax_proj.set_xlim(-50, 50)
        self.ax_proj.set_ylim(-50, 50)
        self.ax_proj.spines['left'].set_position('center')
        self.ax_proj.spines['bottom'].set_position('center')
        self.ax_proj.spines['right'].set_color('none')
        self.ax_proj.spines['top'].set_color('none')
        self.ax_proj.xaxis.set_ticks_position('bottom')
        self.ax_proj.yaxis.set_ticks_position('left')
        self.ax_proj.autoscale(False)
        self.ax_proj.text(0.5, 1.1, 'Now follow the trajectory', transform=self.ax_proj.transAxes, ha='center', fontsize=12)
        #Determine which shape to draw
        if self.shape_choice.get() == "circle":
            shape_x = self.circle_x
            shape_y = self.circle_y
        elif self.shape_choice.get() == "infinity":
            shape_x = self.infinity_x
            shape_y = self.infinity_y
        elif self.shape_choice.get() == "trajectory":
            shape_x = self.trajectory_x
            shape_y = self.trajectory_y
        else:
            shape_x, shape_y = [], []

    # Add the next point from full circle to the traced path
        if self.current_idx < len(shape_x):
            self.traced_x.append(shape_x[self.current_idx])
            self.traced_y.append(shape_y[self.current_idx])
            self.current_idx += 1
        else:
        # Reset the traced path to start the effect again (disappear and reform)
            self.traced_x = []
            self.traced_y = []
            self.current_idx = 0

    # Plot the traced portion of the circle
        self.ax_proj.plot(self.traced_x, self.traced_y, color='g')

        sensors_to_plot = self.s.manager.get_connected_sensors()

        for idx, s in enumerate(sensors_to_plot):
           projected_yaw = s.get_projected_yaw()
           projected_pitch = s.get_projected_pitch()
           color = colors[idx]
           self.ax_proj.plot(projected_yaw, projected_pitch, color=color)

    # Redraw the canvas
        self.projected_angles_canvas.draw()
    
    # set the time between updates on the plot (difficulty level)
        diff_level = 0
        if self.difficulty_level.get() == "easy":
            diff_level = 350
        if self.difficulty_level.get() == "medium":
            diff_level = 200
        if self.difficulty_level.get() == "hard":
            diff_level = 50
        
    # Recursively call this function for continuous updates
        self.update_stream_plot_task_id = self.after(diff_level, self.update_stream_plot)  # Adjust speed here
    

    # Rest of your original code is unchanged...

        #NOT needed for more than one sensor as threads
        #if len(sensors_to_plot)<2:
        #    thread1 = threading.Thread(target=self.clear_and_plot( self.ax, self.stream_fig_canvas, f"Acceleration", "packet count", sensors_to_plot))
        #    thread2 = threading.Thread(target=self.clear_and_plot_euler( self.ax_2d, self.twoD_plot_canvas, f"Euler Angles", "packet count", sensors_to_plot ))
        #    # Start the threads
        #    thread1.start()
        #    thread2.start()
            # Wait for both threads to complete
        #    thread1.join()
        #    thread2.join()


    def assign_sensor_ref(self, address, assignment):
        print(f"UI: {address} {assignment}")
        sensor = self.s.manager.get_connected_sensor_by_address(address)
        sensor.set_placement(assignment)
        sensor_actions = [sa for sa in self.connected_sensor_actions if sa["address"] == address][0]

        if(sensor_actions["placement_label"] != None):
            sensor_actions["placement_label"].destroy()

        placement_label = Label(self.connected_sensor_frame, text=f"{assignment}")
        placement_label.grid(row=sensor_actions["position"], column=5, sticky="nesw")
        placement_label.identifier = "placement_label"
        sensor_actions["placement_label"] = placement_label

    def on_sensor_button_press(self, address, press_type):
        if(press_type == 5):
            print(f"button press from {address}")
            if self.assign_sensor_window is None or not self.assign_sensor_window.winfo_exists():
                print("show top level window")
                self.assign_sensor_window = asw.AssignSensorWindow(self, address, self.assign_sensor_ref, self.p)  # create window if its None or destroyed
            else:
                self.assign_sensor_window.focus()  # if window exists focus it
        
    def battery_status_callback(self, address, battery):
        print(f"ui batt status {address} {battery}%")

        if (len(self.connected_sensor_actions) == len(self.s.manager.get_connected_sensors())):
           sensor_actions = [sa for sa in self.connected_sensor_actions if sa["address"] == address][0]
           sensor_actions['batt_label'].configure(text=f"{battery}%")    
    
    def stop_sensor_callback(self, address):
        print(f"stopped sensor {address}")
        self.console_frame.clear_console()
        self.console_frame.insert_text(f"stopped sensor {address} ..." + '\n\n') 

    # frame functions
    def identify_sensor(self, address):
        print(f"indentifying sensor {address}")
        self.s.manager.send_message("identify", address)
        self.console_frame.clear_console()
        self.console_frame.insert_text(f"indentifying sensor {address} ..." + '\n\n') 

    def disconnect_from_sensor(self, address):
        self.s.manager.send_message("disconnect", address)
        self.console_frame.clear_console()
        self.console_frame.insert_text(f"disconnecting sensor {address} ..." + '\n\n') 

    def start_measuring_for_sensors(self):
        self.focus_set()
        self.timestamp_counter = 1  # Reset timestamp counter

        # Update the plot text
        self.ax_proj.cla()
        self.ax_proj.set_title("Projected Pitch and Yaw")
        self.ax_proj.set_xlim(-50, 50)
        self.ax_proj.set_ylim(-50, 50)
        self.ax_proj.spines['left'].set_position('center')
        self.ax_proj.spines['bottom'].set_position('center')
        self.ax_proj.spines['right'].set_color('none')
        self.ax_proj.spines['top'].set_color('none')
        self.ax_proj.xaxis.set_ticks_position('bottom')
        self.ax_proj.yaxis.set_ticks_position('left')

        if self.timestamp_counter == 1:
            self.ax_proj.text(0.5, 1.1, 'Now let the sensor sit on the table for a few seconds and then press mark timestamp button',
                            transform=self.ax_proj.transAxes, ha='center', fontsize=12)
        elif self.timestamp_counter == 2:
            self.ax_proj.text(0.5, 1.1, 'Now place the sensor and raise the hand as high as you can but not higher than 90° and press start measuring',
                            transform=self.ax_proj.transAxes, ha='center', fontsize=12)

        self.projected_angles_canvas.draw()
        #print(f"start measuring for sensor {address}")
        if len(self.connected_sensor_actions) == 0:
            all_sensors_are_placed = False
        else:
            all_sensors_are_placed = all(action.get('placement_label') is not None for action in self.connected_sensor_actions)
            print("placed:", all_sensors_are_placed)

        if all_sensors_are_placed:
            #self.ax.clear()
            #self.ax_2d.clear()
            #start_measuring_all
            self.s.manager.send_message("start_measuring_all", {})
            self.console_frame.clear_console()
            self.console_frame.insert_text(f"start streaming ..." + '\n\n') 
            #self.update_stream_plot()
        else:
            if len(self.connected_sensor_actions) == 0:
                messagebox.showinfo("Alert", "There are no connected sensors")
            else:
                messagebox.showinfo("Alert", "All sensors are NOT assigned")
    
    def start_plotting(self):
        self.console_frame.insert_text(f"start measuring  ..." + '\n\n')
        self.update_stream_plot()
    
    def stop_measuring_for_sensors(self):
        print(f"stop measuring for sensors")
        self.after_cancel(self.update_stream_plot_task_id)
        self.s.manager.send_message("stop_measuring_all", {})
        self.console_frame.clear_console()
        self.console_frame.insert_text(f"stop measuring  ..." + '\n\n') 
        self.export_button = Button(self.start_stop_frame,  text="export to csv", command= lambda: self.export_to_csv())
        self.export_button.configure(bg="#ED8E5A")
        self.export_button.grid(row=1, column=7)
        
    def export_to_csv(self):
        #self.console_frame.clear_console()
        print(f"export to csv: dummy function")
        for s in self.s.manager.get_connected_sensors():
            address = s.get_address()
            self.s.manager.send_message("export", address, data=self.list_of_timestamps )
            self.console_frame.insert_text(f"writing sensor {address} data to csv ..." + '\n\n') 
        
    def export_to_csv_done_callback(self, address):
        print(f"export for {address} done")
       
        self.console_frame.insert_text(f"export for {address} done" + '\n\n') 
        #remove export button from grid
        self.export_button.destroy()

    # NOT USED IN THIS VERSION
    def clear_and_plot(self, axis, canvas, title, x_label, sensors_to_plot):
        axis.clear()
        axis.set_title(title)
        axis.set_xlabel(x_label)

        for idx, s in enumerate(sensors_to_plot):
            t,x,y,z = s.get_accel()
            
            axis.plot(t, x)
            axis.plot(t, y)
            axis.plot(t, z)
        canvas.draw()
    
    def clear_and_plot_euler(self, axis, canvas, title, x_label, sensors_to_plot):
        axis.clear()
        axis.set_title(title)
        axis.set_xlabel(x_label)

        for idx, s in enumerate(sensors_to_plot):
            t,roll, pitch, yaw = s.get_euler()

            axis.plot(t, roll)
            axis.plot(t, pitch)
            axis.plot(t, yaw)
        canvas.draw()