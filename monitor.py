import time, subprocess, atexit
import Adafruit_SSD1306
from PIL import Image,ImageDraw,ImageFont

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

    font = ImageFont.load_default()

    return (disp,draw,font,image)

def cls(disp):
    disp.clear()
    disp.display()

def drawBlackFilledBox(draw, disp):
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

def addLine(text):
    global cur
    draw.text((0, cur), text,  font=font, fill=255)
    cur = cur + 8

def render():
    global cur
    cur = 0
    disp.image(image)
    disp.display()

def ping(hostname):
    return subprocess.Popen(["/bin/ping", "-c 10", "-D", "-i 0.3", "-q", hostname], stdout=subprocess.PIPE).stdout.read()

def getLastPings():
    subprocess.checkoutput("/home/pi/tmp/upmonitor.log")

def runCmd(cmd):
    return subprocess.check_output(cmd, shell=True)

def displayJollyRoger():
    disp.image(jolly)
    disp.display()
    time.sleep(1)

if __name__ == "__main__":

    cur = 0
    disp,draw,font,image = init()

    while True:
    
        drawBlackFilledBox(draw, disp)

        lastLines = runCmd("tail -2 /home/pi/tmp/upmonitor.log")

        pings = []
        for line in lastLines.split('\n'):
            if len(line) > 0:
                t = line.split()[0]
                pings.append(t)
        print pings

        if all(p == 0 for p in pings):
            displayJollyRoger()
        elif 0 in pings:
            addLine("WARNING: one ping failed")
        else:
            print pings
            curTime = time.strftime("%H:%M:%S", time.localtime(time.time()))
            ms = float(pings[-1])
            text = "%s %.1f ms" % (curTime, ms)
            addLine(text)

        render()
        time.sleep(1)
