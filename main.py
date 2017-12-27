# Evan Widloski - 2017-12-21
# LED Collar
# Stolen from https://lab.whitequark.org/notes/2016-10-20/controlling-a-gpio-through-an-esp8266-based-web-server/

# Begin configuration
TITLE    = "Air conditioner"
GPIO_NUM = 5
# End configuration

import network
import machine
import usocket
from pinmap import amica

ap = network.WLAN(network.AP_IF)
ap.config(essid='KnucklesWifi', password=open('password.txt').read())
if not ap.active(): ap.active(True)

red = machine.PWM(machine.Pin(amica['D1']))
green = machine.PWM(machine.Pin(amica['D2']))
blue = machine.PWM(machine.Pin(amica['D5']))
red.freq(1000)
green.freq(1000)
blue.freq(1000)
red.duty(0)
green.duty(0)
blue.duty(0)


html = """
<!DOCTYPE html><title>Knuckle's Collar</title>
<html>
<body>
<form action="/led" method="GET">
<span>red</span><input name="red" type="range" value="{}" min="0" max="1023"/>
<span>green</span><input name="green" type="range" value="{}" min="0" max="1023"/>
<span>blue</span><input name="blue" type="range" value="{}" min="0" max="1023"/>
<input type='submit' value='OK'/>
</form>
</body>
</html>
"""

def ok(socket, red, green, blue):
    print('sending response')
    socket.write("HTTP/1.1 200 OK\r\n\r\n")
    socket.write(html.format(int(red), int(green), int(blue)))

def err(socket, code, message):
    socket.write("HTTP/1.1 "+code+" "+message+"\r\n\r\n")
    socket.write("<h1>"+message+"</h1>")

def handle(socket):
    (method, url, version) = socket.readline().split(b" ")
    if b"?" in url:
        (path, query) = url.split(b"?", 2)
    else:
        (path, query) = (url, b"")
    while True:
        header = socket.readline()
        if header == b"":
            return
        if header == b"\r\n":
            break

    print('path:',path)
    print('query:', query)
    print('url:', url)
    print('header:',header)
    print('method:',method)
    if version == b"HTTP/1.0\r\n" or version == b"HTTP/1.1\r\n":
        if method == b"GET":
            if path == b"off":
                red.duty(0)
                green.duty(0)
                blue.duty(0)
            elif path.startswith(b'/led'):
                red_duty, green_duty, blue_duty = [color.split(b'=')[1] for color in query.split(b'&')]
                red.duty(int(red_duty))
                green.duty(int(green_duty))
                blue.duty(int(blue_duty))
                ok(socket, red_duty, green_duty, blue_duty)
            else:
                ok(socket, 512, 512, 512)

    else:
        err(socket, "505", "Version Not Supported")


server = usocket.socket()
server.bind(('0.0.0.0', 80))
server.listen(1)
while True:
    try:
        (socket, sockaddr) = server.accept()
        handle(socket)
    except Exception as e:
        print(e)
        socket.write("HTTP/1.1 500 Internal Server Error\r\n\r\n")
        socket.write("<h1>Internal Server Error</h1>")
    socket.close()
