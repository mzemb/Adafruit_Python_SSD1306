import time, subprocess, atexit
import Adafruit_SSD1306
from PIL import Image,ImageDraw,ImageFont
from math import ceil
import RPi.GPIO as GPIO

#TODO: speedtest during the night
#TODO: bip when dead ?

class S1306(object):
    def __init__(self):
        self.buttons = {
            "L":27 
        ,   "R":23 
        ,   "C":4 
        ,   "U":17 
        ,   "D":22 
        ,   "A":5 
        ,   "B":6 
        }

def initGpio():
    GPIO.setmode(GPIO.BCM)
    s1306 = S1306()
    for button in s1306.buttons.keys():
        pin = s1306.buttons[button]
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.RISING, callback=buttonCb, bouncetime=200)

def init():

    initGpio()

    jolly = Image.open('/home/pi/Adafruit_Python_SSD1306/jollyRoger.ppm').convert('1')

    # 128x32 display with hardware I2C:
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)
    disp.begin()
    cls(disp)
    atexit.register(cls,disp)

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new('1', (disp.width, disp.height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    drawBlackFilledBox(draw, disp)

    try:
        font = ImageFont.truetype("/home/pi/Adafruit_Python_SSD1306/start.ttf", 8, encoding="unic")
    except:
        font = ImageFont.load_default()

    return (disp,draw,font,image,jolly)

def cls(disp):
    disp.clear()
    disp.display()

def drawBlackFilledBox(draw, disp):
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

def addLine(text):
    global cur
    draw.text((0, cur), text,  font=font, fill=255)
    cur = cur + 8 + 1 # +1 for spacing between lines

def render(disp):
    global cur
    cur = 0
    disp.image(image)
    disp.display()

def runCmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True)
    except:
        pass
        out = ""
    return out

def ping(hostnames):
    processes = []
    results = {}
    for hostname in hostnames:
        cmd = "/bin/ping -D -w 3 -c 10 -i 0.3 -q %s" % hostname
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT , shell=True)
        processes.append((hostname,process))

    for hostname,process in processes:
        process.wait()
        loss = "100%"
        avgMs = "-"
        for line in process.stdout:
            if line.find("packet loss") != -1:
                loss = line.split(",")[-2].strip().split()[0]
                loss = int(float(loss.replace("%","")) * 100)
            if line.find("rtt") != -1:
                avgMs = int(ceil(float(line.split('/')[-3])))
        results[hostname] = {"loss":loss,"ms":avgMs}
    return results

def displayImg(jolly):
    disp.image(jolly)
    disp.display()
    time.sleep(1)

def buttonCb(channel):
    global hide
    #print('Edge detected on channel %s' % channel)
    hide = not hide
    if hide:
        addLine("hiding")

if __name__ == "__main__":

    cur = 0
    hide = False
    disp,draw,font,image,jolly = init()

    while True:
   
        if hide:
            cls(disp)

        else:
            drawBlackFilledBox(draw, disp)

            hosts = {
                "192.168.0.1":"modem"
            ,   "89.2.0.1":   "dnsred"
            ,   "8.8.8.8":    "google"
            }

            results = ping(hosts.keys())

            for hostname in results.keys():
                result = results[hostname]
                alias = hosts[hostname]
                try:
                    work = 100 - int(result["loss"])
                except:
                    work = 0
                ms = min(result["ms"],999)
                text = "%6s:%3sms %s" % (alias[0:6], ms, work)
                addLine(text)
                results[alias] = result

            #addLine("extra1")
            #addLine("extra2")
            #addLine("extra3")
            #addLine("extra4")

            if results["modem"]["loss"] > 10:
                displayImg(jolly)

            #curTime = time.strftime("%H:%M:%S", time.localtime(time.time()))
            #addLine(curTime)

            render(disp)

        time.sleep(1)

