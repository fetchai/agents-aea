This is a simple demo that introduces you to the main components of an AEA.

A full break down of the development is covered within the <a href="../quickstart/">Development Quickstart</a>. It is highly recommended that developers begin by following the quick start!

This demo assumes you have followed the setup guide.

The fastest way to have your first AEA is to fetch one that already exists!

``` bash
aea fetch open_aea/my_first_aea:0.1.0:bafybeifelwg4md24lwpxgx7x5cugq7ovhbkew3lxw43m52rdppfn5o5g4i --remote
cd my_first_aea
```
### Install AEA dependencies

``` bash
aea install
```

### Add and create a private key

All AEAs need a private key to run. Add one now:

``` bash
aea generate-key ethereum
aea add-key ethereum
```

### Run the AEA

Run the AEA.

``` bash
aea run
```

You will see the echo skill running in the terminal window (an output similar to the one below).

``` bash
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.2.0

Starting AEA 'my_first_aea' in 'async' mode ...
info: Echo Handler: setup method called.
info: Echo Behaviour: setup method called.
info: [my_first_aea]: Start processing messages...
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
...
```
### Interact with the AEA

From a different terminal and same directory (i.e. the <code>my_first_aea</code> project), you can send the AEA a message wrapped in an envelope via the input file.

``` bash
echo 'my_first_aea,sender_aea,fetchai/default:1.0.0,\x12\x10\x08\x01\x12\x011*\t*\x07\n\x05hello,' >> input_file
```

You will see the <code>Echo Handler</code> dealing with the envelope and responding with the same message to the <code>output_file</code>, and also decoding the Base64 encrypted message in this case.

``` bash
info: Echo Behaviour: act method called.
Echo Handler: message=Message(sender=sender_aea,to=my_first_aea,content=b'hello',dialogue_reference=('1', ''),message_id=1,performative=bytes,target=0), sender=sender_aea
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```

Note, due to the dialogue reference having to be incremented, you can only send the above envelope once!

### Stop the AEA

You can stop an AEA by pressing `CTRL C`.

Once you do, you should see the AEA being interrupted and then calling the `teardown()` methods:

``` bash
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
^C my_first_aea interrupted!
my_first_aea stopping ...
info: Echo Handler: teardown method called.
info: Echo Behaviour: teardown method called.
```

To learn more about the folder structure of an AEA project read on <a href="../package-imports/">here</a>.

A full break down of the development is covered within the <a href="../quickstart/">Development Quickstart</a>. It is highly recommended that developers begin by following the quick start!