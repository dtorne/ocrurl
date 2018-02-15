import time
from picamera import PiCamera
import subprocess
import sys
from gpiozero import LED
from gpiozero import Button
from signal import pause

IMAGE_FILE = "/home/pi/Pictures/camera.jpg"
OUTPUT_TEXT = "/home/pi/Pictures/output"
TESS_PATH = "/usr/local/bin/"
COMMAND = [TESS_PATH+"tesseract", IMAGE_FILE, OUTPUT_TEXT]
SECS = 500

def main():
    
    def capture():
        red.on()
        camera.capture(IMAGE_FILE)
        subprocess.run(COMMAND)
        red.off()

    red = LED(17)  
    #pause()
    button = Button(2)
    button.when_pressed = capture
    camera = PiCamera()
    #camera.resolution = (400, 200)
    camera.video_stabilization = True
    camera.start_preview()
    time.sleep(SECS)
    red.off()
    camera.stop_preview()
    
if __name__ == "__main__":
    main()
    sys.exit()
