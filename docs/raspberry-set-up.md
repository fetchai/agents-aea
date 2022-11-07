This guide explains how to run an AEA inside a Raspberry Pi.

## Prerequisites

* <a href="https://thepihut.com/products/raspberry-pi-4-model-b?gclid=EAIaIQobChMImcuwvcfh4wIVirHtCh3szg2EEAAYASAAEgJQ_fD_BwE" target="_blank">Raspberry Pi 4</a> (You can also use Raspberry Pi3 b or Raspberry Pi3 b+)
* Internet connection (preferably wireless to minimise the number of wires connecting into your device)

## Preparing the Raspberry Pi

The easiest and recommended way to get started is to download and unzip our custom <a href="https://github.com/fetchai/aea-raspberry-pi/aea_rpi.img.tar.gz" target="_blank">AEA Raspberry Pi Image</a>, which includes the AEA installation as well as the most common dependencies.

However, you can also do the installation manually, and if you have a new Raspberry Pi, you can boot the system using the included SD card and skip the next section.

## Raspberry Pi Imager

Raspberry Pi Imager is a way to create an SD card for easy operating system installation on a Raspberry Pi.

First download the tool from <a href="https://www.raspberrypi.com/software/" target="_blank">this link</a>.

Then follow <a href="https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up" target="_blank">this guide</a> to set up your SD card.
When you get to the step of choosing an operating system, select the downloaded and unzipped AEA Raspberry Pi Image (`AEA_RPI.IMG`), or for a manual installation, select the latest Raspberry Pi OS.

Once you have set up your SD card, plug it into your Raspberry Pi, connect the power and boot up. 

## Booting up with the AEA Raspberry Pi Image

Upon booting up, you will be prompted to log in as the `aea` user and the password is `fetch`.
Next, navigate to settings menu to set up your internet connection.
Your Raspberry Pi is now ready to run an AEA!

## Booting up with the Raspberry Pi OS for manual installation

When you first boot your Raspberry Pi, you will be prompted to enter a password for the Raspberry Pi and your WiFi password so the device can access the internet. You may also be given the option to update the operating system and software. We recommend that you let the system update. Once finished you will be prompted to restart.

Even if your Raspberry Pi updated itself, we recommend that you make sure it is completely up to date using the terminal. Open a Terminal window (your Raspberry Pi might restart a few times during this process):

``` bash
sudo apt update -y 
sudo apt-get update
sudo apt-get dist-upgrade 
```

## Install common dependencies

``` bash
sudo apt install cmake
sudo apt install golang
```

## Install less common dependencies (optional)

For some of the more advanced AEAs hat make use of SciPy, such as the Car Park Detector, you will need some additional dependencies.

<details><summary>Install additional dependencies with the enclosed steps</summary>
<p>

Install additional dependencies
``` bash
sudo apt install gfortran
sudo apt install libatlas-base-dev
sudo apt install libopenblas-dev
```

Increase the swap space for the SciPy installation:
``` bash
sudo /bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024
sudo /sbin/mkswap /var/swap.1
sudo chmod 600 /var/swap.1
sudo /sbin/swapon /var/swap.1
```

Install NumPy and scikit-image (including SciPy)
``` bash
pip install numpy --upgrade
pip install scikit-image
```

</p>
</details>

## Install the AEA Framework

First, install pipenv: 

``` bash
sudo apt-get install pipenv
```

Once installed, create and launch a clean virtual environment with Python 3.9:

``` bash
pipenv --python 3.9 && pipenv shell
```

Finally, install the AEA framework from PyPI:

``` bash
pip install aea[all]
```

