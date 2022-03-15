/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2021 Fetch.AI Limited
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

package utils

import (
	"bytes"
	"context"
	"encoding/hex"
	"encoding/json"
	"errors"
	"libp2p_node/aea"
	"libp2p_node/mocks"
	"net"
	"reflect"
	"testing"

	"bou.ke/monkey"
	"github.com/golang/mock/gomock"
	"github.com/libp2p/go-libp2p-core/peer"
	kaddht "github.com/libp2p/go-libp2p-kad-dht"
	kbucket "github.com/libp2p/go-libp2p-kbucket"
	multiaddr "github.com/multiformats/go-multiaddr"
	"github.com/rs/zerolog"
	"github.com/stretchr/testify/assert"

	"crypto/ecdsa"
	"github.com/ethereum/go-ethereum/common/hexutil"
	ethCrypto "github.com/ethereum/go-ethereum/crypto"
	p2pCrypto "github.com/libp2p/go-libp2p-core/crypto"
)

// Crypto operations

func TestEthereumCrypto(t *testing.T) {
	//privateKey := "0xb60fe8027fb82f1a1bd6b8e66d4400f858989a2c67428a4e7f589441700339b0"
	publicKey := "0xf753e5a9e2368e97f4db869a0d956d3ffb64672d6392670572906c786b5712ada13b6bff882951b3ba3dd65bdacc915c2b532efc3f183aa44657205c6c337225"
	address := "0xb8d8c62d4a1999b7aea0aebBD5020244a4a9bAD8"
	publicKeySignature := "0x304c2ba4ae7fa71295bfc2920b9c1268d574d65531f1f4d2117fc1439a45310c37ab75085a9df2a4169a4d47982b330a4387b1ded0c8881b030629db30bbaf3a1c"

	addFromPublicKey, err := EthereumAddressFromPublicKey(publicKey)
	if err != nil || addFromPublicKey != address {
		t.Error(
			"Error when computing address from public key or address and public key don't match",
		)
	}

	_, err = BTCPubKeyFromEthereumPublicKey(publicKey)
	if err != nil {
		t.Errorf("While building BTC public key from string: %s", err.Error())
	}

	/*
		ethSig, err := secp256k1.Sign(hashedPublicKey, hexutil.MustDecode(privateKey))
		if err != nil {
			t.Error(err.Error())
		}
		println(hexutil.Encode(ethSig))
		hash := sha3.NewLegacyKeccak256()
		_, err = hash.Write([]byte(publicKey))
		if err != nil {
			t.Error(err.Error())
		}
		sha3KeccakHash := hash.Sum(nil)
	*/

	valid, err := VerifyEthereumSignatureETH([]byte(publicKey), publicKeySignature, publicKey)
	if err != nil {
		t.Error(err.Error())
	}

	if !valid {
		t.Errorf("Signer address don't match %s", addFromPublicKey)
	}
}

func TestFetchAICrypto(t *testing.T) {
	publicKey := "02358e3e42a6ba15cf6b2ba6eb05f02b8893acf82b316d7dd9cda702b0892b8c71"
	address := "fetch19dq2mkcpp6x0aypxt9c9gz6n4fqvax0x9a7t5r"
	peerPublicKey := "027af21aff853b9d9589867ea142b0a60a9611fc8e1fae04c2f7144113fa4e938e"
	pySigStrCanonize := "N/GOa7/m3HU8/gpLJ88VCQ6vXsdrfiiYcqnNtF+c2N9VG9ZIiycykN4hdbpbOCGrChMYZQA3G1GpozsShrUBgg=="

	addressFromPublicKey, _ := FetchAIAddressFromPublicKey(publicKey)
	if address != addressFromPublicKey {
		t.Error("[ERR] Addresses don't match")
	} else {
		t.Log("[OK] Agent address matches its public key")
	}

	valid, err := VerifyFetchAISignatureBTC(
		[]byte(peerPublicKey),
		pySigStrCanonize,
		publicKey,
	)
	if !valid {
		t.Errorf("Signature using BTC don't match %s", err.Error())
	}
	valid, err = VerifyFetchAISignatureLibp2p(
		[]byte(peerPublicKey),
		pySigStrCanonize,
		publicKey,
	)
	if !valid {
		t.Errorf("Signature using LPP don't match %s", err.Error())
	}
}

func TestSetLoggerLevel(t *testing.T) {
	assert.Equal(t, logger.GetLevel(), zerolog.Level(0), "Initial log level is not 0")

	lvl := zerolog.InfoLevel
	SetLoggerLevel(lvl)

	assert.Equal(
		t,
		logger.GetLevel(),
		lvl,
		"Waited for logger level %d but got %d",
		lvl,
		logger.GetLevel(),
	)
}

func Example_ignore() {
	ignore(errors.New("Test"))
	// Output: IGNORED: Test
}

func TestNewDefaultLoggerWithFields(t *testing.T) {
	fields := map[string]string{
		"test_field": "test_value",
	}
	var logBuffer bytes.Buffer
	logger := NewDefaultLoggerWithFields(fields).Output(&logBuffer)
	logger.Info().Msg("test")
	var jsonResult map[string]interface{}
	err := json.Unmarshal(logBuffer.Bytes(), &jsonResult)
	assert.Equal(t, nil, err)
	assert.Equal(t, jsonResult["test_field"], "test_value")
}

func TestComputeCID(t *testing.T) {
	address := "fetch19dq2mkcpp6x0aypxt9c9gz6n4fqvax0x9a7t5r"
	cid, err := ComputeCID(address)
	assert.Equal(t, nil, err)
	assert.Equal(t, "QmZ6ryKyS9rSnesX8YnFLAmFwFuRMdHpE7pQ2V6SjXTbqM", cid.String())
}

func TestWriteBytes(t *testing.T) {
	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()
	mockStream := mocks.NewMockStream(mockCtrl)
	mockStream.EXPECT().Write([]byte{0, 0, 0, 5, 104, 101, 108, 108, 111}).Return(9, nil).Times(1)
	err := WriteBytes(mockStream, []byte("hello"))
	assert.Equal(t, nil, err)

	mockStream.EXPECT().
		Write([]byte{0, 0, 0, 4, 104, 101, 108, 108}).
		Return(8, errors.New("oops")).
		Times(1)
	err = WriteBytes(mockStream, []byte("hell"))
	assert.NotEqual(t, err, nil)
}

func TestReadBytesConn(t *testing.T) {
	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()
	mockConn := mocks.NewMockConn(mockCtrl)
	mockConn.EXPECT().Read(gomock.Any()).Return(4, nil).Times(2)
	buf, err := ReadBytesConn(mockConn)
	assert.Equal(t, nil, err)
	assert.Equal(t, "", string(buf))
}

func TestWriteBytesConn(t *testing.T) {
	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()
	mockConn := mocks.NewMockConn(mockCtrl)
	mockConn.EXPECT().Write(gomock.Any()).Return(0, nil).Times(1)
	err := WriteBytesConn(mockConn, []byte("ABC"))
	assert.Equal(t, nil, err)
}

func TestReadWriteEnvelopeFromConnection(t *testing.T) {
	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()
	defer monkey.UnpatchAll()
	address := "0xb8d8c62d4a1999b7aea0aebBD5020244a4a9bAD8"
	buffer := bytes.NewBuffer([]byte{})
	mockConn := mocks.NewMockConn(mockCtrl)

	t.Run("TestWriteEnvelope", func(t *testing.T) {
		monkey.PatchInstanceMethod(
			reflect.TypeOf(mockConn),
			"Write",
			func(_ *mocks.MockConn, b []byte) (int, error) {
				buffer.Write(b)
				return 0, nil
			},
		)

		err := WriteEnvelopeConn(mockConn, &aea.Envelope{
			To:     address,
			Sender: address,
		})
		assert.Equal(t, nil, err)
		assert.NotEqual(t, 0, buffer)
	})

	t.Run("TestReadEnvelope", func(t *testing.T) {
		monkey.Patch(ReadBytesConn, func(conn net.Conn) ([]byte, error) {
			return buffer.Bytes()[4:], nil
		})
		env, err := ReadEnvelopeConn(mockConn)
		assert.Equal(t, nil, err)
		assert.Equal(t, address, env.To)
	})
}

func TestGetPeersAddrInfo(t *testing.T) {
	addrs, err := GetPeersAddrInfo(
		[]string{
			"/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW",
		},
	)
	assert.Equal(t, nil, err)
	assert.Equal(t, 1, len(addrs))
}

func TestFetchAIPublicKeyFromPubKey(t *testing.T) {
	//(publicKey crypto.PubKey) (string, error) {
	_, pubKey, err := KeyPairFromFetchAIKey(
		"3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc",
	)
	assert.Equal(t, nil, err)
	key, err := FetchAIPublicKeyFromPubKey(pubKey)
	assert.Equal(t, nil, err)
	assert.Equal(t, "03b7e977f498dce004e2614764ff576e17cc6691135497e7bcb5d3441e816ba9e1", key)
}

func TestIDFromFetchAIPublicKey(t *testing.T) {
	_, pubKey, err := KeyPairFromFetchAIKey(
		"3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc",
	)
	assert.Equal(t, nil, err)
	key, err := FetchAIPublicKeyFromPubKey(pubKey)
	assert.Equal(t, nil, err)
	peerID, err := IDFromFetchAIPublicKey(key)
	assert.Equal(t, nil, err)
	assert.NotEqual(t, 0, len(peerID))
}

func TestAgentAddressFromPublicKey(t *testing.T) {
	address, err := AgentAddressFromPublicKey(
		"fetchai",
		"3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc",
	)
	assert.Equal(t, nil, err)
	assert.NotEqual(t, 0, len(address))
}

func TestCosmosAddressFromPublicKey(t *testing.T) {
	address, err := CosmosAddressFromPublicKey(
		"3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc",
	)
	assert.Equal(t, nil, err)
	assert.NotEqual(t, 0, len(address))
}

func TestFetchAIPublicKeyFromFetchAIPrivateKey(t *testing.T) {
	key, err := FetchAIPublicKeyFromFetchAIPrivateKey(
		"3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc",
	)
	assert.Equal(t, nil, err)
	assert.Equal(t, "03b7e977f498dce004e2614764ff576e17cc6691135497e7bcb5d3441e816ba9e1", key)
}

func TestIDFromFetchAIPublicKeyUncompressed(t *testing.T) {
	//bad pub key
	_, err := IDFromFetchAIPublicKeyUncompressed("some")
	assert.NotEqual(t, nil, err)
	// good pub key
	id, err := IDFromFetchAIPublicKeyUncompressed(
		"50863AD64A87AE8A2FE83C1AF1A8403CB53F53E486D8511DAD8A04887E5B23522CD470243453A299FA9E77237716103ABC11A1DF38855ED6F2EE187E9C582BA6",
	)
	assert.Equal(t, nil, err)
	assert.Equal(
		t,
		peer.ID(
			"\x00%\b\x02\x12!\x02P\x86:\xd6J\x87\xae\x8a/\xe8<\x1a\xf1\xa8@<\xb5?S\xe4\x86\xd8Q\x1d\xad\x8a\x04\x88~[#R",
		),
		id,
	)
}

func TestSignFetchAI(t *testing.T) {
	privKey := "3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc"
	message := []byte("somebytes")

	_, pubKey, err := KeyPairFromFetchAIKey(privKey)
	assert.Equal(t, nil, err)
	fetchPubKey, err := FetchAIPublicKeyFromPubKey(pubKey)
	assert.Equal(t, nil, err)

	signature, err := SignFetchAI(message, privKey)
	assert.Equal(t, nil, err)
	assert.NotEqual(t, 0, len(signature))

	isValid, err := VerifyLedgerSignature("fetchai", message, signature, fetchPubKey)
	assert.Equal(t, nil, err)
	assert.Equal(t, true, isValid)

}

func TestBootstrapConnect(t *testing.T) {
	ctx := context.Background()
	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()
	defer monkey.UnpatchAll()
	var ipfsdht *kaddht.IpfsDHT
	var routingTable *kbucket.RoutingTable

	mockPeerstore := mocks.NewMockPeerstore(mockCtrl)
	peers := make([]peer.AddrInfo, 2)
	var addrs []multiaddr.Multiaddr
	peers[0] = peer.AddrInfo{ID: peer.ID("peer1"), Addrs: addrs}
	peers[1] = peer.AddrInfo{ID: peer.ID("peer2"), Addrs: addrs}

	mockHost := mocks.NewMockHost(mockCtrl)

	mockHost.EXPECT().ID().Return(peer.ID("host_id")).Times(2)
	mockHost.EXPECT().Peerstore().Return(mockPeerstore).Times(2)
	mockHost.EXPECT().Connect(gomock.Any(), gomock.Any()).Return(nil).Times(2)
	mockPeerstore.EXPECT().AddAddrs(gomock.Any(), gomock.Any(), gomock.Any()).Return().Times(2)

	t.Run("TestOk", func(t *testing.T) {
		monkey.PatchInstanceMethod(
			reflect.TypeOf(routingTable),
			"Find",
			func(_ *kbucket.RoutingTable, _ peer.ID) peer.ID {
				return peer.ID("som peer")
			},
		)
		monkey.PatchInstanceMethod(
			reflect.TypeOf(ipfsdht),
			"RoutingTable",
			func(_ *kaddht.IpfsDHT) *kbucket.RoutingTable {
				return routingTable
			},
		)

		err := BootstrapConnect(ctx, mockHost, ipfsdht, peers)
		assert.Equal(t, nil, err)
	})

	mockHost = mocks.NewMockHost(mockCtrl)

	mockHost.EXPECT().ID().Return(peer.ID("host_id")).Times(2)
	mockHost.EXPECT().Peerstore().Return(mockPeerstore).Times(2)
	mockHost.EXPECT().Connect(gomock.Any(), gomock.Any()).Return(nil).Times(2)
	mockPeerstore.EXPECT().AddAddrs(gomock.Any(), gomock.Any(), gomock.Any()).Return().Times(2)

	t.Run("Test_PeersNotAdded", func(t *testing.T) {
		monkey.PatchInstanceMethod(
			reflect.TypeOf(routingTable),
			"Find",
			func(_ *kbucket.RoutingTable, _ peer.ID) peer.ID {
				return peer.ID("")
			},
		)
		monkey.PatchInstanceMethod(
			reflect.TypeOf(ipfsdht),
			"RoutingTable",
			func(_ *kaddht.IpfsDHT) *kbucket.RoutingTable {
				return routingTable
			},
		)

		err := BootstrapConnect(ctx, mockHost, ipfsdht, peers)
		assert.NotEqual(t, nil, err)
		assert.Contains(t, err.Error(), "timeout: entry peer haven't been added to DHT")
	})

	mockHost = mocks.NewMockHost(mockCtrl)

	mockHost.EXPECT().ID().Return(peer.ID("host_id")).Times(2)
	mockHost.EXPECT().Peerstore().Return(mockPeerstore).Times(2)
	mockHost.EXPECT().Connect(gomock.Any(), gomock.Any()).Return(errors.New("some error")).Times(2)
	mockPeerstore.EXPECT().AddAddrs(gomock.Any(), gomock.Any(), gomock.Any()).Return().Times(2)

	t.Run("Test_PeersNotConnected", func(t *testing.T) {
		monkey.PatchInstanceMethod(
			reflect.TypeOf(routingTable),
			"Find",
			func(_ *kbucket.RoutingTable, _ peer.ID) peer.ID {
				return peer.ID("")
			},
		)
		monkey.PatchInstanceMethod(
			reflect.TypeOf(ipfsdht),
			"RoutingTable",
			func(_ *kaddht.IpfsDHT) *kbucket.RoutingTable {
				return routingTable
			},
		)

		err := BootstrapConnect(ctx, mockHost, ipfsdht, peers)
		assert.NotEqual(t, nil, err)
		assert.Equal(t, "failed to bootstrap: some error", err.Error())
	})

}

// test default features of Secp256k1 keys (cosmos, fetchai)
func TestP2pCryptoSecp256k1GenerateKeyFeatures(t *testing.T) {
	// testing key features

	bits := 1000000000000 // arbitrary

	// Secp256k1
	privKey, pubKey, err := p2pCrypto.GenerateKeyPair(2, bits)
	assert.Equal(t, nil, err)
	assert.Equal(t, "Secp256k1", privKey.Type().String())
	assert.Equal(t, "Secp256k1", pubKey.Type().String())

	privKeyBytes, err := privKey.Raw()
	assert.Equal(t, nil, err)
	assert.Equal(t, 32, len(privKeyBytes))
	pubKeyBytes, err := pubKey.Raw()
	assert.Equal(t, nil, err)
	assert.Equal(t, 33, len(pubKeyBytes))
	privKeyHex := hexutil.Encode(privKeyBytes)
	assert.Equal(t, 66, len(privKeyHex))
	pubKeyHex := hexutil.Encode(pubKeyBytes)
	assert.Equal(t, 68, len(pubKeyHex))
}

// type env_variables struct {
// 	ID          string // node_key.private_key
// 	ADDRESS     string // agent_key.address (== AEA_AGENT_ADDR and AEA_P2P_POR_ADDRESS)
// 	PUBKEY      string // agent_key.public_key
// 	PEER_PUBKEY string // node_key.public_key
// 	SIGNATURE   string
// 	LEDGER_ID   string
// }

// func newEnvVariables(
// 	id string,
// 	address string,
// 	pubkey string,
// 	peer_pubkey string,
// 	signature string,
// 	ledger_id string,
// ) *env_variables {
// 	variables := env_variables{id, address, pubkey, peer_pubkey, signature, ledger_id}
// 	return variables
// }
//
// // Define the environmental variables (example from temp_dir/.env_file.txt)
// const (
// 	FETCH_ENV_VARS = newEnvVariables( // pass tests
// 		"17d0eb590228d1418d0693bbbf41a3e1fd51b516b2fd37ed16301232c18b4e8e",
// 		"fetch16k3x9vw8jraxxddkhmz6rh3j74xjjrsdvcs2gz",
// 		"0296bd7ad062c2ca5a85ada147c7cb951cb0e1672778aa99abf0f641de578e0e65",
// 		"021aed1ce78a449109de6cc7ef516602a60d76e771b0cc2fef448b81d234d5b06b",
// 		"iUcIQWrj+9KACugzIRDlyRuoNL7UThexSOn/l8ukBn9jEs1w4HJCcdfbNLEjfUrwOkMK3tX+Yaw3q80UicaNAQ==",
// 		"fetchai",
// 	)
// 	ETH_ENV_VARS = newEnvVariables( // fail tests
// 		"0xeddbb87bd92c82f5e6700e8b9960a044a23cb2323ea4b827fa5927f0af03e564",
// 		"0x0B2F0C90222badbBC3C03b762FaB51c4192748F5",
// 		"0x03ec9f0a631d746b97c101bb442558ac9a57da7152a5761593a96046ef85f7c7e4577aa95ff47ede6eb74a1f13c4c74ec408a9e75ca5f548e5ada6f4f1adffc0",
// 		"0x5355ba6a065dfe10619f080894d66343b952ca6768988112afd5f2228fbf813d331097564d8fb5ec9e8dbd8ff0f8d2b72e02a61956d2f89a731af4626ec3753c",
// 		"0x8dd7a585dc4a9c7186dfe66b728f610f4aeb422a27e79ec2bc7b11cd4ea0fdaf0ea7bb8efa2bb8844bb38a38b2df6675c87bcb444525bec22f7f7f69530d92861b",
// 		"ethereum",
// 	)
// 	ETH_ENV_VARS = newEnvVariables( // mixed: pass tests
// 		"a369b5be68d3b5c166c782a50247a688f4018b06b6308f8cc72081840eaadcbc",
// 		"0x011a6845c7a09d5bF1316B783d9fB7C803bbfc8b",
// 		"0x7d8d0de693e1b80b78ff8e616ec47e8f70414ac3104cd85abab119d2da2877a5a6fff91081b49c3d2e7c094d91c161be5bef4989aad8ee692d98dc1d60f9e813",
// 		"035f0610ebb6be14c631c5463d095008a3e421474acc24b3d2cd4a9e7de01622f8",
// 		"0x46e8a9a7acd315482ba9e43d576c7596efca50a68c01ef3a528dd8b241c85a863ddf7e8df8de286b843bb0d8435eedb8857f2cb69cbd55a85ad7a497b639f81c1c",
// 		"ethereum",
// 	)
// )

// test default features of ECDSA keys (ethereum)
func TestP2pCryptoECDSAGenerateKeyFeatures(t *testing.T) {
	bits := 1000000000000 // arbitrary

	privKey, pubKey, err := p2pCrypto.GenerateKeyPair(3, bits)
	assert.Equal(t, nil, err)
	assert.Equal(t, "ECDSA", privKey.Type().String())
	assert.Equal(t, "ECDSA", pubKey.Type().String())

	privKeyBytes, err := privKey.Raw()
	assert.Equal(t, nil, err)
	assert.Equal(t, 121, len(privKeyBytes))
	pubKeyBytes, err := pubKey.Raw()
	assert.Equal(t, nil, err)
	assert.Equal(t, 91, len(pubKeyBytes))
	privKeyHex := hexutil.Encode(privKeyBytes)
	assert.Equal(t, 244, len(privKeyHex))
	pubKeyHex := hexutil.Encode(pubKeyBytes)
	assert.Equal(t, 184, len(pubKeyHex))
}

func TestFetchAIKeyType(t *testing.T) {
	privateKeyHex := "17d0eb590228d1418d0693bbbf41a3e1fd51b516b2fd37ed16301232c18b4e8e"
	expectedPublicKeyHex := "021aed1ce78a449109de6cc7ef516602a60d76e771b0cc2fef448b81d234d5b06b"
	// expectedAddress := "fetch16k3x9vw8jraxxddkhmz6rh3j74xjjrsdvcs2gz"
	privKey, pubKey, err := KeyPairFromFetchAIKey(privateKeyHex)
	assert.Equal(t, nil, err)
	assert.Equal(t, "Secp256k1", privKey.Type().String())
	assert.Equal(t, "Secp256k1", pubKey.Type().String())
	pubKeyBytes, err := pubKey.Raw()
	assert.Equal(t, nil, err)
	// don't use hexutil.Encode for non-ETH, it will prepend "0x"
	PublicKeyHex := hex.EncodeToString(pubKeyBytes)
	assert.Equal(t, expectedPublicKeyHex, PublicKeyHex)
	// TODO: get from public key to address
}

func TestEthereumKeyType(t *testing.T) {
	privateKeyHex := "0xeddbb87bd92c82f5e6700e8b9960a044a23cb2323ea4b827fa5927f0af03e564"
	expectedPublicKeyHex := "0x5355ba6a065dfe10619f080894d66343b952ca6768988112afd5f2228fbf813d331097564d8fb5ec9e8dbd8ff0f8d2b72e02a61956d2f89a731af4626ec3753c"
	_, pubKey, err := KeyPairFromEthereumKey(privateKeyHex)
	assert.Equal(t, nil, err)
	// pubKeyBytes, err := pubKey.Raw() // x509: unsupported elliptic curve
	// assert.Equal(t, nil, err)Z
	publicKey, err := p2pCrypto.PubKeyToStdKey(pubKey)
	assert.Equal(t, nil, err)
	publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	assert.Equal(t, true, ok)
	publicKeyBytes := ethCrypto.FromECDSAPub(publicKeyECDSA)
	publicKeyHex := hexutil.Encode(publicKeyBytes[1:]) // remove EC prefix "04"
	assert.Equal(t, expectedPublicKeyHex, publicKeyHex)
}

// func TestEthereumKeyType(t *testing.T) {
// 	privateKeyHex := "0xbb0c01836c9ddfc89a890d829dfaa569be545bac71cf20bbff8e02a114a2f042"
// 	privKey, pubKey, err := KeyPairFromEthereumKey(privateKeyHex)
// 	assert.Equal(t, nil, err)
// 	assert.Equal(t, "ECDSA", privKey.Type().String())
// 	assert.Equal(t, "ECDSA", pubKey.Type().String())
// }
