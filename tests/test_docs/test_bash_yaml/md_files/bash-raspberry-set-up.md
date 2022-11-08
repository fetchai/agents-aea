``` bash
sudo apt update -y 
sudo apt-get update
sudo apt-get dist-upgrade 
```
``` bash
sudo apt install cmake golang -y
```
``` bash
sudo apt install gfortran libatlas-base-dev libopenblas-dev -y
```
``` bash
sudo /bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024
sudo /sbin/mkswap /var/swap.1
sudo chmod 600 /var/swap.1
sudo /sbin/swapon /var/swap.1
```
``` bash
pip install numpy --upgrade
pip install scikit-image
```
``` bash
sudo swapoff /var/swap.1
sudo rm /var/swap.1
```
``` bash
export PATH="$HOME/.local/bin:$PATH"
```
``` bash
pip install aea[all]
```
``` bash
aea --version
```
