
import cv2
import picamera2

picam2 = picamera2.Picamera2()


config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

try:
    while True:
     
        frame = picam2.capture_array()
        
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        cv2.imshow("Camera Test", frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    picam2.stop()
    cv2.destroyAllWindows()

