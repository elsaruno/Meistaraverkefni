from sensor_sdk import helper_functions as hf
import threading
import queue
import multiprocessing
import time
import math
from typing import Literal
from classes.Config import Config
from sensor_sdk.helper_functions import create_transform

class BatteryStatus:
    def __init__(self, battery_level, is_charging):
        self.battery_level = battery_level
        self.is_charging = is_charging

class SensorDataPacket:
    def __init__(self, address, data_packet):
        self.address = address
        self.data_packet = data_packet

class MessageError:
    def __init__(self, error_message):
        self.error_message

## Sensor Classes
class ScannedSensor:
    def __init__(self, address, ble_address, ble_device):
        self.address = address
        self.ble_address = ble_address
        self.ble_device = ble_device

    def get_scanned_sensor_address(self):
        return self.address
    def get_scanned_sensor_ble_device(self):
        return self.ble_device
    
class ConnectedSensor:
    def __init__(self, address, client, ble_device, sensor_manager):

        self.c = Config()
        self.address = address
        self.ble_device = ble_device
        self.ble_client = client
        self.placement = ""
        self.sensor_manager = sensor_manager
        self.batt_level = 0
        self.raw_data = []
        self.data_rate = 0
        self.packet_count = 0
        self.time_pc = []
        self.is_measuring = False
        self.is_first_data_packet = True

        self.time = []
        self.accel_x = []
        self.accel_y = []
        self.accel_z = []
        self.yaw = []
        self.pitch = []
        self.roll = []
        self.max_roll = 0
        self.max_pitch = 0
        self.max_yaw = 0
        self.projected_roll = []
        self.projected_pitch = []
        self.projected_yaw = []
        
        self.prev_timestamp = 0
        self.packet_count = 0
        self.list_of_timestamps = []

        self.ema_roll = None
        self.ema_pitch = None
        self.ema_yaw =  None

        self.yaw_offset = None
        self.pitch_offset = None
        self.roll_offset = None

        
        self.transform = None
        #vars
        self.prev_timestamp = 0
        self.latest_timestamp = 0
        self.result_queue = multiprocessing.Queue()

    def append_timestamp_prev_timestamp(self):
        self.list_of_timestamps.append(self.prev_timestamp)
        print(f"appending prev timestamp {self.prev_timestamp}")
    
    def get_previous_timestamp(self):
        return self.prev_timestamp
    
    def get_space_press_timestamps(self):
        return self.list_of_timestamps

    def set_max_pitch(self, pitch):
        self.max_pitch = pitch
    
    def set_max_roll(self, roll):
        self.max_roll = roll
    
    def set_max_yaw(self, yaw):
        self.max_yaw = yaw

    def set_is_measuring(self, is_measuring):
        self.is_measuring = is_measuring

    def on_button_event(self,sender, event):
        press_type = event[0] # should be 5 for single press
        if(press_type == 5):
            print(f"single button press from {self.address}")
            self.sensor_manager.on_sensor_button_press(self.address, press_type)

    def on_sensor_data(self, sender, data):
        
        # if its the first packet ignore it
        if(self.is_first_data_packet):
            self.is_first_data_packet = False
        else:
            encoded_data = hf.encode_data_packet(data)
        
            self.latest_timestamp = encoded_data[0][0] 
            if(self.prev_timestamp != 0):
                self.update_data_rate(int( 1/((self.latest_timestamp - self.prev_timestamp)/1e6)))
                self.prev_timestamp = self.latest_timestamp
            else:
                self.prev_timestamp = self.latest_timestamp 

            self.add_raw_data_packet(encoded_data)
            #self.packet_count +=1
            roll, pitch, yaw = hf.euler_from_quaternion(encoded_data[0][2], encoded_data[0][3], encoded_data[0][4], encoded_data[0][1] ) 

                # function get accleration depending on payload
            a_x = encoded_data[0][5] # x accel?
            a_y = encoded_data[0][6]
            a_z = encoded_data[0][7] # z accel

            self.accel_x.append(a_x)
            self.accel_y.append(a_y)
            self.accel_z.append(a_z)

            # these are the raw valus converted to degrees
            roll_deg = math.degrees(roll)
            pitch_deg = math.degrees(pitch)
            yaw_deg = math.degrees(yaw)

            self.roll.append(roll_deg)
            self.pitch.append(pitch_deg)
            self.yaw.append(yaw_deg)
            if (roll_deg > self.max_roll):
                self.set_max_roll(round(abs(roll_deg),2))
            if (pitch_deg > self.max_pitch):
                self.set_max_pitch(round(abs(pitch_deg),2))
            if(yaw_deg > self.max_yaw):
                self.set_max_yaw(round(abs(yaw_deg), 2))
            

            if self.c.transform_mode == 'yaw_offset':
                if(self.packet_count == 0):
                    # capture the angles for offset correction
                    self.yaw_offset = yaw
                    self.pitch_offset = pitch
                pitch_moving_avg = pitch-self.pitch_offset
                yaw_moving_avg = yaw - self.yaw_offset

                #x = self.c.x_ref + (self.c.max_rotation * math.cos(pitch_moving_avg) * math.sin(yaw_moving_avg))
                #y = self.c.y_ref + (self.c.max_flex_ext * math.sin(pitch_moving_avg))
                x = self.c.x_ref + (self.c.max_rotation * math.cos(pitch_moving_avg) * math.cos(yaw_moving_avg))
                y = self.c.y_ref + (self.c.max_flex_ext * math.sin(pitch_moving_avg))
                
                #print(f"x :{x} y: {y}")
                #self.projected_roll.append(math.degrees(roll_moving_avg))
            elif self.c.transform_mode == 'quaternion':
                q_arr = (encoded_data[0][1], encoded_data[0][2], encoded_data[0][3], encoded_data[0][4] )
                
                if(self.packet_count == 0):
                    self.transform = create_transform(q_arr, self.c.sensor_model)
                x, y = self.transform(q_arr)

            self.projected_pitch.append(y)
            self.projected_yaw.append(x)
            self.time.append(self.packet_count)
            self.packet_count +=1
            

            #print(f"x :{x} y: {y}")
            #self.projected_roll.append(math.degrees(roll_moving_avg))
            

    def on_battery_status_update(self, sender, batt):
        battery_level = hf.get_battery_level(batt)
        self.batt_level = battery_level.battery_level
        self.sensor_manager.on_battery_status(self.address, battery_level.battery_level)
    
    def get_address(self):
        return self.address
    
    def get_placement(self):
        return self.placement
    
    def set_placement(self, placement):
        self.placement = placement
    
    def set_set_data_rate(self, rate):
        self.set_data_rate = rate
    
    def get_set_data_rate(self):
        return self.set_data_rate
    
    def update_data_rate(self, rate):
        # compute the data rate from timestamps
        self.data_rate = rate

    def get_batt_level(self):
        return self.batt_level
    
    def get_last_data_rate(self):
        return self.data_rate
    
    def add_raw_data_packet(self, data_packet):
        self.raw_data.append(data_packet)

    def get_raw_data(self):
        return self.raw_data
    
    def remove_raw_data(self):
        self.raw_data = []
    
    def get_projected_roll(self):
        return self.projected_roll

    def get_projected_pitch(self):
        return self.projected_pitch
    
    def get_projected_yaw(self):
        return self.projected_yaw
    
    def get_accel(self):
        if len(self.time) > 0:
            n = self.c.get_number_of_plot_points()
            print(self.c.number_of_plot_points)
            return self.time[-n:], self.accel_x[-n:], self.accel_y[-n:], self.accel_z[-n:]
        else:
            return [0], [0], [0], [0]
        
    def get_euler(self):
        if len(self.time) > 0:
            n = self.c.get_number_of_plot_points()
            print(self.c.number_of_plot_points)
            return self.time[-n:], self.roll[-n:], self.pitch[-n:], self.yaw[-n:]
        else:
            return [0], [0], [0], [0]
        
    def clear_all_data(self):
        self.raw_data = []
        self.packet_count = 0
        self.time = []
        self.accel_x = []
        self.accel_y = []
        self.accel_z = []
        self.roll = []
        self.pitch = []
        self.yaw = []
        self.projected_pitch = []
        self.projected_roll = []
        self.projected_yaw = []
        self.prev_timestamp = 0
    
    def get_packet_count(self):
        return self.packet_count
    
    def get_length_raw_data(self):
        return len(self.raw_data)
    
