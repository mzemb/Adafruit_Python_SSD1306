#/bin/bash
# from https://learn.adafruit.com/adafruit-128x64-oled-bonnet-for-raspberry-pi/usage
set -o errexit
set -o nounset
set -o pipefail

sudo apt-get update
sudo apt-get install build-essential python-dev python-pip
sudo pip install RPi.GPIO

sudo apt-get install python-imaging python-smbus

sudo apt-get install git

git clone git@github.com:mzemb/Adafruit_Python_SSD1306.git
cd Adafruit_Python_SSD1306

sudo python setup.py install

echo now shutdown the pi, plug the screen, and on next boot "sudo i2cdetect -y 1" should output 0x3c

