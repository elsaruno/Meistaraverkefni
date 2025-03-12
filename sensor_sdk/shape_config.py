_global_shape_data = {"shape_choice": "circle"}  #default shape value is circle 

def set_shape_choice(choice: str):
    """Update the shape choice globally."""
    _global_shape_data["shape_choice"] = choice  

def get_shape_choice():
    """Retrieve the current shape choice."""
    return _global_shape_data["shape_choice"]
