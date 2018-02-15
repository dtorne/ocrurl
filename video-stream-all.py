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
import subprocess
import re
import cgi

IMAGE_FILE = "/home/pi/Pictures/camera.jpg"
OUTPUT_TEXT = "/home/pi/Pictures/output"
TESS_PATH = "/usr/local/bin/"
COMMAND = [TESS_PATH+"tesseract", IMAGE_FILE, OUTPUT_TEXT]
SECS = 600
PATTERN = r'\d{8}'
PAGE="""\
<html>
<head>
<title>Visual del lector</title>
</head>
<!--body style="background-color:#00CCFF;"-->
<h1>Lector. Apriete el dispositivo para visualizar y para leer.</h1>
<img src="stream.mjpg" width="960" height="190" />
</body>

<div id="result"></div>

<script>

if(typeof(EventSource) !== "undefined") {
    var source = new EventSource("/ocr");
    source.onmessage = function(event) {
        if(event.data == "refresh") {
            location.reload()
        }
        else {
            window.open(event.data, "_blank");
        }
        
    };
} else {
    document.getElementById("result").innerHTML = "Sorry, your browser does not support server-sent events...";
}

</script>
</html>
"""

CONF_PAGE = """\
<html>
<head>
<title>Ajustes del lector</title>
</head>
<!--body style="background-color:#00CCFF;"-->
<h1>Ajustes del lector</h1>
<br>
<body>

<form action="/sendurl" method="post">

  Pagina web de redireccionamiento<br>
  
  <input type="text" size=100 id="patternurl" name="patternurl" value="http://www.example.com/search?=ocrscan"><br>
  Ej: Al escanear transforma en substituyendo ocrscan por 232342. www.example.com/search?=232342
  <br><br>
  <input type="submit" value="Submit url">
</form>
<form action="/sendwifi" method="post">
  SIID Wifi<br>
  <input type="text" id="idwifi" name="idwifi" value="Nombre ID wifi">
  <br><br>
  Password
  <br>
  <input type="password" id="passwifi" name="passwifi" value="Pass Wifi"><br><br>
  <input type="submit" value="Submit wifi">
</form> 

</body>
</html>
"""

WIFI_CABEZERA = """ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=ES
"""

    
def addWifi(ssid, password):
    with open('data.txt', 'r') as myfile:
        data=myfile.read().replace('\n', '')
    if not (ssid in data and password in data):
        f=open("/etc/wpa_supplicant/wpa_supplicant.conf", "a+")
        f.write("\nnetwork={\n\tssid=\"%s\"\n\tpsk=\"%s\"\n}" % (ssid,password))

global lights_on
global id_num
global id_on
global url



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
    global id_num
    global url
    global id_on
    global lights_on
    
    id_num = "0"
    def do_POST(self):
        global url
        if self.path=="/sendurl":
            form = cgi.FieldStorage(
                    fp=self.rfile, 
                    headers=self.headers,
                    environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
            })

            print("Your name is: %s",form["patternurl"].value)
            url = form["patternurl"].value
            f=open("url", "w")
            f.write(url)
            f.close()
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'URL del escaner cambiada')
            return
        if self.path=="/sendwifi":
            form = cgi.FieldStorage(
                    fp=self.rfile, 
                    headers=self.headers,
                    environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
            })


            print("Your name is: %s",form["idwifi"].value)
            print("Your name is: %s",form["passwifi"].value)
            addWifi(form["idwifi"].value,form["passwifi"].value)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Wifi indroducida')
            return
        
		    
    def do_GET(self):
        global id_on
        global id_num
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
            id_on = False
        elif self.path == '/index.html':      
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            
        elif self.path == '/conf.html':      
            content = CONF_PAGE.encode('utf-8')
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

            if id_on:
                message = url
                message = message.replace("ocrscan",id_num)
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"data: ")
                self.wfile.write(message.encode('utf-8'))
                self.wfile.write(b'\n\n')
                id_on = False
                
            if lights_on and id_num == "0":
                message = "refresh"
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"data: ")
                self.wfile.write(message.encode('utf-8'))
                self.wfile.write(b'\n\n')
                id_num = "00"
            
                    
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution = (1920,380),framerate=24) as camera:
    global id_num   
    global lights_on
    global id_on
    global url
    
    id_num = "0"
    
    with open('url', 'r') as myfile:
        data=myfile.read().replace('\n', '')
    url = data
    
    lights_on = False
    id_on = False
    
    def capture():
        global lights_on
        global id_num
        global id_on
    
        
        if not lights_on:
            led.on()
            camera.start_recording(output, format='mjpeg')
            lights_on = True
        else:
            global id_on
            camera.capture(IMAGE_FILE, use_video_port=True)
            camera.stop_recording()
            led.blink()     
            subprocess.run(COMMAND)
            led.off()
                
            with open(OUTPUT_TEXT + '.txt') as f:
                read_data = f.read()
            print("Data: \n")
            print(read_data)
            read_data = read_data.replace(" ","")
            read_data = read_data.replace("\"","")
            read_data = read_data.replace("'","")
            res_search = re.search(PATTERN, read_data)
            if res_search:
                id_num = res_search.group()
                print(id_num)
                id_on = True
            lights_on = False

    led = LED(17)  
    #pause()
    button = Button(2)
    button.when_pressed = capture
    camera.video_stabilization = True
    output = StreamingOutput()
    
    try:
        address = ('', 8001)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
