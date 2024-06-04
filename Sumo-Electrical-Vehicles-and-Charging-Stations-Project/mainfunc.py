import traci
import sumolib
import threading
import xml.etree.ElementTree as ET
import os
import tkinter as tk
from tkinter import messagebox

# Path variables
sumo_cfg_file = "copy-your-cfg-file-path-here"
sumo_network_file = "copy-your-network-file-path-here"
sumo_charging_station_file = "copy-your-additional-file-path-here"
xml_file = 'copy-your-route-xml-file-path-here'
current_charge_percentage = 0

def getCurrentChargePercentage():
    return current_charge_percentage

class RedirectText:
    def __init__(self, text_widget):
        self.output = text_widget
        self.buffer = []

    def write(self, string, charge_percentage=None):
        if string.strip():  # Check if the string is not empty
            self.buffer.append(string + '\n')
            if len(self.buffer) > 5:
                self.buffer.pop(0)  # Remove the oldest message to keep the buffer size to 5

            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, ''.join(self.buffer))
            self.output.see(tk.END)
            
            if charge_percentage is not None:
                if charge_percentage <= 15:
                    self.output.configure(bg='red')
                elif 15 < charge_percentage < 40:
                    self.output.configure(bg='yellow')
                else:
                    self.output.configure(bg='green')

    def flush(self):
        pass

# aracın şarj yüzdesini hesaplar
def getChargePercentage(charge_level, battery_capacity):
    return (charge_level / battery_capacity) * 100

# %40'ın altına düştüğü zaman uyarı
def show_warning_message(vehicle_id):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("Low Battery Warning", f"Vehicle {vehicle_id} is below 40% charge.")
    root.destroy()

# rota üzerindeki en yakın şarj istasyonunu hesaplama
def calculate_distance_using_route(vehicle_id, start_edge_id, end_edge_id):
    try:
        route = traci.simulation.findRoute(start_edge_id, end_edge_id)
        if route.edges:
            total_distance = sum(traci.lane.getLength(edge_id + "_0") for edge_id in route.edges)
            return total_distance
        else:
            print(f"No route found between {start_edge_id} and {end_edge_id}.")
            return None
    except traci.exceptions.TraCIException as e:
        print(f"TraCI Exception while calculating distance: {e}")
        return None

def find_nearest_charging_station(vehicle_position, charging_stations, vehicle_id):
    nearest_station = None
    min_distance = float('inf')
    
    for station_id, station_details in charging_stations.items():
        start_edge_id = traci.vehicle.getRoadID(vehicle_id)
        end_edge_id = station_details['edge_id']
        
        distance = calculate_distance_using_route(vehicle_id, start_edge_id, end_edge_id)
        
        if distance is not None and distance < min_distance:
            min_distance = distance
            nearest_station = station_id

    return nearest_station, min_distance

# xml dosyasından şarj istasyonlarını getirme
def get_charging_stations(additional_file, net_file):
    if not os.path.isfile(additional_file):
        raise FileNotFoundError(f"The additional file {additional_file} does not exist.")
    
    if not os.path.isfile(net_file):
        raise FileNotFoundError(f"The network file {net_file} does not exist.")
    
    net = sumolib.net.readNet(net_file)
    
    tree = ET.parse(additional_file)
    root = tree.getroot()
    
    charging_stations = {}
    for station in root.findall('chargingStation'):
        id_ = station.get('id')
        lane = station.get('lane')
        start_pos = float(station.get('startPos'))
        end_pos = float(station.get('endPos'))
        power = float(station.get('power'))
        charge_delay = float(station.get('chargeDelay'))
        
        lane_parts = lane.split('_')
        edge_id = lane_parts[0]
        lane_index = int(lane_parts[1])
        
        edge = net.getEdge(edge_id)
        position = edge.getLane(lane_index).getShape()[-1]
        
        charging_stations[id_] = {
            'lane': lane,
            'startPos': start_pos,
            'endPos': end_pos,
            'power': power,
            'chargeDelay': charge_delay,
            'position': position,
            'edge_id': edge.getID(),
            'lane_index': lane_index
        }
    
    return charging_stations

def check_teleporting_vehicles():
    starting_teleport_vehicles = traci.simulation.getStartingTeleportIDList()
    ending_teleport_vehicles = traci.simulation.getEndingTeleportIDList()
    if starting_teleport_vehicles:
        print(f"Starting Teleporting Vehicles: {starting_teleport_vehicles}")
    if ending_teleport_vehicles:
        print(f"Ending Teleporting Vehicles: {ending_teleport_vehicles}")

# şarj istasyonuna yönlendirme
def find_route_to_charging_station(vehicle_id, start_edge_id, end_edge_id):
    try:
        route = traci.simulation.findRoute(start_edge_id, end_edge_id)
        if route.edges:
            traci.vehicle.setRoute(vehicle_id, route.edges)
            return True
        else:
            print(f"No route found between {start_edge_id} and {end_edge_id}.")
            return False
    except traci.exceptions.TraCIException as e:
        print(f"TraCI Exception while finding route: {e}")
        return False

# ana fonksiyon
def main():
    global current_charge_percentage
    try:
        sumoBinary = sumolib.checkBinary('sumo-gui')
        traci.start([sumoBinary, "-c", sumo_cfg_file])
        
        vehicle_current_situation = {}
        warning_shown = {}
        previous_energy_consumed = {}
        original_routes = {}
        vehicle_charging_station = {}
        
        charging_stations = get_charging_stations(sumo_charging_station_file, sumo_network_file)
        
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            check_teleporting_vehicles()

            vehicle_ids = traci.vehicle.getIDList()
            for vehicle_id in vehicle_ids:
                speed = traci.vehicle.getSpeed(vehicle_id)
                position = traci.vehicle.getRoadID(vehicle_id)
                vehicle_position = traci.vehicle.getPosition(vehicle_id)
                
                charge_level = float(traci.vehicle.getParameter(vehicle_id, "device.battery.actualBatteryCapacity"))
                battery_capacity = float(traci.vehicle.getParameter(vehicle_id, "device.battery.maximumBatteryCapacity"))
                charge_percentage = getChargePercentage(charge_level, battery_capacity)
                
                total_energy_consumed = float(traci.vehicle.getParameter(vehicle_id, "device.battery.totalEnergyConsumed"))
                if vehicle_id in previous_energy_consumed:
                    energy_consumed_last_step = total_energy_consumed - previous_energy_consumed[vehicle_id]
                else:
                    energy_consumed_last_step = total_energy_consumed
                energy_consumed_per_ms = energy_consumed_last_step / 1000
                
                previous_energy_consumed[vehicle_id] = total_energy_consumed
                vehicle_current_situation[vehicle_id] = charge_percentage
                #for function
                current_charge_percentage = charge_percentage

                if charge_percentage <= 15:
                    traci.vehicle.setColor(vehicle_id, (255, 0, 0))
                elif 15 < charge_percentage < 40:
                    if not warning_shown.get(vehicle_id, False):
                        warning_shown[vehicle_id] = True
                        traci.vehicle.setColor(vehicle_id, (255, 255, 0))
                        threading.Thread(target=show_warning_message, args=(vehicle_id,)).start()

                    nearest_station, nearest_distance = find_nearest_charging_station(vehicle_position, charging_stations, vehicle_id)
                    print(f"Nearest Station: {nearest_station}, Distance: {nearest_distance} meters")
                    
                    if nearest_station in charging_stations:
                        nearest_cs_edge_id = charging_stations[nearest_station]['edge_id']
                        
                        if vehicle_id not in original_routes:
                            original_routes[vehicle_id] = traci.vehicle.getRoute(vehicle_id)
                        
                        vehicle_charging_station[vehicle_id] = nearest_station
                        
                        if not find_route_to_charging_station(vehicle_id, position, nearest_cs_edge_id):
                            print(f"Unable to find route to charging station for vehicle {vehicle_id}.")
                
                elif charge_percentage >= 80 and vehicle_id in original_routes:
                    if original_routes[vehicle_id]:
                        try:
                            start_edge_id = traci.vehicle.getRoadID(vehicle_id)
                            end_edge_id = original_routes[vehicle_id][0]
                            route = traci.simulation.findRoute(start_edge_id, end_edge_id)
                            if route.edges:
                                traci.vehicle.setRoute(vehicle_id, route.edges)
                                if vehicle_id in vehicle_charging_station:
                                    charging_station_id = vehicle_charging_station[vehicle_id]
                                    traci.vehicle.setChargingStationStop(vehicle_id, charging_station_id, duration=0)
                                    vehicle_charging_station.pop(vehicle_id, None)
                                traci.vehicle.setRoute(vehicle_id, original_routes[vehicle_id])
                                original_routes.pop(vehicle_id, None)
                                traci.vehicle.setColor(vehicle_id, (0, 255, 0))
                            else:
                                print(f"Error restoring route for vehicle {vehicle_id}: No route found.")
                        except traci.exceptions.TraCIException as e:
                            print(f"Error restoring route for vehicle {vehicle_id}: {e}")
                    else:
                        print(f"No original route stored for vehicle {vehicle_id}.")

                else:
                    traci.vehicle.setColor(vehicle_id, (0, 255, 0))

                current_edge = traci.vehicle.getRoadID(vehicle_id)
                for station_id, station_details in charging_stations.items():
                    if current_edge == station_details['edge_id'] and charge_percentage < 30:
                        traci.vehicle.setChargingStationStop(vehicle_id, station_id, duration=60)
                        break

                print(f"Vehicle ID: {vehicle_id}, Charge Percentage: {charge_percentage}%, Energy Consumption per ms: {energy_consumed_per_ms} J")

    except traci.exceptions.TraCIException as e:
        print(f"TraCI Exception occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        traci.close()

# simülasyonu başlatma
def start_simulation():
    threading.Thread(target=main).start()

# araç özellikleri için yazılmış XML Parse fonksiyonu
def get_vehicle_properties(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    vehicle_properties = {}
    for vehicle in root.findall('vehicle'):
        vehicle_id = vehicle.get('id')
        vehicle_properties[vehicle_id] = {
            'type': vehicle.get('type'),
            'depart': vehicle.get('depart'),
            'route': vehicle.get('route')
        }
        for param in vehicle.findall('param'):
            key = param.get('key')
            value = param.get('value')
            vehicle_properties[vehicle_id][key] = value
    
    # Include vType properties
    vType_properties = {}
    for vtype in root.findall('.//vType'):
        vtype_id = vtype.get('id')
        vType_properties[vtype_id] = {}
        for param in vtype.findall('param'):
            key = param.get('key')
            value = param.get('value')
            vType_properties[vtype_id][key] = value
    
    return vehicle_properties, vType_properties

# araç özelliklerini arayüzde göstermek için yazılmış fonksiyon
def display_vehicle_properties(frame, vehicle_properties, vType_properties, vehicle_id):
    for widget in frame.winfo_children():
        widget.destroy()
    
    if vehicle_id in vehicle_properties:
        properties = vehicle_properties[vehicle_id]
        for key, value in properties.items():
            label = tk.Label(frame, text=f"{key}: {value}", anchor='w')
            label.pack(fill='x')
        
        vehicle_type = properties['type']
        if vehicle_type in vType_properties:
            vtype_props = vType_properties[vehicle_type]
            for key, value in vtype_props.items():
                label = tk.Label(frame, text=f"{key}: {value}", anchor='w')
                label.pack(fill='x')
    else:
        label = tk.Label(frame, text="Vehicle not found.", anchor='w')
        label.pack(fill='x')
