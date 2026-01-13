from gpiozero import LED, Buzzer
import time

# GPIO SETUP
green_led = LED(17)
red_led = LED(27)
buzzer = Buzzer(22)

# TEST SEQUENCE
try:
    print("Starting GPIO test...")
    print()
    
# Test Green LED
    print("Testing Green LED (GPIO 17)...")
    green_led.on()
    time.sleep(1)
    green_led.off()
    time.sleep(0.5)
    print("Green LED: OK")
    print()
    
# Test Red LED
    print("Testing Red LED (GPIO 27)...")
    red_led.on()
    time.sleep(1)
    red_led.off()
    time.sleep(0.5)
    print("Red LED: OK")
    print()
    
 # Test Buzzer
    print("Testing Buzzer (GPIO 22)...")
    buzzer.on()
    time.sleep(1)
    buzzer.off()
    time.sleep(0.5)
    print("Buzzer: OK")
    print()
    
 # Test all together
    print("Testing all devices together...")
    green_led.on()
    red_led.on()
    buzzer.on()
    time.sleep(2)
    
    green_led.off()
    red_led.off()
    buzzer.off()
    print()
    
    print("All devices working!")

except KeyboardInterrupt:
    print("\nTest stopped by user")

except Exception as e:
    print(f"Error: {e}")

finally:
    # Turn off all devices
    green_led.off()
    red_led.off()
    buzzer.off()
    print("Test complete")