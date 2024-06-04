
# SUMO ile Batarya Yönetimi Simülasyonu

Bu proje, SUMO (Simulation of Urban MObility) ve Python scriptini entegre ederek araç hareketlerini simüle eder, batarya seviyelerini izler ve bataryası düşük olan araçları şarj istasyonlarına yönlendirir. Simülasyon, Tkinter kullanılarak oluşturulmuş bir grafik arayüzde görselleştirilir.

## Gereksinimler

- SUMO (en son sürüm)
- Python 3.x
- Tkinter (genellikle Python ile birlikte gelir)
- `sumolib` ve `traci` Python paketleri

## Kurulum

1. **SUMO'yu Yükleyin:**
   [SUMO'nun resmi web sitesi](https://sumo.dlr.de/docs/Installing/index.html) üzerindeki talimatları takip ederek SUMO'yu yükleyin.

2. **Python Paketlerini Yükleyin:**
   ```bash
   pip install sumolib traci
   ```

## Dosya Yapısı

- `main.py`: Simülasyonu çalıştırmak için ana betik.
- `sumo_cfg_file`: SUMO yapılandırma dosyanızın yolu.
- `sumo_network_file`: SUMO ağ dosyanızın yolu.
- `sumo_charging_station_file`: Şarj istasyonlarını içeren SUMO ek dosyanızın yolu.
- `route.xml`: Rota XML dosyanızın yolu.

## Kullanım

1. **Yolları Güncelleyin:**
   Betikteki yer tutucu yolları, SUMO yapılandırma, ağ, ek ve rota XML dosyalarınızın gerçek yollarıyla değiştirin:
   ```python
   sumo_cfg_file = "yapılandırma-dosyanızın-yolu"
   sumo_network_file = "ağ-dosyanızın-yolu"
   sumo_charging_station_file = "ek-dosyanızın-yolu"
   xml_file = "rota-xml-dosyanızın-yolu"
   ```

2. **Betik Çalıştırma:**
   Simülasyonu başlatmak için ana betiği çalıştırın:
   ```bash
   python main.py
   ```

## Script Genel Bakış

### **`mainFunc.py`** içindeki fonksiyonlar

- **`main()`:** Simülasyonu çalıştıran ana fonksiyon. SUMO'yu başlatır, araç batarya seviyelerini izler ve gerekirse araçları şarj istasyonlarına yönlendirir.
- **`getCurrentChargePercentage()`:** Bir aracın mevcut şarj yüzdesini döndürür.
- **`RedirectText`:** Tkinter metin widget'ında çıktıyı yönetmek ve görüntülemek için bir sınıf.
- **`getChargePercentage(charge_level, battery_capacity)`:** Bir aracın batarya yüzdesini hesaplar.
- **`show_warning_message(vehicle_id)`:** Batarya seviyesi %40'ın altına düştüğünde uyarı mesajı gösterir.
- **`calculate_distance_using_route(vehicle_id, start_edge_id, end_edge_id)`:** Araç ile şarj istasyonu arasındaki mesafeyi hesaplar.
- **`find_nearest_charging_station(vehicle_position, charging_stations, vehicle_id)`:** Bir araç için en yakın şarj istasyonunu bulur.
- **`get_charging_stations(additional_file, net_file)`:** Ek dosyadan şarj istasyonlarını alır.
- **`check_teleporting_vehicles()`:** Teleport olan araçları kontrol eder.
- **`find_route_to_charging_station(vehicle_id, start_edge_id, end_edge_id)`:** Aracı en yakın şarj istasyonuna yönlendirir.
- **`start_simulation()`:** Simülasyonu yeni bir iş parçacığında başlatır.
- **`get_vehicle_properties(xml_file)`:** Rota XML dosyasından araç özelliklerini alır.
- **`display_vehicle_properties(frame, vehicle_properties, vType_properties, vehicle_id)`:** Tkinter GUI'de araç özelliklerini görüntüler.

### GUI Bileşenleri

- Tkinter GUI, simülasyon durumu, araç özellikleri ve batarya seviyelerini görüntülemek için kullanılır.
- `RedirectText` sınıfı, çıktının bir metin widget'ına yönlendirilmesi için kullanılır.
- Araç özellikleri ve rotalar, `display_vehicle_properties` fonksiyonu kullanılarak GUI'de görüntülenir.

## Ek Notlar

- **Batarya Yönetimi:** Betik, araçların batarya seviyelerini izler. Batarya seviyesi %40'ın altına düştüğünde uyarı mesajı gösterilir ve araç en yakın şarj istasyonuna yönlendirilir.
- **Rota Yönetimi:** Araçlar bataryası düşük olduğunda şarj istasyonlarına yönlendirilir ve şarj olduktan sonra orijinal rotalarına dönerler.

Bu Python scripti, kontrollü bir kentsel mobilite ortamında batarya yönetim stratejilerini test etmek için kapsamlı bir simülasyon ortamı sağlar.
