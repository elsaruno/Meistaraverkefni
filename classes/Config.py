from typing import Literal, Tuple
import numpy as np

def unit_vec(x: float, y: float, z: float) -> np.ndarray:
    vec = np.array([x,y,z])
    return vec / np.linalg.norm(vec)

def vector(x: float, y: float, z: float) -> np.ndarray:
    return np.array([x,y,z])

def point(x: float, y: float, z: float) -> np.ndarray:
    return np.array([x,y,z])

def is_normalized(v: np.ndarray):
    return (np.linalg.norm(v) - 1) < 1e-5
class SensorModel:
    def __init__(self, name: Literal['head', 'wrist', 'free', 'head-z-down']):
        print(f'Using "{name}" sensor model')
        self.name = name
        if self.name == 'free':
            # Sensor freely rotating around itself"
            self.o_global = point(0,0,0)
            self.p_beam = self.o_global
            self.v_beam = unit_vec(1,0,0)
            self.o_window = self.p_beam + vector(60,0,0)
            self.u_window = unit_vec(0,-1,0)
            self.v_window = unit_vec(0,0,1)

        elif self.name == 'head':
            # Sensor mounted on head, rotatation around neck and z is up
            self.o_global = point(0,0,0)
            self.p_beam = self.o_global + vector(0,0,10) # You can play with the offset a bit. Is the beam point in the eyes or nose?
            self.v_beam = unit_vec(1,0,0)
            self.o_window = self.p_beam + vector(60,0,0)
            self.u_window = unit_vec(0,-1,0)
            self.v_window = unit_vec(0,0,1)
        elif self.name == 'head-z-down':
            # Sensor mounted on head, rotatation around neck and z is down
            self.o_global = point(0,0,0)
            self.p_beam = self.o_global + vector(0,0,-10) # You can play with the offset a bit. Is the beam point in the eyes or nose?
            self.v_beam = unit_vec(1,0,0)
            self.o_window = self.p_beam + vector(60,0,0)
            self.u_window = unit_vec(0,1,0)
            self.v_window = unit_vec(0,0,-1)
        elif self.name == 'wrist':
            # Sensor mounted on wrist, rotation around shoulder with straight arm and z z is up
            self.o_global = point(0,0,0)
            self.p_beam = self.o_global + vector(70,0,0) # Approximately length of the arm
            self.v_beam = unit_vec(1,0,0)
            self.o_window = self.o_global + (self.p_beam - self.o_global) + 30*self.v_beam 
            self.u_window = unit_vec(0,-1,0)
            self.v_window = unit_vec(0,0,1)
        else:
            raise ValueError(f'Unsupported model name: {self.name}')
        
        if not is_normalized(self.v_beam):
            raise ValueError(f'v_beam not normalized')

        if not is_normalized(self.u_window):
            raise ValueError(f'u_window not normalized')
        
        if not is_normalized(self.v_window):
            raise ValueError(f'v_window not normalized')
        
        # By "physical" we mean in the physical world i.e. cm or in
        #  Units don't really matter just be consistent and use the same units in the vector/point values above. 
        #  Use a measuring tape.
        # By "canvas" we mean within the software context (what you pass in to the plot method)
        self.window_width_physical = 31 #55
        self.window_height_physical = 22 #23
        self.window_width_canvas = 50 * 2
        self.window_height_canvas = 50 * 2

        # These were the measurements before start measurement is clicked, the axis is rescaled after measurement starts?
        #self.window_width_canvas = 47.5 * 2 
        #self.window_height_canvas = 33 * 2

        
class Config:
    def __init__(self):
        self.number_of_plot_points = 250
        self.data_rate = 60
        self.alpha = 0.2 # pre set alpha for exponential moving average filter

        # Controlls which transformation of "orientation" to xy coordinates to be used. 
        self.transform_mode: Literal['yaw_offset', 'quaternion'] = 'quaternion'
        
        ### Specifics for the "yaw offset" transformation mode ###
        self.max_rotation = 30
        self.max_flex_ext = 30
        self.x_ref = 0
        self.y_ref = 0
        
        # Controls the refresh rate and the animation
        self.animation_length = 10000 # ms
        self.update_interval = 20 # ms ... 20 ms = 50Hz
        self.max_sensor_points_to_show = 120 # Shows only this many of the latest sensor points. Set to 0 to disable
        
        ### Specifics for the "quaternion" transformation mode ###
        self.sensor_model = SensorModel('free')
    
    def get_number_of_plot_points(self):
        return self.number_of_plot_points