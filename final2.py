from machine import Pin, ADC, SoftI2C
from machine_i2c_lcd import I2cLcd
from time import sleep
import onewire, ds18x20

# ==== CONFIG ====
MAX_V = 8.4     # max voltage
MIN_V = 6.0     # min voltage

# Pin setup
VOLT_PIN = 32
CURR_PIN = 34
TEMP_PIN = 13

# LCD I2C setup
I2C_ADDR = 63  # adjust if different (use i2c.scan() to confirm)
i2c = SoftI2C(scl=Pin(23), sda=Pin(22))
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# ==== SENSOR SETUP ====
volt_sensor = ADC(Pin(VOLT_PIN))
volt_sensor.atten(ADC.ATTN_11DB)
volt_sensor.width(ADC.WIDTH_12BIT)

curr_sensor = ADC(Pin(CURR_PIN))
curr_sensor.atten(ADC.ATTN_11DB)
curr_sensor.width(ADC.WIDTH_12BIT)

'''
temp_sensor = ADC(Pin(TEMP_PIN))
temp_sensor.atten(ADC.ATTN_11DB)
temp_sensor.width(ADC.WIDTH_12BIT)
'''
# DS18B20 setup (digital)
dat = Pin(13)                  # Data pin for DS18B20
ds_sensor = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds_sensor.scan()

# ==== CURRENT SENSOR CALIBRATION ====
print("== Current sensor auto-calibration ==")
print("Make sure the load is OFF. Calibrating zero offset...")
samples = []
for _ in range(100):
    samples.append(curr_sensor.read())
    sleep(0.01)
zero_offset = sum(samples) / len(samples)
zero_voltage = (zero_offset / 4095) * 3.3
print(f"Zero raw ADC offset: {zero_offset}")
print(f"Zero sensor voltage (V): {zero_voltage:.4f}")

# ==== HELPER FUNCTIONS ====
def read_voltage():
    raw = volt_sensor.read()
    v = (raw / 4095) * 3.3
    # Adjust if voltage divider is used (example: 1:2 divider)
    battery_v = v * 4
    return battery_v

def read_temperature():
    # Read temperature from DS18B20
    ds_sensor.convert_temp()
    sleep(0.75)  # DS18B20 needs conversion time
    return ds_sensor.read_temp(roms[0]) if roms else 24.0

def read_current():
    raw = curr_sensor.read()
    v = (raw / 4095) * 3.3
    v_adj = v - zero_voltage
    # Assuming ACS712 5A (185 mV/A)
    current = v_adj / 0.185
    return max(0,current)

def compute_soc(voltage):
    soc = (voltage - MIN_V) / (MAX_V - MIN_V) * 100
    return max(0, min(100, soc))

def estimate_soh(voltage, temp, current, soc):
    # ==== REPLACE WITH YOUR OWN COEFFICIENTS ====
    a0 = 68.0
    a1, a2, a3, a4 = 4.2, -0.8, 0.5, 0.1

    soh = a0 + a1*voltage + a2*temp + a3*current + a4*soc
    return max(0, min(100, soh))

# ==== MAIN LOOP ====
lcd.clear()
lcd.putstr("Battery Monitor")
sleep(2)

print("\nStarting monitoring. Toggle the load ON/OFF to observe changes.\n")

while True:
    voltage = read_voltage()
    temp = read_temperature()
    current = read_current()
    soc = compute_soc(voltage)
    soh = estimate_soh(voltage, temp, current, soc)

    lcd.clear()
    #lcd.putstr(f"V:{voltage:.2f}V I:{current:.2f}A\n")
    #lcd.putstr(f"SoC:{soc:.0f}% SoH:{soh:.0f}")
    
    
    lcd.putstr(f"SoC:{soc:.0f} SoH:{soh:.0f} {temp:.0f}C\n")
    lcd.putstr(f"{voltage:.2f}V {current*1000:.0f}mA ")

    print(f"V={voltage:.2f}V | I={current:.2f}A | T={temp:.0f}°C | SoC={soc:.0f}% | SoH={soh:.0f}")

    sleep(0)
