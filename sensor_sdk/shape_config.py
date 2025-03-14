_global_shape_data = {"shape_choice": "circle"}  #default shape value is circle 

_global_start_measuring = {"start_measuring_button_pressed": False} #default start measuring button is not pressed

def set_shape_choice(choice: str):
    """Update the shape choice globally."""
    _global_shape_data["shape_choice"] = choice  

def get_shape_choice():
    """Retrieve the current shape choice."""
    return _global_shape_data["shape_choice"]

def set_start_measuring_true():
    _global_start_measuring["start_measuring_button_pressed"] = True
    
def get_start_measuring():
    return _global_start_measuring["start_measuring_button_pressed"]
