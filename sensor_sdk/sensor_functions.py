from bleak import BleakClient
from sensor_sdk import helper_functions as hf
from sensor_sdk import data_classes as dc
from datetime import datetime
import time

import asyncio

async def discover_sensors(sensor_manager):
    print("discovering sensors")
    sensor_manager.remove_all_scanned_sensors()
    print(sensor_manager.get_selected_sensor())

    #get the sensor type calls 
    sts = sensor_manager.get_sensor_types()
    sensor_type = [st for st in sts if st.get_sensor_type_name() == sensor_manager.get_selected_sensor()][0]
    sensors = await hf.discover_sensors()
    scanned_sensors = []

    if(sensors):
        for s, a in sensors.values():
            print(s)
            if( len(list(a.manufacturer_data.keys())) != 0 and list(a.manufacturer_data.keys())[0] == sensor_type.manufacturer_id):
                mac_address = hf.get_mac_address(a.manufacturer_data[sensor_type.manufacturer_id].hex())
                scanned_sensor = dc.ScannedSensor(mac_address, s.address, s)
                scanned_sensors.append(scanned_sensor)

    return scanned_sensors

async def connect_to_sensor(sensor_manager, address):
    sts = sensor_manager.get_sensor_types()
    sensor_type = [st for st in sts if st.get_sensor_type_name() == sensor_manager.get_selected_sensor()][0]
    #find device in scanned sensors 
    sensor = list(filter(lambda x: x.address == address, sensor_manager.scanned_sensors))[0]
    device = BleakClient(sensor.ble_device,loop=sensor_manager.loop)
    await device.connect()
    print("sleeping for 2 seconds")
    #time.sleep(2)

    connected_sensor = dc.ConnectedSensor(sensor.address, device, sensor.ble_device, sensor_manager)
    sensor_manager.connected_sensors.append(connected_sensor)
    payload = {}
    for p in sensor_type.config["ble_config"]["payloads"]:
        if(p["name"] == sensor_type.payload_name):
            payload = p

    # configure sensor with 60Hz data rate to be sure it is set
    #device_control = sensor_type.config["ble_config"]["services"]["control_service"]
    #date_rate_char = sensor_manager.sensor_type.config["ble_config"]["characteristics"]["data_rate"]["60"]
    #await device.ble_client.write_gatt_char(device_control, date_rate_char, response=True)
    connected_sensor.set_set_data_rate(60)

    await device.start_notify(payload["payload_size"], connected_sensor.on_sensor_data )

    #subsribe to button press
    device_report = sensor_type.config["ble_config"]["services"]["device_report"]
    await device.start_notify(device_report, connected_sensor.on_button_event)

    #read initial battery
    battery_service = sensor_type.config["ble_config"]["services"]["battery_service"]
    batt = await device.read_gatt_char(battery_service, response=True)
    connected_sensor.on_battery_status_update(connected_sensor.address, batt)
    await device.start_notify(battery_service, connected_sensor.on_battery_status_update)

    return connected_sensor

async def disconnect_from_sensor(sensor_manager, address):
    sensor = list(filter(lambda x: x.address == address, sensor_manager.connected_sensors))
    if(len(sensor)>0):
        print(f"disconneting from sensor {sensor[0]}")
        disconnected = await sensor[0].ble_client.disconnect()
        return disconnected
    else:
        return False


### need to reset all the data on a connected sensor
async def start_measuring(sensor_manager, address):
    sensor = list(filter(lambda x: x.address == address, sensor_manager.connected_sensors))[0]
    print("Sensor", sensor)
    if(sensor):    
        start_char = sensor_manager.sensor_type.config["ble_config"]["characteristics"]["start_measurement"]
        measurement_service = sensor_manager.sensor_type.config['ble_config']["services"]["measurement_service"]
        await sensor.ble_client.write_gatt_char(measurement_service, start_char, response=True)

async def start_measuring_on_all_sensors(sensor_manager):
    sts = sensor_manager.get_sensor_types()
    sensor_type = [st for st in sts if st.get_sensor_type_name() == sensor_manager.get_selected_sensor()][0]
    start_char = sensor_type.config["ble_config"]["characteristics"]["start_measurement"]
    measurement_service = sensor_type.config['ble_config']["services"]["measurement_service"]

    # clear all data if starting a test again
    for s in sensor_manager.connected_sensors:
        print("Setting is measuring")
        s.clear_all_data()
        s.set_is_measuring(True)

    # this doesnt matter as > 1 sensor halves data rate
    tasks = [s.ble_client.write_gatt_char(measurement_service, start_char,  response=True) for s in sensor_manager.connected_sensors]
    await asyncio.gather(*tasks)

###############################################

async def stop_measuring_on_all_sensors(sensor_manager):
    sts = sensor_manager.get_sensor_types()
    sensor_type = [st for st in sts if st.get_sensor_type_name() == sensor_manager.get_selected_sensor()][0]
    stop_char = sensor_type.config["ble_config"]["characteristics"]["stop_measurement"]
    measurement_service = sensor_type.config['ble_config']["services"]["measurement_service"]
    for s in sensor_manager.connected_sensors:
        s.set_is_measuring(False)
    #     await s.ble_client.write_gatt_char(measurement_service, stop_char, response=True)
        
    tasks = [s.ble_client.write_gatt_char(measurement_service, stop_char,  response=True) for s in sensor_manager.connected_sensors]
    await asyncio.gather(*tasks)

async def stop_measuring(sensor_manager, address):
    sensor = list(filter(lambda x: x.address == address, sensor_manager.connected_sensors))[0]
    stop_char = sensor_manager.sensor_type.config["ble_config"]["characteristics"]["stop_measurement"]
    measurement_service = sensor_manager.sensor_type.config['ble_config']["services"]["measurement_service"]
    await sensor.ble_client.write_gatt_char(measurement_service, stop_char, response=True)
    sensor_manager.stop_sensor_callback(sensor.address)

async def indentify_sensor(sensor_manager, address):
    sts = sensor_manager.get_sensor_types()
    sensor_type = [st for st in sts if st.get_sensor_type_name() == sensor_manager.get_selected_sensor()][0]
    sensor = list(filter(lambda x: x.address == address, sensor_manager.connected_sensors))[0]
    control_service = sensor_type.config["ble_config"]["services"]["control_service"]
    indentify_char = sensor_type.config['ble_config']["characteristics"]["identify"]
    await sensor.ble_client.write_gatt_char(control_service, indentify_char, response=True)
    
async def export_to_csv(sensor_manager, address):
    # exports data from a sensor to csv
    sensor = list(filter(lambda x: x.address == address, sensor_manager.connected_sensors))[0]
    data_to_write_to_csv = sensor.get_raw_data()
    #print(data_to_write_to_csv)
    list_of_timestamps = sensor.get_space_press_timestamps()
    modified_address = address.replace(":", "_")
    now = int(datetime.timestamp(datetime.now()) * 1000)
    csv_file_name = f"{now}_{modified_address}_{sensor.get_placement()}.csv"
    # payloads is a list of payloads (name) but actually there is only one in this app
    row_headers = sensor_manager.sensor_type.config["ble_config"]["payloads"][0]["csv_header"]

    hf.check_and_create_export_diretory(sensor_manager.export_dir)

    done = hf.write_data_to_csv(sensor_manager.export_dir, csv_file_name, row_headers, data_to_write_to_csv, list_of_timestamps)
    
    if(done):
        # remove raw data
        sensor.remove_raw_data()
        sensor_manager.export_to_csv_done_callback(sensor.address)

    