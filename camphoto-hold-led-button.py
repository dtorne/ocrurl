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
SECS = 1

global lights_on

def main():
    
    global lights_on
    lights_on = False
    
    def capture():
        global lights_on
        if not lights_on:
            led.on()
            camera.start_preview()
            lights_on = True
        else:
            camera.capture(IMAGE_FILE, use_video_port=True)
            camera.stop_preview()
            led.blink()     
            subprocess.run(COMMAND)
            led.off()
        
            with open(OUTPUT_TEXT + '.txt') as f:
                read_data = f.read()
            print(read_data)
            doing_ocr = False
            lights_on = False
    
            

    led = LED(17)  
    #pause()
    button = Button(2)
    button.when_pressed = capture
    camera = PiCamera()
    #camera.resolution = (1920, 1080)
    camera.video_stabilization = True
    while True:
        time.sleep(SECS)

    
if __name__ == "__main__":
    main()
    sys.exit()