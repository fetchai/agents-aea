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
aea fetch fetchai/my_first_aea:0.1.0
cd my_first_aea
```
``` bash
TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE		
```
``` bash
recipient_aea,sender_aea,fetchai/default:0.1.0,{"type": "bytes", "content": "aGVsbG8="}
```
``` bash
aea run
```
``` bash
aea run --connections fetchai/stub:0.1.0
```
``` bash
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```
``` bash
echo 'my_first_aea,sender_aea,fetchai/default:0.1.0,{"type": "bytes", "content": "aGVsbG8="}' >> input_file
```
``` bash
info: Echo Behaviour: act method called.
info: Echo Handler: message=Message(type=bytes content=b'hello'), sender=sender_aea
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```
``` bash
aea delete my_first_aea
```
``` bash
aea create my_first_aea		
cd my_first_aea		
```
``` bash
aea add skill fetchai/echo:0.1.0		
```
