## Prerequisites
Raspberry Pi 4  <a href="https://thepihut.com/products/raspberry-pi-4-model-b?gclid=EAIaIQobChMImcuwvcfh4wIVirHtCh3szg2EEAAYASAAEgJQ_fD_BwE" target="_blank">link</a> (You can also use Raspberry Pi3 b or Raspberry Pi3 b+)

I use a wireless network because, once your Raspberry Pi is set up, you want as few wires going to it as possible.

## Preparing the Raspberry Pi
If you have got a brand-new Raspberry Pi, you can simply insert the SD card, connect the power and boot up.
If you do not have a new Rasperry Pi SD card, you will need to make one. To do this follow the NOOBS instructions below.

## NOOBS
NOOBS is a way to get an SD card like it was when you got your Raspberry Pi new from the shop.
Go to the following link https://www.raspberrypi.org/downloads/ to download noobs. 
You can follow this guide to set up your sd card : https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up 

Once you have set up your SD card, plug it into your Raspberry Pi, connect the power and watch it boot up. When prompted, select the Raspbian operating system and click on Install.
Booting up and updating the OS

When you first boot your Raspberry Pi, you will be prompted to enter a password for the Raspberry PI and your wifi password so the Raspberry Pi has access to the internet. You may also be given the option to update the operating system and software. Let the system update and when it has finished you will be prompted to restart. Do this.
I recommend having these instructions easily accessible on your Raspberry Pi so you can copy and paste lines into the terminal. You will also be restarting your Raspberry Pi a few times during this process. 

Even if your Raspberry Pi updated itself, I recommend making sure it is completely up to date using the terminal. Open a Terminal window and type:
``` bash
sudo apt update -y 
sudo apt-get update
sudo apt-get dist-upgrade 
```

## Install a virtual environment
You will need to install pipenv. This is a virtual environment for python. Open a terminal and write the following command:

sudo apt-get install pipenv

## Create and launch a virtual environment
``` bash
pipenv --python 3.7 && pipenv shell
```

## Installing the AEA-framework
Install the package from source:
``` bash
pip install aea[all]
```

