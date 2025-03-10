# Use a dictionary to ensure updates persist across modules
_global_shape_data = {"shape_choice": "circle"}  # Default value

def set_shape_choice(choice: str):
    """Update the shape choice globally."""
    _global_shape_data["shape_choice"] = choice  # Use dictionary for persistence
    print(f"Shape choice updated to: {choice}")  # Debugging print

def get_shape_choice():
    """Retrieve the current shape choice."""
    return _global_shape_data["shape_choice"]
