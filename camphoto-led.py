import time
from picamera import PiCamera
import subprocess
import sys
from gpiozero import LED
from signal import pause

IMAGE_FILE = "/home/pi/Pictures/camera.jpg"
OUTPUT_TEXT = "/home/pi/Pictures/output"
TESS_PATH = "/usr/local/bin/"
COMMAND = [TESS_PATH+"tesseract", IMAGE_FILE, OUTPUT_TEXT]
SECS = 3

def main():
    
    red = LED(17)
    red.on()
    #pause()
    camera = PiCamera()
    #camera.resolution = (400, 200)
    camera.video_stabilization = True
    camera.start_preview()
    #red.off()
    time.sleep(SECS)
    x = input("Enter: ")
    camera.capture(IMAGE_FILE)
    camera.stop_preview()
    subprocess.run(COMMAND)
    
if __name__ == "__main__":
    main()
    sys.exit()
    