/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2019 Fetch.AI Limited
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*
* ------------------------------------------------------------------------------
 */

package main

import (
	"encoding/hex"
	"fmt"

	"github.com/btcsuite/btcd/btcec"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/multiformats/go-multiaddr"
)

// DHTPeerOption for dhtpeer.New
type DHTPeerOption func(*DHTPeer) error

// IdentityFromFetchAIKey for dhtpeer.New
func IdentityFromFetchAIKey(key string) DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.key, dhtPeer.publicKey, err = KeyPairFromFetchAIKey(key)
		if err != nil {
			return err
		}
		return nil
	}
}

// RegisterAgentAddress for dhtpeer.New
func RegisterAgentAddress(addr string, isReady func() bool) DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.myAgentAddress = addr
		dhtPeer.myAgentReady = isReady
		return nil
	}
}

// BootstrapFrom for dhtpeer.New
func BootstrapFrom(entryPeers []string) DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.bootstrapPeers, err = GetPeersAddrInfo(entryPeers)
		if err != nil {
			return err
		}
		return nil
	}
}

// LocalURI for dhtpeer.New
func LocalURI(host string, port uint16) DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.localMultiaddr, err =
			multiaddr.NewMultiaddr(fmt.Sprintf("/ip4/%s/tcp/%d", host, port))
		if err != nil {
			return err
		}
		dhtPeer.host = host
		dhtPeer.port = port
		return nil
	}
}

// PublicURI for dhtpeer.New
func PublicURI(host string, port uint16) DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.publicMultiaddr, err =
			multiaddr.NewMultiaddr(fmt.Sprintf("/dns4/%s/tcp/%d", host, port))
		if err != nil {
			return err
		}
		dhtPeer.publicHost = host
		dhtPeer.publicPort = port
		return nil
	}
}

// EnableDelegateService for dhtpeer.New
func EnableDelegateService(port uint16) DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.delegatePort = port
		return nil
	}
}

// EnableRelayService for dhtpeer.New
func EnableRelayService() DHTPeerOption {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.enableRelay = true
		return nil
	}

}

/*
   Helpers
*/

// KeyPairFromFetchAIKey  key pair from hex encoded secp256k1 private key
func KeyPairFromFetchAIKey(key string) (crypto.PrivKey, crypto.PubKey, error) {
	pk_bytes, err := hex.DecodeString(key)
	if err != nil {
		return nil, nil, err
	}

	btc_private_key, _ := btcec.PrivKeyFromBytes(btcec.S256(), pk_bytes)
	prvKey, pubKey, err := crypto.KeyPairFromStdKey(btc_private_key)
	if err != nil {
		return nil, nil, err
	}

	return prvKey, pubKey, nil
}

// GetPeersAddrInfo Parse multiaddresses and convert them to peer.AddrInfo
func GetPeersAddrInfo(peers []string) ([]peer.AddrInfo, error) {
	pinfos := make([]peer.AddrInfo, len(peers))
	for i, addr := range peers {
		maddr := multiaddr.StringCast(addr)
		p, err := peer.AddrInfoFromP2pAddr(maddr)
		if err != nil {
			return pinfos, err
		}
		pinfos[i] = *p
	}
	return pinfos, nil
}

// IDFromFetchAIPublicKey Get PeeID (multihash) from fetchai public key
func IDFromFetchAIPublicKey(public_key string) (peer.ID, error) {
	b, err := hex.DecodeString(public_key)
	if err != nil {
		return "", err
	}

	pub_bytes := make([]byte, 0, btcec.PubKeyBytesLenUncompressed)
	pub_bytes = append(pub_bytes, 0x4) // btcec.pubkeyUncompressed
	pub_bytes = append(pub_bytes, b...)

	pub_key, err := btcec.ParsePubKey(pub_bytes, btcec.S256())
	if err != nil {
		return "", err
	}

	multihash, err := peer.IDFromPublicKey((*crypto.Secp256k1PublicKey)(pub_key))
	if err != nil {
		return "", err
	}

	return multihash, nil
}
