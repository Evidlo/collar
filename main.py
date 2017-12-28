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
import math
from pinmap import amica

ap = network.WLAN(network.AP_IF)
password = open('password.txt').read().rstrip('\n')
hostname = 'knuckles'
ap.config(essid='KnucklesWifi', password=password)
if not ap.active(): ap.active(True)

timer = machine.Timer(1)
timer_initialized = False

red = machine.PWM(machine.Pin(amica['D1']))
green = machine.PWM(machine.Pin(amica['D2']))
blue = machine.PWM(machine.Pin(amica['D5']))
red_duty = 0
green_duty = 0
blue_duty = 0
red.freq(200)
green.freq(200)
blue.freq(200)
red.duty(red_duty)
green.duty(green_duty)
blue.duty(blue_duty)

lights_on = True
def flash(_):
    global lights_on
    if lights_on:
        red.duty(0)
        green.duty(0)
        blue.duty(0)
        lights_on = False
    else:
        red.duty(red_duty)
        green.duty(green_duty)
        blue.duty(blue_duty)
        lights_on = True

count = 0
def party(_):
    global count
    count = (count + 1) % 99
    red.duty(int(1023 * (math.sin(2 * math.pi * float(count) / 99) / 2 + 1/2)))
    green.duty(int(1023 * (math.sin(2 * math.pi * float((count + 33) % 99) / 99) / 2 + 1/2)))
    blue.duty(int(1023 * (math.sin(2 * math.pi * float((count + 66) % 99) / 99) / 2 + 1/2)))

def ok(socket):
    socket.write("HTTP/1.1 200 OK\r\n\r\n")
    html = open('index.html').read()
    socket.write(html)

def err(socket, code, message):
    socket.write("HTTP/1.1 "+code+" "+message+"\r\n\r\n")
    socket.write("<h1>"+message+"</h1>")

def handle(socket):
    global red_duty, blue_duty, green_duty, timer_initialized
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
                red_duty, green_duty, blue_duty, radio = [color.split(b'=')[1] for color in query.split(b'&')]
                red_duty = int(red_duty)
                green_duty = int(green_duty)
                blue_duty = int(blue_duty)
                if radio == b'solid':
                    if timer_initialized:
                        timer.deinit()
                        timer_initialized = False
                    red.duty(red_duty)
                    green.duty(green_duty)
                    blue.duty(blue_duty)
                if radio == b'flash':
                    timer.init(period=100, mode=machine.Timer.PERIODIC, callback=flash)
                    timer_initialized = True

                elif radio == b'party':
                    timer.init(period=100, mode=machine.Timer.PERIODIC, callback=party)
                    timer_initialized = True

            ok(socket)

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
        try:
            socket.write("HTTP/1.1 500 Internal Server Error\r\n\r\n")
            socket.write("<h1>Internal Server Error</h1>")
        except Exception as e:
            print(e)
    socket.close()
