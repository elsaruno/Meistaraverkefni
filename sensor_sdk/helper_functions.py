from bleak import BleakScanner
import numpy as np
from sensor_sdk import data_classes as dc
from os import chdir, mkdir,listdir,remove,getcwd, makedirs
from os.path import splitext, isdir, exists
import csv
import math
import quaternionic
from typing import Callable, Tuple, Union
from classes.Config import SensorModel

########################################################################
# helper functions
########################################################################

# Install packages quaternionic and numpy

def line_plane_intersection(line_point: np.ndarray, line_dir: np.ndarray, plane_point: np.ndarray, plane_u: np.ndarray, plane_v: np.ndarray) -> Tuple[np.float64, np.float64]:
    """
    Computes the intersection of a line and a plane in 3D.
    
    Parameters:
    - line_point: np.array, a point on the line (P0)
    - line_dir: np.array, the direction vector of the line (d)
    - plane_point: np.array, a point on the plane (Q0)
    - plane_u: np.array, one of the vectors defining the plane (u)
    - plane_v: np.array, the other vector defining the plane (v)
    
    Returns:
    - intersection: np.array, the intersection point in u,v coordinates if it exists, otherwise None
    """
    # Calculate the normal vector of the plane
    plane_normal = np.cross(plane_u, plane_v)
    
    # Calculate the dot product of the line direction with the plane normal
    denom = np.dot(line_dir, plane_normal)
    
    # Check if the line is parallel to the plane
    if np.isclose(denom, 0):
        print("The line is parallel to the plane, no intersection.")
        return None
    
    # Calculate the parameter t for the line equation
    t = np.dot(plane_normal, (plane_point - line_point)) / denom
    
    # Calculate the intersection point
    intersection = line_point + t * line_dir

    # Convert to the plane's coordinate space
    u_coord = np.dot(intersection - plane_point, plane_u) / np.dot(plane_u, plane_u)
    v_coord = np.dot(intersection - plane_point, plane_v) / np.dot(plane_v, plane_v)
    return u_coord, v_coord
    


def rotate_vec(v: np.ndarray, q: quaternionic.QuaternionicArray) -> np.ndarray:
    # Rotates the vector v with quaternion q -> v_rotate = q * v * q^-1
    qp = np.divide(np.multiply(q, quaternionic.array([0, *v])), q)
    return np.array([qp.x, qp.y, qp.z])

def clamp(x: float, mx: float, mn: float) -> float: 
    return min(max(x, mn), mx)

# This is just so that the users of this transformation do not need to use "quaternionic"
ExternalQuaternion = Tuple[float, float, float, float] # w,x,y,z
Transform = Callable[[ExternalQuaternion], Tuple[float, float]]



def create_transform(_q_rg: ExternalQuaternion, s: SensorModel) -> Transform:
    q_rg = quaternionic.array(_q_rg)
    beam_origin = s.p_beam
    beam_vec = s.v_beam
    
    plane_u = rotate_vec((s.window_width_physical / 2) * s.u_window, q_rg) # The "-" is to match the sensor's coordinate space
    plane_v = rotate_vec((s.window_height_physical / 2) * s.v_window, q_rg)
    plane_o = rotate_vec(s.o_window, q_rg)   

    x_to_canvas = s.window_width_canvas
    y_to_canvas = s.window_height_canvas 

    def _transform(_q: ExternalQuaternion):
        q_tg = quaternionic.array(_q)
        v_tg = rotate_vec(beam_vec, q_tg)
        p_tg = rotate_vec(beam_origin, q_tg)
        p = line_plane_intersection(p_tg, v_tg, plane_o, plane_u, plane_v)
        if p is None:
            return [0,0]
        x = p[0]
        y = p[1]
        return x*x_to_canvas, y*y_to_canvas
    return _transform


toDeg = 180 / math.pi

def euler_from_quaternion(x, y, z, w):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)
     
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)
     
        return roll_x, pitch_y, yaw_z # radians converted to degrees


def get_mac_address(id):
    return ":".join(list(reversed([id[i:i + 2] for i in range(0, len(id), 2)]))).upper()

#device = await BleakScanner.find_device_by_filter(lambda d, ad: d.name and d.name.lower() == GLOVEName.lower())
async def discover_sensors():
    devices = await BleakScanner.discover( return_adv=True)
    return devices

def get_battery_level(batt_bytes):
    segments = np.dtype([
        ("level", np.int8),
        ("charging", np.int8),

    ])
    battry_level = np.frombuffer(batt_bytes, dtype=segments)[0]
    is_charging = False
    if(battry_level[1]==0):
        is_charging=False
    else:
        is_charging=True
    batt = dc.BatteryStatus(battry_level[0], is_charging)
    return batt

# data format Custom mode 5
#   Timestamp 4 bytes
#   Quaternions 16 bytes (4 per value)
#   Acceleration 12 bytes (4 per value)
#   Angular velocity 12 bytes (4 per value)

def encode_data_packet(bytes_):

    data_segments = np.dtype([
        ('timestamp', np.uint32),
        ('q_w', np.float32),
        ('q_x', np.float32),
        ('q_y', np.float32),
        ('q_z', np.float32),
        ('acc_x', np.float32),
        ('acc_y', np.float32),
        ('acc_z', np.float32),
        ('gyr_x', np.float32),
        ('gyr_y', np.float32),
        ('gyr_z', np.float32),
        ("zero_0", np.int64),
        ("zero_1", np.int64),
        ("zero_2", np.int16),
        ("zero_3", np.int8),
        ])
    formatted_data = np.frombuffer(bytes_, dtype=data_segments)
    return formatted_data


def check_and_create_export_diretory(dir):
    if not exists(dir):
        makedirs(dir)
        print(f"Export directory '{dir}' created successfully in the current working directory!")
    else:
        print(f"Export directory '{dir}' already exists in the current working directory.")


def write_data_to_csv(export_dir, csv_file_name, row_headers, data_to_write, list_of_timestamps):
        with open(export_dir + "/" + csv_file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row_headers)  # Write the header row
            for row in data_to_write:
                row_to_write = []
                #custom payload 5 has 11 pieces + space_bar_presses
                for d in range(11):
                    row_to_write.append(row[0][d])
                # if the timestamp  is in the list_of_timestamps add 1 else 0
                if(row_to_write[0] in list_of_timestamps):
                    row_to_write.append(1)
                else:
                    row_to_write.append(0)

                writer.writerow(row_to_write)

        return True

# exponential moving avereage
def calculate_ema(data_point, alpha, ema=None):
    if ema is None:
        ema = data_point
    else:
        ema = alpha * data_point + (1 - alpha) * ema
    return ema


# head_x = x_ref + scaling_factor * math.cos(flexion_radians) * math.sin(rotation_radians)
# head_y = y_ref + scaling_factor * math.sin(flexion_radians)