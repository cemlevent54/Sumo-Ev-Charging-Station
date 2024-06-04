import tkinter as tk
import sys
from mainfunc import start_simulation, RedirectText, get_vehicle_properties, display_vehicle_properties, xml_file

# mainfunc kısmında dosya yolu kopyalama işlemi yaptıktan sonra buradan uygulamayı çalıştırabilirsiniz.

root = tk.Tk()
root.geometry('800x600')  # Form boyutunu burada ayarlayabilirsiniz
root.title('SUMO GUI')

# Ekran boyutlarını al
screen_width = 1000  # Ekran genişliğini güncelledik
screen_height = 1000  # Ekran yüksekliğini güncelledik

# sumo_car_properties_frame
sumo_car_properties_frame = tk.Frame(root, highlightbackground='red', highlightthickness=2)
sumo_car_properties_frame.pack(side='left', fill='y')
sumo_car_properties_frame.pack_propagate(False)
sumo_car_properties_frame.configure(width=int(screen_width * 0.2))

# sumo_car_state_frame
sumo_car_state_frame = tk.Frame(root, highlightbackground='blue', highlightthickness=2)
sumo_car_state_frame.pack(side='right', fill='y')
sumo_car_state_frame.pack_propagate(False)
sumo_car_state_frame.configure(width=int(screen_width * 0.8))

# Log output text widget
sumo_car_state_frame_text = tk.Text(sumo_car_state_frame)
sumo_car_state_frame_text.pack(fill='both', expand=True)

# Redirect stdout to the log output text widget
sys.stdout = RedirectText(sumo_car_state_frame_text)

# Get vehicle properties from the XML file
vehicle_properties, vType_properties = get_vehicle_properties(xml_file)

# Get the first vehicle ID from the XML file
first_vehicle_id = next(iter(vehicle_properties))

# Display the vehicle properties in the sumo_car_properties_frame
display_vehicle_properties(sumo_car_properties_frame, vehicle_properties, vType_properties, first_vehicle_id)

# Pencere yüklendikten sonra SUMO GUI'yi başlatma ve simülasyonu başlatma
root.after(100, start_simulation)

root.mainloop()
