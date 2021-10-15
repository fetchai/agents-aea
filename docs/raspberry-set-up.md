This guide explains how to run an AEA inside a Raspberry Pi.

## Prerequisites

* <a href="https://thepihut.com/products/raspberry-pi-4-model-b?gclid=EAIaIQobChMImcuwvcfh4wIVirHtCh3szg2EEAAYASAAEgJQ_fD_BwE" target="_blank">Raspberry Pi 4</a> (You can also use Raspberry Pi3 b or Raspberry Pi3 b+)
* Internet connection (preferably wireless to minimise the number of wires connecting into your device)

## Preparing the Raspberry Pi

If you have a brand-new Raspberry Pi, you can simply insert the SD card, connect the power and boot up.
If you do not have a new Raspberry Pi SD card, you will need to make one. To do this follow the NOOBS instructions below.

## NOOBS

NOOBS is a way to create an SD card for easy operating system installation on a Raspberry Pi. 

First download noobs from <a href="https://www.raspberrypi.com/software/" target="_blank">this link</a>.

Then follow <a href="https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up" target="_blank">this guide</a> to set up your SD card.

Once you have set up your SD card, plug it into your Raspberry Pi, connect the power and boot up. When prompted, select the Raspbian operating system and click "Install".

## Booting up and updating the OS

When you first boot your Raspberry Pi, you will be prompted to enter a password for the Raspberry Pi and your WiFi password so the device can access the internet. You may also be given the option to update the operating system and software. We recommend that you let the system update. Once finished you will be prompted to restart.

Even if your Raspberry Pi updated itself, we recommend that you make sure it is completely up to date using the terminal. Open a Terminal window (your Raspberry Pi might restart a few times during this process):

``` bash
sudo apt update -y 
sudo apt-get update
sudo apt-get dist-upgrade 
```

## Install the AEA Framework

First, install pipenv: 

``` bash
sudo apt-get install pipenv
```

Once installed, create and launch a clean virtual environment with Python 3.7:

``` bash
pipenv --python 3.7 && pipenv shell
```

Finally, install the AEA framework from PyPI:

``` bash
pip install aea[all]
```

