import time, subprocess, atexit
import Adafruit_SSD1306
from PIL import Image,ImageDraw,ImageFont
from math import ceil
import RPi.GPIO as GPIO

# crontab: @reboot sleep 30 && /usr/bin/python /home/pi/Adafruit_Python_SSD1306/monitor.py 2>&1 >> /home/pi/tmp/monitor.log

#TODO: log results
#TODO: speedtest during the night

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
    global hide
    GPIO.setmode(GPIO.BCM)
    s1306 = S1306()
    for button in s1306.buttons.keys():
        pin = s1306.buttons[button]
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.RISING, callback=buttonCb, bouncetime=200)
    time.sleep(.3)
    hide = False

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


def renderLines(disp):
    global cur
    cur = 0
    disp.image(image)
    disp.display()
    time.sleep(1)


def renderImg(jolly):
    disp.image(jolly)
    disp.display()
    time.sleep(0.3)


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
                loss = int(float(loss.replace("%","")))
            if line.find("rtt") != -1:
                avgMs = int(ceil(float(line.split('/')[-3])))
        results[hostname] = {"loss":loss,"ms":avgMs}
    return results


def buttonCb(channel):
    global hide
    global lossText
    global lossTime
    global mode
    print('debug: edge on channel %s at %s' % (channel, time.strftime("%H:%M:%S", time.localtime())))
    s1306 = S1306()
    cls(disp)
    if channel in [s1306.buttons["A"], s1306.buttons["B"]]:
        lossText = ""
        lossTime = 0
    elif channel == s1306.buttons["R"]:
        mode = MODES[0]
    elif channel == s1306.buttons["L"]:
        mode = MODES[1]
    else:
        hide = not hide
        renderLines(disp)


def getCurTime():
    return time.time()


def timeToString(t):
    return time.strftime("%d %b %Hh%M", time.localtime(t))


def renderPing():
    global hide
    loss = False
    lossText = ""
    lossTime = 0

    curTime = getCurTime()
    addLine("  %s" % timeToString(curTime))
    
    results = ping(hosts.keys())
    
    for hostname in results.keys():
        result = results[hostname]
        alias = hosts[hostname]
        try:
            #print "host:%s loss:%s" % (alias,result["loss"])
            work = 100 - int(result["loss"])
        except:
            work = 0
        ms = min(result["ms"],999)
        text = "%6s:%3sms %s" % (alias[0:6], ms, work)
        addLine(text)
        results[alias] = result
        if work < 80 and curTime > lossTime:
            lossText = "err %s %s \non %s" % (alias, work, timeToString(curTime))
            loss = True
            lossTime = curTime
    
    addLine("")
    addLine(lossText)
    
    if loss:
        renderImg(jolly)
    renderLines(disp)


def onlyPrintable(string):
    return ''.join(s for s in string if ord(s)>31 and ord(s)<126)


def contains(string,x):
    return string.find(x) != -1


def getVpnClients():

    cmd = "/usr/local/bin/pivpn clients"
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT , shell=True)
    process.wait()

    prelude = True
    clients = []
    for line in process.stdout:
        if len(line.strip()) > 0:
            text = onlyPrintable(line)
            if not prelude:
                x = line.split()
                #print x
                host = x[0]
                ip = x[2]
                clients.append("%s %s" % (host,ip))
    
            if contains(text,"Name") and contains(text,"Connected Since"):
                prelude = False

    return clients


def renderVpn():
    clients = getVpnClients()
    addLine("%d pivpn clients" % len(clients))
    addLine("")

    for client in clients:
        addLine(client)
    renderLines(disp)


def getIps():
    cmd = '/sbin/ip addr show | grep -e "[0-9]: " -e "inet "'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT , shell=True)
    process.wait()
    ips = []
    adapterName = None
    adapterIp = None
    adapterNames = ""
    for line in process.stdout:
        if len(line.strip()) > 0:
            #print line
            if contains(line, "inet "):
                adapterIp = line.split()[1].strip()
                #print "IP:%s" % line
                ips.append(adapterIp)
                #ips.append("%s %s" % (adapterName, adapterIp))
            else:
                adapterName = line.split()[1].strip().strip(':')[0:3]
                #print "NAME:%s" % line
                #ips.append(adapterName)
                adapterNames += " " + adapterName
    print adapterNames
    ips.insert(0, adapterNames)
    return ips


def renderIp():
    ips = getIps()
    for ip in ips:
        addLine(ip)
    renderLines(disp)



if __name__ == "__main__":

    MODES = ["ip","vpn","ping"]
    mode = MODES[0]
    hide = False
    cur = 0

    hosts = {
        "192.168.0.1":"modem"
    ,   "89.2.0.1":   "dnsred"
    ,   "8.8.8.8":    "google"
    #,   "1.2.3.4":    "dummy"
    }

    print "start at %s" % time.strftime("%H:%M:%S", time.localtime())

    disp,draw,font,image,jolly = init()

    while True:
 
        if hide:
            cls(disp)

        else:
            drawBlackFilledBox(draw, disp)

            if mode == "ip":
                renderIp()
            if mode == "ping":
                renderPing()
            if mode == "vpn":
                renderVpn()
            
        time.sleep(10)
