# micropython-sgp30

A simple driver for the Sensirion SGP30 (eCO2 / TVOC) Indoor Air Quality sensor, designed for the MicroPython environment.

## 🛠️ Supported Devices

* Microcontrollers running MicroPython (e.g., ESP32, Raspberry Pi Pico)
* Sensirion SGP30 Indoor Air Quality Sensor

## 📥 Installation

1.  Download the `sgp30.py` file from this repository.
2.  Upload `sgp30.py` to the root directory of your microcontroller board using your MicroPython development environment (e.g., Thonny).

## 🚀 Usage (Example)

Use the following example code (e.g., in `main.py`) to start measuring eCO2 (equivalent carbon dioxide) and TVOC (total volatile organic compounds).

**Note:** For the first 15 seconds after initialization, the sensor returns fixed values (eCO2: 400 ppm, TVOC: 0 ppb) while it warms up.

```python
from machine import I2C, Pin
import time
from sgp30 import SGP30

# I2C Setup Example (Adjust pin numbers for your specific board)
# Example: Seeed Studio Xiao ESP32C6
# i2c = I2C(0, scl=Pin(23), sda=Pin(22)) 
# Example: Raspberry Pi Pico
# i2c = I2C(0, scl=Pin(1), sda=Pin(0)) 

# Initialize your I2C object here
i2c = I2C(...) 

# Initialize the SGP30 driver
sgp = SGP30(i2c)
sgp.init_air_quality()

print("SGP30 sensor initialization complete. Sensor adjusting for 15 seconds...")

# Wait for the sensor to stabilize
time.sleep(15) 
print("Starting measurement.")

while True:
    # Read the IAQ measurement
    reading = sgp.measure_iaq()
    
    # Display results
    print("-" * 20)
    print(f"eCO2 (Equivalent CO2): {reading.equivalent_co2} ppm")
    print(f"TVOC (Total VOC): {reading.total_voc} ppb")
    
    # Per SGP30 specifications, a measurement interval of at least 1 second is required
    time.sleep(1)
```

## 📝 Key Methods

* **`sgp.init_air_quality()`** : Initializes the sensor to begin IAQ (Indoor Air Quality) measurement.
* **`sgp.measure_iaq()`** : Retrieves the latest eCO2 and TVOC measurement values.
* **`sgp.get_iaq_baseline()`** : Reads the sensor's internal baseline value (recommended for maintaining long-term accuracy).
* **`sgp.set_iaq_baseline(TVOC, eCO2)`** : Writes a previously saved baseline value back to the sensor.
* **`sgp.set_absolute_humidity(grams_per_m3)`** : Sets the absolute humidity (from an external sensor) to improve measurement accuracy via humidity compensation.

## 🔗 References

* [Sensirion SGP30 Product Page / Datasheet](https://sensirion.com/media/documents/984E0DD5/61644B8B/Sensirion_Gas_Sensors_Datasheet_SGP30.pdf)
