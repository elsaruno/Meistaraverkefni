_global_length_from_screen = {"length_from_screen": 60}

def set_length_from_screen(choice: str):
    _global_length_from_screen["length_from_screen"] = int(choice)

def get_length_from_screen():
    return _global_length_from_screen["length_from_screen"]