
from tkinter import PanedWindow, Frame, LabelFrame,Label, Button, BOTH

class SideBar(PanedWindow):
     def __init__(self, master, console_frame, s, c, p, plot_frame, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s
        self.c = c
        self.p = p
        self.plot_frame = plot_frame
        self.configure(orient="vertical",  sashwidth = 5)
        self.grid(row=0, column=0,rowspan=2,columnspan=1, sticky='news')
        self.grid_rowconfigure(0, weight=1)

        
        self.scan_and_connect_frame = ScanSensorFrame(self, console_frame, self.s, self.c, self.p, self.plot_frame)
        self.console_frame = console_frame

        self.scan_button_frame = LabelFrame(self)
        self.scan_button =  Button(self.scan_button_frame,text='Scan',command=self.scan_and_connect_frame.scan_for_sensors)
        self.scan_button.grid(row=0, column=0,  sticky='ew',padx=5,pady=5)
        self.scan_button_frame.configure(text = "Scan For Sensors",)

        self.add(self.console_frame)
        self.add(self.scan_button_frame)
        self.add(self.scan_and_connect_frame)

class ScanSensorFrame(LabelFrame):
    def __init__(self, master,console_frame, s, c, p, plot_frame, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s
        self.c = c
        self.p = p
        self.plot_frame = plot_frame
        self.console_frame = console_frame

        # these are to update the UI
        self.s.set_discovered_sensors_callback(self.discovered_senors)
        self.s.set_connected_sensors_callback(self.connected_sensor)
        #self.s.set_battery_status_callback(self.battery_status)
       
        self.configure(text = "Discovered Sensors",)
        self.grid(row=0, column=0,rowspan=1,columnspan=1, sticky='nesw')

        self.info_label = Label(self, text=f"Only a maximum of 2 sensors will be discovered")
        self.info_label.grid(row=0, column=0, pady=5)
       

        self.scanned_sensors_frame = Frame(self)
        self.scanned_sensors_frame.grid(row=1, column=0,  sticky='ew', padx=5, pady=5)

    def scan_for_sensors(self):
        # send the message to the sensor manager on the sensors class
        self.s.manager.send_message("scan", {})
        self.console_frame.clear_console()
        self.console_frame.insert_text("scanning for dots ..." + '\n\n') 

    def connect_to_sensor(self, address):
        print(address, "connect to")
        self.s.manager.send_message("connect", address)
        self.console_frame.clear_console()
        self.console_frame.insert_text(f"connecting to dot {address} ..." + '\n\n') 
        
    def connected_sensor(self, sensor):
        print(f"UI connected to {sensor}")
        self.console_frame.clear_console()
        self.console_frame.insert_text("Connected to Dot: " + sensor.address + " " +'\n')

        num_of_sensors = self.plot_frame.get_sensors_in_plot_frame()-1
        self.plot_frame.set_sensor_position(sensor.address, num_of_sensors+1)
        print("row", num_of_sensors+1)
        # do we want a sensor actions object to update parameters?
        sensor_actions = {
            "address": sensor.address,
            "position": num_of_sensors+1,
            "disconnect_button": None,
            "identify_button" : None,
            "batt_label" : None,
            "data_rate_label": None,
            "placement_label": None,
        }

        connected_sensor_address_label = Label(self.plot_frame.connected_sensor_frame, text=f"{sensor.address}")
        connected_sensor_address_label.grid(row=num_of_sensors+1, column=0, padx=5, pady=5,sticky="nsw")
        connected_sensor_address_label.identifier = "address"

        connected_sensor_identity_button = Button(self.plot_frame.connected_sensor_frame, text="identify", command= lambda: self.plot_frame.identify_sensor(sensor.address))
        connected_sensor_identity_button.configure(bg="red", fg="black")
        connected_sensor_identity_button.grid(row=num_of_sensors+1, column=1, padx=5,pady=5, sticky="nsw")
        connected_sensor_identity_button.identifier = "indentify_btn"
        sensor_actions["identify_button"] = connected_sensor_identity_button

        connected_sensor_batt_label = Label(self.plot_frame.connected_sensor_frame, text=f"{sensor.batt_level}%")
        connected_sensor_batt_label.grid(row=num_of_sensors+1, column=2, padx=5, pady=5, sticky="nsw")
        connected_sensor_batt_label.identifier = "batt_status"
        sensor_actions['batt_label'] = connected_sensor_batt_label

        disconnect_sensor_btn = Button(self.plot_frame.connected_sensor_frame, text="disconnect",
                                          command= lambda: self.plot_frame.disconnect_from_sensor(sensor.address))
        disconnect_sensor_btn.grid(row=num_of_sensors+1, column=3, padx=5, pady=5, sticky="nsw")
        disconnect_sensor_btn.identifier = "disconnect_btn"
        sensor_actions['disconnect_button'] = disconnect_sensor_btn

        connected_sensor_data_rate_label = Label(self.plot_frame.connected_sensor_frame, text=f"60 Hz", )
        connected_sensor_data_rate_label.grid(row=num_of_sensors+1, column=4, padx=5, pady=5, sticky="nsw")
        connected_sensor_data_rate_label.identifier = "data_rate"
        sensor_actions["data_rate_label"] = connected_sensor_data_rate_label

        
        #self.plot_frame.start_measuring_button = Button(self.plot_frame.connected_sensor_frame, text="start measuring", command= lambda: self.plot_frame.start_measuring_for_sensor(sensor.address))
        #self.plot_frame.start_measuring_button.grid(row=0, column=3)
        #self.plot_frame.stop_measuring_button = Button(self.plot_frame.connected_sensor_frame, text="stop measuring", command= lambda: self.plot_frame.stop_measuring_for_sensor(sensor.address))
        #self.plot_frame.stop_measuring_button.grid(row=0, column=4)
        #self.plot_frame.disconnect_button = Button(self.plot_frame.connected_sensor_frame, text="disconnect", command= lambda: self.plot_frame.disconnect_from_sensor(sensor.address))
        #self.plot_frame.disconnect_button.grid(row=0, column=5)

        self.plot_frame.append_sensor_actions(sensor_actions)

    def discovered_senors(self, sensors):
        #TODO: only return 2 sensors
        print(f" discovered sensors on UI {sensors}")
        labels = []
        connect_buttons = []

        def connect_lambda(address):
            return lambda: self.connect_to_sensor(address)
    
        if(len(sensors)> 0):
            self.console_frame.clear_console()
            for idx, s in enumerate(sensors):
                if idx<2:
                    self.console_frame.insert_text("Dot found: " + s.address + " " +'\n')
                    label = Label(self.scanned_sensors_frame, text=f"{s.address}")
                    labels.append(label)
                    connect_button = Button(self.scanned_sensors_frame, text="connect", command=connect_lambda(s.address))
                    connect_buttons.append(connect_button) 

            for i in range(len(labels)):
                labels[i].grid(row=i, column=0, padx=1, pady=5)
                connect_buttons[i].grid(row=i, column=1, padx=1, pady=5)    
        else:
            self.console_frame.clear_console()
            self.console_frame.insert_text("NO Dots found")