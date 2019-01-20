import time, subprocess, atexit
import Adafruit_SSD1306
from PIL import Image,ImageDraw,ImageFont
from math import ceil

def init():
    jolly = Image.open('jollyRoger.ppm').convert('1')

    # 128x32 display with hardware I2C:
    disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
    disp.begin()
    cls(disp)
    #atexit.register(cls)

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new('1', (disp.width, disp.height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    drawBlackFilledBox(draw, disp)

    try:
        font = ImageFont.truetype("start.ttf", 8, encoding="unic")
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
    cur = cur + 8

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

if __name__ == "__main__":

    cur = 0
    disp,draw,font,image,jolly = init()

    while True:
    
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
            text = "%6s: " % (alias[0:6])
            if result["loss"] > 0:
                text += (" %s LOSS" % result["loss"])
            else:
                text += (" %4s ms" % result["ms"])
            addLine(text)
            results[alias] = result

        if results["modem"]["loss"] > 10:
            displayImg(jolly)

        #curTime = time.strftime("%H:%M:%S", time.localtime(time.time()))
        #addLine(curTime)

        render(disp)
        time.sleep(1)

