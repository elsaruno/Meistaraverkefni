from sensor_sdk import SensorManager as sm
from sensor_sdk import data_classes as dc
from sensor_sdk import sensor_config as sc
import time


# could this be placed in the SDK and thus created for the developer
class LocalSensorManager:
    def __init__(self):
        # sensor manager data
        self.manager = sm.SensorManager()
    
        # imlpemented callbacks
        self.manager.on_sdk_init = self.on_sdk_init
        self.manager.on_sensors_discovered = self.on_sensors_discovered
        self.manager.on_sensor_connected = self.on_sensor_connected
        self.manager.on_sensor_disconnected = self.on_sensor_disconnected
        self.manager.on_battery_status = self.on_battery_status
        self.manager.on_sensor_data = self.on_sensor_data
        self.manager.on_message_error = self.on_message_error
        self.manager.on_sensor_button_press = self.on_sensor_button_press
        self.manager.export_to_csv_done_callback = self.on_export_to_csv_done
        
        # callback references 
        self.discovered_sensors = None
        self.connected_sensor = None
        self.sensor_disconnected = None
        self.sensor_data = None
        self.stop_sensor_data = None
        self.battery_status = None
        self.export_done_callback = None
        self.sensor_button_press_callback = None
       
    # callback references from UI components that need the data
   
    def set_discovered_sensors_callback(self, func):
        self.discovered_sensors = func
    
    def set_connected_sensors_callback(self, func):
        self.connected_sensor = func
    
    def set_sensor_disconnected_callback(self, func):
        self.sensor_disconnected = func

    def set_sensor_data_callback(self, func):
        self.sensor_data = func
    
    def set_stop_sensor_data_callback(self, func):
        self.stop_sensor_data = func

    def set_battery_status_callback(self, func):
        self.battery_status = func

    def set_export_done_callback(self, func):
        self.export_done_callback = func

    def set_sensor_button_press_callback(self, func):
        self.sensor_button_press_callback = func

    # sensor manager callbacks
    def on_sdk_init(self, done: bool):
        print(f"sdk init: {done}")

    def on_export_to_csv_done(self, address):
        self.export_done_callback(address)

    def on_battery_status(self, address, batt_level):
        print(f"sensor {address} battery level {batt_level}%")
        self.battery_status(address, batt_level)

    def on_sensors_discovered(self, scanned_sensors: dc.ScannedSensor):
        print(f"LM: Discovered sensors {scanned_sensors}")
        self.discovered_sensors(scanned_sensors)

    def on_sensor_connected(self, connected_sensor: dc.ConnectedSensor):
        print(f"Connected Sensor {connected_sensor.address}")
        self.connected_sensor(connected_sensor)

    def on_sensor_disconnected(self, address: str):
        print(f"sensor {address} disconnected")
        self.sensor_disconnected(address)

    def on_sensor_button_press(self, address: str, press_type:int):
        self.sensor_button_press_callback(address, press_type)
    
    def on_sensor_data(self, data_packet: dc.SensorDataPacket):
        self.sensor_data(data_packet)
    
    def on_message_error(self, error: dc.MessageError):
        print(f"message error: {error.error_message}")

    # manager interface
    def get_supported_sensors(self):
        supported_sensors = self.manager.get_supported_sensors()
        print(f"LM: get supported sensors: {supported_sensors}")
        return supported_sensors

    def initialise_sdk(self):
        self.manager.init_sdk(["Movella Dot", "OsteoSense"])

    

    