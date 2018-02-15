import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import random
from gpiozero import LED
from gpiozero import Button
from signal import pause
import re

IMAGE_FILE = "/home/pi/Pictures/camera.jpg"
OUTPUT_TEXT = "/home/pi/Pictures/output"
TESS_PATH = "/usr/local/bin/"
COMMAND = [TESS_PATH+"tesseract", IMAGE_FILE, OUTPUT_TEXT]
SECS = 600

PAGE="""\
<html>
<head>
<meta http-equiv="refresh" content="2" />
<title> picamera MJPEG streaming demo</title>
</head>
<body>
<h1 id='ocr-nu'>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>

<div id="result"></div>

<script>
if(typeof(EventSource) !== "undefined") {
    var source = new EventSource("/ocr");
    source.onmessage = function(event) {
    
        document.getElementById("result").innerHTML += "hjhj";
        window.open("https://www.softocr.com", "_blank");
    };
} else {
    document.getElementById("result").innerHTML = "Sorry, your browser does not support server-sent events...";
}

function myFunction() {

    document.getElementById("result").innerHTML = "page 1";
}
myFunction()
</script>
</html>
"""

PAGEOCR="""\
<html>
<head>
<meta http-equiv="refresh" content="2" />
<title> picamera MJPEG streaming demo</title>
</head>
<body>
<h1 id='ocr-nu'>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>

<div id="result"></div>

<script>
if (!!window.EventSource) {
  var source = new EventSource('/ocr');
} else {
  document.getElementById("result").innerHTML = "Received event";
}
function myFunction() {
    window.open("https://www.softocr.com", "_blank");
    document.getElementById("result").innerHTML = "page2";
}
myFunction()
</script>
</html>
"""


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = ''
            if random.randrange(5) == 2:
                content = PAGEOCR.encode('utf-8')
            else:
                content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/ocr':
            ocr_text = 'hello event'
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.write(b'sdfsdf\r\n')
            
            
                    
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    global id_num
    def capture():
        led.on()
        camera.capture(IMAGE_FILE)
        subprocess.run(COMMAND)
        led.off()
        #file = open(OUTPUT_TEXT+".txt”, “r”)
        #text = file.read()
        text = "lkjsf sdlfkj lk 23423423 lkjlj"
        id = re.search('\\d.*',text);
        id_num = id.group()
        print(id_num)

    led = LED(17)  
    #pause()
    button = Button(2)
    button.when_pressed = capture
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8001)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
