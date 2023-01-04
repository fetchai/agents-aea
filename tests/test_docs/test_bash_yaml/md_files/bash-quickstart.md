``` bash
python3 --version
```
``` bash
sudo apt-get install python3.8-dev
```
``` bash
curl https://raw.githubusercontent.com/valory-xyz/open-aea/main/scripts/install.sh --output install.sh
chmod +x install.sh
./install.sh
```
```bash
docker pull valory/open-aea-user:latest
```
```bash
docker run -it -v $(pwd):/agents --workdir=/agents valory/open-aea-user:latest
```
```bash
docker run -it -v %cd%:/agents --workdir=/agents valory/open-aea-user:latest
```
``` bash
mkdir my_aea_projects/
cd my_aea_projects/
```
``` bash
mkdir my_aea_projects/ && cd my_aea_projects/
```
``` bash
which pipenv
```
``` bash
touch Pipfile && pipenv --python 3.10 && pipenv shell
```
``` bash
svn export https://github.com/valory-xyz/open-aea.git/trunk/examples
svn export https://github.com/valory-xyz/open-aea.git/trunk/scripts
svn export https://github.com/valory-xyz/open-aea.git/trunk/packages
```
``` bash
echo "$SHELL"
```
``` bash
pip install open-aea[all]
pip install open-aea-cli-ipfs
```
```
svn checkout https://github.com/valory-xyz/open-aea/tags/v1.27.0.post1/packages packages
```

``` bash
sudo apt-get install python3.10-dev
```
``` bash
aea init --remote
```
``` bash
Do you have a Registry account? [y/N]: n
Create a new account on the Registry now:
Username: fetchai
Email: hello@fetch.ai
Password:
Please make sure that passwords are equal.
Confirm password:
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.7.0

AEA configurations successfully initialized: {'author': 'fetchai'}
```
``` bash
aea fetch open_aea/my_first_aea:0.1.0:bafybeiewms67jpwf46u4wwh6tbzedsi5jffajnywgydeo5nlvvr6pcz2zm --remote
cd my_first_aea
```
``` bash
aea create my_first_aea
cd my_first_aea
```
``` bash
aea add connection fetchai/stub:0.21.0
```
``` bash
aea add skill fetchai/echo:0.19.0
```
``` bash
TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE,
```
``` bash
recipient_aea,sender_aea,fetchai/default:1.0.0,\x08\x01\x12\x011*\x07\n\x05hello,
```
``` bash
aea install
```
``` bash
aea generate-key ethereum
aea add-key ethereum
```
``` bash
aea run
```
``` bash
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.7.0

Starting AEA 'my_first_aea' in 'async' mode ...
info: Echo Handler: setup method called.
info: Echo Behaviour: setup method called.
info: [my_first_aea]: Start processing messages...
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
...
```

``` bash
info: Echo Behaviour: act method called.
info: Echo Handler: message=Message(dialogue_reference=('1', '') message_id=1 target=0 performative=bytes content=b'hello'), sender=my_first_aea_interact
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```
``` bash
echo 'my_first_aea,sender_aea,fetchai/default:1.0.0,\x12\x10\x08\x01\x12\x011*\t*\x07\n\x05hello,' >> input_file
```
``` bash
info: Echo Behaviour: act method called.
Echo Handler: message=Message(sender=sender_aea,to=my_first_aea,content=b'hello',dialogue_reference=('1', ''),message_id=1,performative=bytes,target=0), sender=sender_aea
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```
``` bash
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
^C my_first_aea interrupted!
my_first_aea stopping ...
info: Echo Handler: teardown method called.
info: Echo Behaviour: teardown method called.
```
``` bash
pipenv run pytest test.py
```
``` bash
aea delete my_first_aea
```


``` bash
aea fetch open_aea/my_first_aea:0.1.0:bafybeiewms67jpwf46u4wwh6tbzedsi5jffajnywgydeo5nlvvr6pcz2zm --remote
cd my_first_aea
```

``` bash
aea fetch open_aea/my_first_aea:0.1.0:bafybeiewms67jpwf46u4wwh6tbzedsi5jffajnywgydeo5nlvvr6pcz2zm --remote
cd my_first_aea
```

```bash
mkdir packages
cd my_first_aea
aea add protocol fetchai/default:1.0.0:bafybeifdodei24xy4zsnmurg3dbbe2ysp7ii7v5bmrsgl7stt7lj22pezq --remote
aea push protocol fetchai/default --local
cd ..
aea delete my_aea
```