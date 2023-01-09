# Build an AEA on a Raspberry Pi

This guide explains how to run an AEA inside a Raspberry Pi.

## Prerequisites

- <a href="https://thepihut.com/products/raspberry-pi-4-model-b?gclid=EAIaIQobChMImcuwvcfh4wIVirHtCh3szg2EEAAYASAAEgJQ_fD_BwE" target="_blank">Raspberry Pi 4</a> (You can also use Raspberry Pi3 b or Raspberry Pi3 b+)
- Internet connection (preferably wireless to minimise the number of wires connecting into your device)

## Preparing the Raspberry Pi

The easiest and recommended way to get started is to download and unzip our custom <a href="https://storage.googleapis.com/fetch-ai-aea-images/aea_rpi.img.tar.gz" target="_blank">AEA Raspberry Pi Image</a>, which includes the AEA installation as well as the most common dependencies.

However, you can also do the installation manually, and if you have a new Raspberry Pi, you can boot the system using the included SD card and skip the next section.

## Raspberry Pi Imager

Raspberry Pi Imager is a way to write to an SD card for easy installation on a Raspberry Pi.

First download the tool from <a href="https://www.raspberrypi.com/software/" target="_blank">this link</a>.

Then follow <a href="https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up" target="_blank">this guide</a> to set up your SD card.
When you get to the step of choosing an operating system, select the downloaded and unzipped AEA Raspberry Pi Image (`AEA_RPI.IMG`), or for a manual installation, select the latest Raspberry Pi OS.

Once you have set up your SD card, plug it into your Raspberry Pi, connect the power and boot up.

## Booting up with the AEA Raspberry Pi Image

After booting up, you may be prompted to log in as the `aea` user and the password is `fetch`.
Next, navigate to settings menu to set up your internet connection.
Your Raspberry Pi is now ready to run an AEA!
You can find some preloaded demos in the folder `~/aea/demos`.
To run these demos, navigate to one of the sub-folders and enter `aea run`.

## Booting up with the Raspberry Pi OS for Manual Installation

When you first boot your Raspberry Pi, you will be prompted to enter a password for the Raspberry Pi and your Wi-Fi password so the device can access the internet. You may also be given the option to update the operating system and software. We recommend that you let the system update. Once finished you will be prompted to restart.

Even if your Raspberry Pi updated itself, we recommend that you make sure it is completely up-to-date using the terminal. Open a Terminal window (your Raspberry Pi might restart a few times during this process):

``` bash
sudo apt update -y 
sudo apt-get update
sudo apt-get dist-upgrade 
```

## Install Common Dependencies

``` bash
sudo apt install cmake golang -y
```

## Install Less Common Dependencies (optional)

For some of the more advanced AEAs that make use of SciPy, such as the Car Park Detector, you will need some additional dependencies.

??? note "Install additional dependencies with the enclosed steps:"

    Install additional dependencies

    ``` bash
    sudo apt install gfortran libatlas-base-dev libopenblas-dev -y
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
    
    Revert to default swap space
    ``` bash
    sudo swapoff /var/swap.1
    sudo rm /var/swap.1
    ```

## Install the AEA Framework

Add to the local `PATH` environment variable (this will happen automatically the next time you log in):

``` bash
export PATH="$HOME/.local/bin:$PATH"
```

Finally, install the AEA framework from PyPI:

``` bash
pip install aea[all]
```

Check to make sure installation was successful:

``` bash
aea --version
```

Your Raspberry Pi is now ready to run an AEA!
