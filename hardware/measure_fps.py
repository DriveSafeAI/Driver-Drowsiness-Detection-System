from picamera2 import Picamera2
import time

picam2 = Picamera2()

config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

num_frames = 100
start_time = time.time()
for _ in range(num_frames):
    frame = picam2.capture_array()
end_time = time.time()

fps = num_frames / (end_time - start_time)
print(f"Approx FPS: {fps}")


