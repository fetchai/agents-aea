!!! Warning
Work in progress.

# Car Park Agent Application

The Fetch.ai car park agent application is made up of three components:

-   A Raspberry Pi hardware device with camera module viewing a car park.
-   A car park agent GUI running on the Raspberry Pi that collects data on free spaces and serves it up for purchase on the Fetch.ai network.
-   A remote client agent GUI that connects to the Raspberry Pi and buys data.

| Hardware                                            |               Car Park Agent GUI               |                 Client Agent GUI                 |
| --------------------------------------------------- | :--------------------------------------------: | :----------------------------------------------: |
| <img src="../assets/device_small.jpg" height="150"> | <img src="../assets/pi_live.jpg" height="150"> | <img src="../assets/client_04.jpg" height="150"> |

## Raspberry Pi hardware set up

The hardware set up is the most time consuming part of these instructions.

We assume the developer has some familiarity with Raspberry Pi and refer them to the manufacturer's instructions. However, we do list any problems we encountered and their solutions below.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>We have used the Raspberry Pi 4. You are welcome to use earlier versions but the set up may change slightly.</p>
</div>

Follow the manufacturer's instructions to set up the Raspberry Pi 4 hardware device: <a href="https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up/2" target=_blank>https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up/2</a>.

### Install and update the OS

Install the Raspbian OS and update it.

```bash
sudo apt update -y
sudo apt-get update
sudo apt-get dist-upgrade
sudo reboot
```

### Enable camera, ssh, and VNC

Click on the Raspberry symbol in the top left of the screen.

Select Preferences then Raspberry Pi Configuration.

<center>
<img src="../assets/config_nav.png" />
</center>
<br/>

Enable the Camera, SSH, and VNC options.

<center>
<img src="../assets/config_dlg.png" />
</center>

### Set up camera module

Follow the manufacturer's instructions to set up the Raspberry Pi Camera module: <a href="https://projects.raspberrypi.org/en/projects/getting-started-with-picamera" target=_blank>https://projects.raspberrypi.org/en/projects/getting-started-with-picamera</a>.

Configure and test the camera software: <a href="https://www.raspberrypi.org/documentation/configuration/camera.md" target=_blank>https://www.raspberrypi.org/documentation/configuration/camera.md</a>.

Set up your Pi to physically view the car park. We'll leave that to you.

### Potential issues

1. Make sure you use the first port, `HDMI 0` on the Pi for the initial set up monitor.
2. If you install the Pi with a used SD card, you will need to reformat the card with NOOBS: <a href="https://www.raspberrypi.org/downloads/noobs/" target=_blank>https://www.raspberrypi.org/downloads/noobs/</a>.
3. Fix the screen resolution issues by editing the configuration.

```bash
sudo raspi-config
```

Select the `1920X1080` resolution option - number 31.

Then update the configuration file as follows. Open it.

```bash
sudo nano /boot/config.txt
```

And make sure the following three lines are commented out.

```bash
# Enable DRM VC4 V3D driver on top of the dispmanx display stack
# dtoverlay=vc4-fkms-v3d
# max_framebuffers=2
```

## Agent server application installation

Now we are ready to install the car park agent GUI server application on the Raspberry Pi.

### Get the code

```bash
cd ~/Desktop
git clone https://github.com/fetchai/carpark_agent.git
cd carpark_agent
```

### Download datafile

This is required for the machine learning algorithms.

```bash
./car_detection/weights/download_weights.sh
```

Install the required libraries.

```bash
sudo apt-get install gcc htop vim mc python3-dev ffmpeg virtualenv libatlas-base-dev libsm6 libxext6 clang libblas3 liblapack3 liblapack-dev libblas-dev cython gfortran build-essential libgdal-dev libopenblas-dev liblapack3 liblapacke liblapacke-dev liblcms2-utils liblcms2-2 libwebpdemux2 python3-scipy python3-numpy python3-matplotlib libjasper-dev libqtgui4 libqt4-test protobuf-compiler python3-opencv gpsd gpsd-clients
```

### Activate a virtual environment.

```bash
pip3 install virtualenv
./run_scripts/create_venv.sh
source venv/bin/activate
```

### Install the software

```bash
python setup.py develop
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>We recommend that using `develop` as this creates a link to the code and so any changes you make will take immediate effect when you run the code.</p>
</div>

### Run it

```bash
./run_scripts/run_carpark_agent.sh
```

You should now see the agent running.

### Ensure agent start on boot (RPi4 only)

Ensure the startup script runs whenever we the Raspberry Pi turns on.

```bash
crontab -e
```

Pick an editor which will open a text file. Scroll to the bottom and add the following line.

```bash
@reboot /home/pi/Desktop/carpark_agent/run_scripts/run_carpark_agent.sh
```

Save and reboot. The agent should now start automatically on reboot.

### Get the Pi's ip address

We will need the ip address of the Raspberry Pi to connect remotely.

```bash
ifconfig
```

Returns something like:

```bash
...
wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
	inet 192.168.11.9  netmask 255.255.255.0  broadcast 192.168.11.255
...
```

The `inet` value is the Raspberry Pi's ip address.

<!--
### Get the code

``` bash
cd ~/Desktop
git clone https://github.com/fetchai/carpark_agent.git
cd carpark_agent
```
-->

### Connect to the app remotely

Download and install the VNC viewer onto your remote laptop: <a href="https://www.realvnc.com/en/connect/download/viewer/" target=_blank>https://www.realvnc.com/en/connect/download/viewer/</a>.

Add the Pi's ip address. You will be prompted for the Raspberry Pi password. The Raspberry Pi's desktop should appear.

### Get your remote desktop ip

Follow the <a href="https://www.tp-link.com/uk/support/faq/838/?utm_medium=select-local" target=_blank>instructions</a> to get your remote ip address.

### Connect to the Raspberry Pi

Start up the agent, if it is not running - but it should be.

```bash
cd Desktop/carpark_agent
./run_scripts/run_carpark_agent.sh
```

# STOPPED HERE - Monday 28th October

# The Pi server app instructions come next

From "When it starts up and you see the output from the camera, you can move your camera around so it is looking at the area...
