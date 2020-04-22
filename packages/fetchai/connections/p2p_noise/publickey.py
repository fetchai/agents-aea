import os
import sys
from typing import Optional

import nacl.signing
import nacl.encoding


class PubKey:
    def __init__(
        self,
        *,
        strkey: Optional[str] = None,
        naclkey: Optional[nacl.signing.VerifyKey] = None
    ):
        if naclkey is not None:
            self._ed25519_pub = naclkey
        elif strkey is not None:
            self._ed25519_pub = nacl.signing.VerifyKey(
                strkey, encoder=nacl.encoding.HexEncoder
            )
        else:
            raise ValueError("Either 'strkey' or 'naclkey' must be set")

    def __str__(self):
        return self._ed25519_pub.encode(encoder=nacl.encoding.HexEncoder).decode(
            "ascii"
        )


class PrivKey:
    def __init__(self, key: Optional[str] = None):
        if key is None:
            self._ed25519 = nacl.signing.SigningKey.generate()
        else:
            self._ed25519 = nacl.signing.SigningKey(
                key, encoder=nacl.encoding.HexEncoder
            )

    def __str__(self):
        return self._ed25519.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")

    def hex(self):
        return self._ed25519.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")

    def pub(self) -> PubKey:
        return PubKey(naclkey=self._ed25519.verify_key)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: {} <swarm> <number>".format(sys.argv[0]), file=sys.stderr)
        sys.exit(-1)

    swarm = sys.argv[1]
    count = int(sys.argv[2])
    keys = list()

    for i in range(count):
        key = PrivKey()
        with open("{}_priv_{}.txt".format(swarm, i + 1), "w") as f:
            f.write(str(key))
        keys.append(key)

    pubs = "{}_pubs.txt".format(swarm)
    with open(pubs, "w+") as f:
        f.writelines([str(key.pub()) + os.linesep for key in keys])

    print(
        "{} keys saved to {} and {}_priv_[1-{}].txt".format(count, pubs, swarm, count)
    )
