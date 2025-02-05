class Parameters:

    def __init__(self):
        self.selected_sensor = ""
        self.count_down = 5

        # Note: where can sensors be placed?
        self.placements = [
            "Sensor 1",
            "Sensor 2"
            
        ]


    def get_placements(self):
        return self.placements
    
    def get_count_down_start(self):
        return self.count_down
    
    def set_selected_sensor(self, selected_sensor):
        self.selected_sensor = selected_sensor
        
    def get_selected_sensor(self):
        return self.selected_sensor