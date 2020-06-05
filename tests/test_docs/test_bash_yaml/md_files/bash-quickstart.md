``` bash
mkdir my_aea_projects/
cd my_aea_projects/
```
``` bash
which pipenv
```
``` bash
touch Pipfile && pipenv --python 3.7 && pipenv shell
```
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/examples
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```
``` bash
pip install aea[all]
```
``` bash
sudo apt-get install python3.7-dev
```
``` bash
aea init
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
                         
v0.3.3

AEA configurations successfully initialized: {'author': 'fetchai'}
```
``` bash
aea fetch fetchai/my_first_aea:0.4.0
cd my_first_aea
```
``` bash
aea create my_first_aea
cd my_first_aea
```
``` bash
aea add skill fetchai/echo:0.1.0
```
``` bash
TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE,
```
``` bash
recipient_aea,sender_aea,fetchai/default:0.1.0,\x08\x01*\x07\n\x05hello,
```
``` bash
aea run
```
``` bash
aea run --connections fetchai/stub:0.4.0
```
``` bash
    _     _____     _    
   / \   | ____|   / \   
  / _ \  |  _|    / _ \  
 / ___ \ | |___  / ___ \ 
/_/   \_\|_____|/_/   \_\
                         
v0.3.3

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
echo 'my_first_aea,sender_aea,fetchai/default:0.1.0,\x08\x01*\x07\n\x05hello,' >> input_file
```
``` bash
info: Echo Behaviour: act method called.
info: Echo Handler: message=Message(dialogue_reference=('', '') message_id=1 target=0 performative=bytes content=b'hello'), sender=sender_aea
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
aea delete my_first_aea
```