# import libraries
import cv2
import time
from picamera2 import Picamera2
from gpiozero import LED, Buzzer
from ultralytics import YOLO


# GPIO SETUP
green_led = LED(17)  
red_led = LED(27)   
buzzer = Buzzer(22)  

# Turn off all devices initially
for device in [green_led, red_led, buzzer]:
    device.off()

# LOAD MODEL
model = YOLO("best_ncnn_model", task="classify")

# PARAMETERS
FPS = 10
FRAME_INTERVAL = 1.0 / FPS

DROWSY_THRESHOLD = 10
drowsy_counter = 0

labels = {
    0: "absent",
    1: "awake",
    2: "drowsy"
}

# State tracking variables for printing
previous_displayed_state = None  # Last displayed state
alarm_was_on = False   # Was alarm active before?

# CAMERA SETUP
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()
time.sleep(2)  # Let camera stabilize

last_time = time.time()

# MAIN LOOP
try:
    while True:
        current_time = time.time()
        
        # Control FPS
        if current_time - last_time < FRAME_INTERVAL:
            continue
        last_time = current_time

        frame = picam2.capture_array()

        # YOLO INFERENCE
        frame_resized = cv2.resize(frame, (224, 224))

        frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        frame_3ch = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2BGR)
        results = model(frame_3ch, verbose=False)

        
        cls_id = int(results[0].probs.top1)
        label = labels.get(cls_id, "unknown")

        # DROWSY COUNTER LOGIC
        if label == "drowsy":
            drowsy_counter += 1
        else:
            drowsy_counter = 0

        # Determine displayed state (same logic as GUI)
        alarm_is_active = (drowsy_counter >= DROWSY_THRESHOLD)
        
        if label == "absent":
            displayed_state = "ABSENT"
        elif label == "awake":
            displayed_state = "AWAKE"
        elif label == "drowsy" and alarm_is_active:
            displayed_state = "DROWSY_ALERT"
        else:  # drowsy before threshold
            displayed_state = "AWAKE"

        # GPIO CONTROL (same logic as GUI)
        if label == "absent":
            # Red LED - Face not detected
            red_led.on()
            green_led.off()
            buzzer.off()
            
        elif label == "awake":
            # Green LED - Driver awake
            green_led.on()
            red_led.off()
            buzzer.off()
            
        elif label == "drowsy":
            # Green LED - Face present (even if drowsy)
            green_led.on()
            red_led.off()
            
            # Buzzer only when threshold is reached
            if alarm_is_active:
                buzzer.on()
            else:
                buzzer.off()

      
        # Print only when displayed state changes
       
        if displayed_state != previous_displayed_state:
            timestamp = time.strftime("%H:%M:%S")
            
            if displayed_state == "ABSENT":
                print(f"[{timestamp}] Face not detected")
            
            elif displayed_state == "AWAKE":
                print(f"[{timestamp}] Awake")
            
            elif displayed_state == "DROWSY_ALERT":
                print(f"[{timestamp}] DROWSY - ALERT!")
                print("=" * 50)
            
            previous_displayed_state = displayed_state

       
        # DISPLAY
       
        # Determine text color based on displayed state
        if displayed_state == "ABSENT":
            display_text = "Face not detected"
            color = (0, 0, 255)  # Red
        elif displayed_state == "AWAKE":
            display_text = "Awake"
            color = (0, 255, 0)  # Green
        else:  # DROWSY_ALERT
            display_text = "DROWSY - ALERT"
            color = (0, 0, 255)  # Red
        
        alarm_status = "ON" if alarm_is_active else "OFF"
        
        cv2.putText(frame, f"State: {display_text}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, f"Counter: {drowsy_counter}/{DROWSY_THRESHOLD}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


        cv2.imshow("Driver Monitor", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

except KeyboardInterrupt:
    print("\n" + "=" * 50)
    print("System stopped by user")
    print("=" * 50)

except Exception as e:
    print(f"Error: {e}")

finally:
    # CLEANUP
  
    picam2.stop()
    cv2.destroyAllWindows()
    
    # Turn off all devices
    for device in [green_led, red_led, buzzer]:
        device.off()