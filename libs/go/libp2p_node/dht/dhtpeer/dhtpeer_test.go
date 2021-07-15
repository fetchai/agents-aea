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

package dhtpeer

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/tls"
	"fmt"
	"log"
	"math/rand"
	"net"
	"os"
	"path"
	"strconv"
	"testing"
	"time"

	"libp2p_node/acn"
	"libp2p_node/aea"
	"libp2p_node/dht/dhtclient"
	"libp2p_node/dht/dhtnode"
	"libp2p_node/utils"

	"github.com/pkg/errors"
	"google.golang.org/protobuf/proto"
)

/*
	DHTPeer and DHT network routing tests
*/

const (
	DefaultLocalHost    = "127.0.0.1"
	DefaultLocalPort    = 2000
	DefaultDelegatePort = 3000

	EnvelopeDeliveryTimeout = 1 * time.Second
	DHTPeerSetupTimeout     = 5 * time.Second

	DefaultLedger = dhtnode.DefaultLedger
)

var (
	FetchAITestKeys = []string{
		"3e7a1f43b2d8a4b9f63a2ffeb1d597f971a8db7ffd95453173268b453106cadc",
		"92c36941ae78c1b93e5f4bebcf2b40be0af37573aa263ebb70b769ea235b88b6",
		"b6a8ff857c49b81895f18dd6dbd309e270906b75e2c290a721da48c5de4cba70",
		"91a90b5be4817c46e06f0e792dd9d9ef3ceb2dbb5ff5c45125153d289d515ce1",
		"5ee086c5c3df6f641e36e083769d6a03f918b33e4505b1102d2be7a75bb2ae0f",
		"6768d7918659c1699a379691381c19e55c3c13c49d30086e74a86524123659fb",
		"d31485403d0cce93b0c48a2fad2acae61a68396e93a602acfcd08dadd7ba12ae",
		"db533c3e74963a0571e962a4022a4ebce14ab5f240299b5350c83dd18549c1fd",
		"95aaa63bceeb0946c877c414e1f17119b8a975417924d83db8e281abd71820b2",
		"9427c1472b66f6abd94a6c246eee495e3709ec45882ae0badcbc71ad2cd8f8b2",
	}

	FetchAITestPublicKeys = []string{
		"03b7e977f498dce004e2614764ff576e17cc6691135497e7bcb5d3441e816ba9e1",
		"02344c3f0e79f56aef8e167a6fea912745f1f770b66b4c5096040c0e8c9e3c68b3",
		"023d6021c001c7b562af8b6e54ace4f98b1b14170d7db4749ecab2b1f0e4252794",
		"02a0eb20ae23f2f78650b42dfafa6bf4e4752657905da8598b2c0806478e0bfa0d",
		"023db373d1fc21212f2f03fec1ddd49f193f54f71545e72f37c8a70ca20ef1622b",
		"03290b4e5dabcca2a994a8d63057f5c83f60d999ede181a8d9b42084e3bee256c2",
		"03510651fbb9d2ce5b7ae00968339055fbc552e565c54cce8c69f5a52209d3d6a7",
		"02c11df29b5873e0c37d1427c488ba84e5ccc57405d39299757cee06893ab8595d",
		"031545edc0fe81a17c77a391a343f95547745b28703bbe664e12c523e3272b637e",
		"02dd78522785e4175e7db9794b03adcdcfaf707153f307caa3368da5a30594d369",
	}

	AgentsTestKeys = []string{
		"730c22474709a6d17cf11599a80413a84ddb691a3c7b11a6d8d47a2c024b7b56",
		"a085c5eeb39636a21c85a9bc667bae18bf3e327a220ecb3998e317b62ab20ec6",
		"0b7af750e7e96ceb9fe5582bdf9bdafae726427d34447f7245a084b6cf0aa5e5",
		"dffaa5a9779931a2c1194794e6e9a89787557d6cd708d84c74de20ec5e03a7bf",
		"509c4019dd96a337a36149031869e6de5db014ab9ae5d8097ac997ca8f10422a",
		"a385fa48b4f40a2f4ea66de88c0021532299865fe6137d765788f9f856e79453",
		"ff212371e454f8292fd3b13020a3910fc91002a7ab5eb3f297b71df6b7ff9bc1",
		"04289e97041fc025c103141909d2cce649944153822f032b646214a850363618",
		"116294510fba759d19af7a65b915467384258d997695ed7018d8c19d38c29412",
		"dc2f0238e65c0291bedae58cb1c013bd03e0f41f78e1779744ac401952ec2b51",
	}

	AgentsTestAddresses = []string{
		"fetch1y39e4tec9fll66x2k7wed5qn7zhaneayjm55kk",
		"fetch1ufjmhth6dnhrckxrvk05lmt8s2vture23xvwjl",
		"fetch1dja5uazc9n7jpjm94rhmkkmcyv5nj3kt8aexgf",
		"fetch18v5lz9psp53akm26ztk3exytqfdvpnfdsyx232",
		"fetch10u6ra4qmukhf57xadv64jt9jhr9gdrg707x6l9",
		"fetch1hys3k2anw5mxe0y2vksccpe58jyk5gksrsjd60",
		"fetch1t07jnjjtlqa07mstg4gw9twjs2ddtqs3sgtx7c",
		"fetch18sxxgat6uaxqxvd7mgt99y7avyy3c24av36u2l",
		"fetch1sx2rmtndc5t97pn00x76sksrzgc9s2watpgw64",
		"fetch1mwd8n27t68svv4w5urztgw7e3kjh7nqkqz0j94",
	}
)

/*
	DHT Network: DHTPeer-to-DHTPeer
*/

// TestRoutingDHTPeerToSelf dht peer with agent attached
func TestRoutingDHTPeerToSelf(t *testing.T) {
	opts := []Option{
		LocalURI(DefaultLocalHost, DefaultLocalPort),
		PublicURI(DefaultLocalHost, DefaultLocalPort),
		IdentityFromFetchAIKey(FetchAITestKeys[0]),
		EnableRelayService(),
		EnableDelegateService(DefaultDelegatePort),
		StoreRecordsTo(path.Join(os.TempDir(), "agents_records_"+randSeq(5))),
	}

	agentPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(AgentsTestKeys[0])
	if err != nil {
		t.Fatal("Failed at DHTPeer initialization:", err)
	}

	signature, err := utils.SignFetchAI([]byte(FetchAITestPublicKeys[0]), AgentsTestKeys[0])
	if err != nil {
		t.Fatal("Failed at DHTPeer initialization:", err)
	}

	record := &acn.AgentRecord{LedgerId: DefaultLedger}
	record.Address = AgentsTestAddresses[0]
	record.PublicKey = agentPubKey
	record.PeerPublicKey = FetchAITestPublicKeys[0]
	record.Signature = signature

	opts = append(opts, RegisterAgentAddress(record, func() bool { return true }))

	dhtPeer, err := New(opts...)
	if err != nil {
		t.Fatal("Failed at DHTPeer initialization:", err)
	}
	defer dhtPeer.Close()

	var rxEnvelopes []*aea.Envelope
	dhtPeer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxEnvelopes = append(rxEnvelopes, envel)
		return nil
	})

	err = dhtPeer.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[0],
		Sender: AgentsTestAddresses[0],
	})
	if err != nil {
		t.Error("Failed to Route envelope to local Agent")
	}

	if len(rxEnvelopes) == 0 {
		t.Error("Failed to Route & Process envelope to local Agent")
	}

}

// TestRoutingDHTPeerToDHTPeerDirect from a dht peer to its bootstrap peer
func TestRoutingDHTPeerToDHTPeerDirect(t *testing.T) {
	dhtPeer1, cleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup1()

	dhtPeer2, cleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{dhtPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup2()

	rxPeer1 := make(chan *aea.Envelope, 2)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan *aea.Envelope, 2)
	dhtPeer2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer2 <- envel
		return nil
	})

	ensureAddressAnnounced(dhtPeer1, dhtPeer2)

	err = dhtPeer2.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[0],
		Sender: AgentsTestAddresses[1],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer 2 to peer 1:", err)
	}

	expectEnvelope(t, rxPeer1)
	expectEnvelope(t, rxPeer2)
}

// TestRoutingDHTPeerToDHTPeerIndirect two dht peers connected to the same peer
func TestRoutingDHTPeerToDHTPeerIndirect(t *testing.T) {
	entryPeer, cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup()

	dhtPeer1, cleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup1()

	dhtPeer2, cleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestKeys[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup2()

	rxPeer1 := make(chan *aea.Envelope, 2)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan *aea.Envelope, 2)
	dhtPeer2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer2 <- envel
		return nil
	})

	ensureAddressAnnounced(dhtPeer1, dhtPeer2)

	err = dhtPeer2.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer 2 to peer 1:", err)
	}

	expectEnvelope(t, rxPeer1)
	expectEnvelope(t, rxPeer2)
}

// TestRoutingDHTPeerToDHTPeerIndirectTwoHops two dht peers connected to different peers
func TestRoutingDHTPeerToDHTPeerIndirectTwoHops(t *testing.T) {
	entryPeer1, cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], "", DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup()

	entryPeer2, cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup()

	time.Sleep(1 * time.Second)
	dhtPeer1, cleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestKeys[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{entryPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup1()

	dhtPeer2, cleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[3], AgentsTestKeys[3], DefaultLocalPort+3, DefaultDelegatePort+3,
		[]string{entryPeer2.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup2()

	rxPeer1 := make(chan *aea.Envelope, 2)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan *aea.Envelope, 2)
	dhtPeer2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer2 <- envel
		return nil
	})

	ensureAddressAnnounced(dhtPeer1, dhtPeer2)

	err = dhtPeer2.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[2],
		Sender: AgentsTestAddresses[3],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer 2 to peer 1:", err)
	}

	expectEnvelope(t, rxPeer1)
	expectEnvelope(t, rxPeer2)
}

// TestRoutingDHTPeerToDHTPeerFullConnectivity fully connected dht peers network
func TestRoutingDHTPeerToDHTPeerFullConnectivity(t *testing.T) {
	peers := []*DHTPeer{}
	rxs := []chan *aea.Envelope{}

	for i := range FetchAITestKeys {
		peer, cleanup, err := SetupLocalDHTPeer(
			FetchAITestKeys[i], AgentsTestKeys[i],
			DefaultLocalPort+uint16(i), DefaultDelegatePort+uint16(i),
			func() []string {
				multiaddrs := []string{}
				for _, entryPeer := range peers {
					multiaddrs = append(multiaddrs, entryPeer.MultiAddr())
				}
				return multiaddrs
			}(),
		)
		if err != nil {
			t.Fatal("Failed to initialize DHTPeer", i, ":", err)
		}

		rx := make(chan *aea.Envelope, 2)
		peer.ProcessEnvelope(func(envel *aea.Envelope) error {
			rx <- envel
			if string(envel.Message) == "ping" {
				err := peer.RouteEnvelope(&aea.Envelope{
					To:      envel.Sender,
					Sender:  envel.To,
					Message: []byte("ack"),
				})
				return err
			}
			return nil
		})

		peers = append(peers, peer)
		rxs = append(rxs, rx)
		defer cleanup()
	}

	ensureAddressAnnounced(peers...)

	for i := range peers {
		for j := range peers {
			from := len(peers) - 1 - i
			target := j

			// Should be able to route to self though
			if from == target {
				continue
			}

			err := peers[from].RouteEnvelope(&aea.Envelope{
				To:      AgentsTestAddresses[target],
				Sender:  AgentsTestAddresses[from],
				Message: []byte("ping"),
			})

			if err != nil {
				t.Error("Failed to RouteEnvelope from ", from, "to", target)
			}

			expectEnvelope(t, rxs[target])
			expectEnvelope(t, rxs[from])
		}
	}
}

/*
	DHT network: DHTClient
*/

// TestRoutingDHTClientToDHTPeer dht client to its bootstrap peer
func TestRoutingDHTClientToDHTPeerX(t *testing.T) {
	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client, clientCleanup, err := SetupDHTClient(
		FetchAITestKeys[1], AgentsTestKeys[1], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup()

	rxPeer := make(chan *aea.Envelope, 2)
	peer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer <- envel
		return peer.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient := make(chan *aea.Envelope, 2)
	client.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient <- envel
		return nil
	})

	time.Sleep(1 * time.Second)
	err = client.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[0],
		Sender: AgentsTestAddresses[1],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from DHTClient to DHTPeer:", err)
	}

	expectEnvelope(t, rxPeer)
	expectEnvelope(t, rxClient)

}

// TestRoutingDHTClientToDHTPeerIndirect dht client to dht peer different than its bootstrap one
func TestRoutingDHTClientToDHTPeerIndirect(t *testing.T) {
	entryPeer, entryPeerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer entryPeerCleanup()

	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	time.Sleep(1 * time.Second)
	client, clientCleanup, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestKeys[2], []string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup()

	rxPeer := make(chan *aea.Envelope, 2)
	peer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer <- envel
		return peer.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient := make(chan *aea.Envelope, 2)
	client.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient <- envel
		return nil
	})

	ensureAddressAnnounced(entryPeer, peer)

	time.Sleep(1 * time.Second)
	err = client.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from DHTClient to DHTPeer:", err)
	}

	expectEnvelope(t, rxPeer)
	expectEnvelope(t, rxClient)
}

// TestRoutingDHTClientToDHTClient dht client to dht client connected to the same peer
func TestRoutingDHTClientToDHTClient(t *testing.T) {
	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client1, clientCleanup1, err := SetupDHTClient(
		FetchAITestKeys[1], AgentsTestKeys[1], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestKeys[2], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup2()

	rxClient1 := make(chan *aea.Envelope, 2)
	client1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient1 <- envel
		return client1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient2 := make(chan *aea.Envelope, 2)
	client2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient2 <- envel
		return nil
	})

	time.Sleep(1 * time.Second)
	err = client2.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from DHTClient to DHTClient:", err)
	}

	expectEnvelope(t, rxClient1)
	expectEnvelope(t, rxClient2)

}

// TestRoutingDHTClientToDHTClientIndirect dht client to dht client connected to a different peer
func TestRoutingDHTClientToDHTClientIndirect(t *testing.T) {
	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], "", DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	client1, clientCleanup1, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestKeys[2], []string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDHTClient(
		FetchAITestKeys[3], AgentsTestKeys[3], []string{peer2.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup2()

	rxClient1 := make(chan *aea.Envelope, 2)
	client1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient1 <- envel
		return client1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient2 := make(chan *aea.Envelope, 2)
	client2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient2 <- envel
		return nil
	})

	ensureAddressAnnounced(peer1, peer2)

	time.Sleep(1 * time.Second)
	err = client2.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[2],
		Sender: AgentsTestAddresses[3],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from DHTClient to DHTClient:", err)
	}

	expectEnvelope(t, rxClient1)
	expectEnvelope(t, rxClient2)

}

/*
	DHT network: DelegateClient
*/

// TestRoutingDelegateClientToDHTPeer
func TestRoutingDelegateClientToDHTPeerX(t *testing.T) {
	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client, clientCleanup, err := SetupDelegateClient(
		AgentsTestKeys[1],
		DefaultLocalHost,
		DefaultDelegatePort,
		FetchAITestPublicKeys[0],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer := make(chan *aea.Envelope, 2)
	peer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer <- envel
		return nil
	})

	err = client.Send(&aea.Envelope{
		To:     AgentsTestAddresses[0],
		Sender: AgentsTestAddresses[1],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
	}

	expectEnvelope(t, rxPeer)

	err = peer.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[0],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer to delegate client:", err)
	}

	expectEnvelope(t, client.Rx)
}

// TestRoutingDelegateClientToDHTPeerIndirect
func TestRoutingDelegateClientToDHTPeerIndirect(t *testing.T) {
	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	time.Sleep(3 * time.Second)
	client, clientCleanup, err := SetupDelegateClient(
		AgentsTestKeys[2],
		DefaultLocalHost,
		DefaultDelegatePort+1,
		FetchAITestPublicKeys[1],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer1 := make(chan *aea.Envelope, 20)
	peer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		return nil
	})

	ensureAddressAnnounced(peer1, peer2)

	err = client.Send(&aea.Envelope{
		To:     AgentsTestAddresses[0],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
	}
	expectEnvelope(t, rxPeer1)

	err = peer1.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[2],
		Sender: AgentsTestAddresses[0],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer to delegate client:", err)
	}
	expectEnvelope(t, client.Rx)
}

// TestMessageOrderingWithDelegateClient
func TestMessageOrderingWithDelegateClient(t *testing.T) {
	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	time.Sleep(1 * time.Second)

	client, clientCleanup, err := SetupDelegateClient(
		AgentsTestKeys[2],
		DefaultLocalHost,
		DefaultDelegatePort+1,
		FetchAITestPublicKeys[1],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer1 := make(chan *aea.Envelope, 20)
	peer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		return nil
	})
	rxPeer2 := make(chan *aea.Envelope, 20)
	peer2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer2 <- envel
		return nil
	})

	ensureAddressAnnounced(peer1, peer2)

	max := 10
	i := 0
	for x := 0; x < max; x++ {
		envelope := &aea.Envelope{
			To:      AgentsTestAddresses[0],
			Sender:  AgentsTestAddresses[2],
			Message: []byte(strconv.Itoa(i)),
		}
		err = client.Send(envelope)
		if err != nil {
			t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
		}
		i++
		t.Log("Sending Envelope : ", envelope)
		// time.Sleep(100 * time.Millisecond)

		envelope1 := &aea.Envelope{
			To:      AgentsTestAddresses[1],
			Sender:  AgentsTestAddresses[2],
			Message: []byte(strconv.Itoa(i)),
		}
		err = client.Send(envelope1)
		if err != nil {
			t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
		}
		i++
		t.Log("Sending Envelope : ", envelope1)
		// time.Sleep(100 * time.Millisecond)
	}

	// go func() {
	ii := 0
	for x := 0; x < max; x++ {
		expectEnvelopeOrdered(t, rxPeer1, ii)
		ii++
		ii++
	}
	// }()

	// go func() {
	iii := 0
	for x := 0; x < max; x++ {
		iii++
		expectEnvelopeOrdered(t, rxPeer2, iii)
		iii++
	}
	// }()

}

// TestMessageOrderingWithDelegateClientTwoHops
func TestMessageOrderingWithDelegateClientTwoHops(t *testing.T) {
	peer1Index := 0
	peer2Index := 1
	client1Index := 2
	client2Index := 3
	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[peer1Index],
		AgentsTestKeys[peer1Index],
		DefaultLocalPort,
		DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[peer2Index],
		AgentsTestKeys[peer2Index],
		DefaultLocalPort+1,
		DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	time.Sleep(1 * time.Second)

	client1, clientCleanup1, err := SetupDelegateClient(
		AgentsTestKeys[client1Index],
		DefaultLocalHost,
		DefaultDelegatePort,
		FetchAITestPublicKeys[peer1Index],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDelegateClient(
		AgentsTestKeys[client2Index],
		DefaultLocalHost,
		DefaultDelegatePort+1,
		FetchAITestPublicKeys[peer2Index],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup2()

	rxClient1 := make(chan *aea.Envelope, 20)
	client1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient1 <- envel
		return nil
	})
	rxClient2 := make(chan *aea.Envelope, 20)
	client2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient2 <- envel
		return nil
	})

	ensureAddressAnnounced(peer1, peer2)

	max := 100
	i := 0
	for x := 0; x < max; x++ {
		envelope := &aea.Envelope{
			To:      AgentsTestAddresses[client2Index],
			Sender:  AgentsTestAddresses[client1Index],
			Message: []byte(strconv.Itoa(i)),
		}
		err = client1.Send(envelope)
		if err != nil {
			t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
		}
		i++
		t.Log("Sending Envelope : ", envelope)
		// time.Sleep(100 * time.Millisecond)

		envelope1 := &aea.Envelope{
			To:      AgentsTestAddresses[client1Index],
			Sender:  AgentsTestAddresses[client2Index],
			Message: []byte(strconv.Itoa(i)),
		}
		err = client2.Send(envelope1)
		if err != nil {
			t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
		}
		i++
		t.Log("Sending Envelope : ", envelope1)
		// time.Sleep(100 * time.Millisecond)
	}

	// go func() {
	ii := 0
	for x := 0; x < max; x++ {
		expectEnvelopeOrdered(t, rxClient2, ii)
		ii++
		ii++
	}
	// }()

	// go func() {
	iii := 0
	for x := 0; x < max; x++ {
		iii++
		expectEnvelopeOrdered(t, rxClient1, iii)
		iii++
	}
	// }()

}

// TestRoutingDelegateClientToDHTPeerIndirectTwoHops
func TestRoutingDelegateClientToDHTPeerIndirectTwoHops(t *testing.T) {
	entryPeer, entryPeerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer entryPeerCleanup()

	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestKeys[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	time.Sleep(1 * time.Second)
	client, clientCleanup, err := SetupDelegateClient(
		AgentsTestKeys[3],
		DefaultLocalHost,
		DefaultDelegatePort+2,
		FetchAITestPublicKeys[2],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer1 := make(chan *aea.Envelope, 2)
	peer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		return nil
	})

	ensureAddressAnnounced(entryPeer, peer1, peer2)

	err = client.Send(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[3],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DHTPeer:", err)
	}

	expectEnvelope(t, rxPeer1)

	err = peer1.RouteEnvelope(&aea.Envelope{
		To:     AgentsTestAddresses[3],
		Sender: AgentsTestAddresses[1],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer to delegate client:", err)
	}

	expectEnvelope(t, client.Rx)
}

// TestRoutingDelegateClientToDelegateClient
func TestRoutingDelegateClientToDelegateClient(t *testing.T) {
	_, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client1, clientCleanup1, err := SetupDelegateClient(
		AgentsTestKeys[1],
		DefaultLocalHost,
		DefaultDelegatePort,
		FetchAITestPublicKeys[0],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDelegateClient(
		AgentsTestKeys[2],
		DefaultLocalHost,
		DefaultDelegatePort,
		FetchAITestPublicKeys[0],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup2()

	time.Sleep(1 * time.Second)
	err = client1.Send(&aea.Envelope{
		To:     AgentsTestAddresses[2],
		Sender: AgentsTestAddresses[1],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DelegateClient:", err)
	}

	expectEnvelope(t, client2.Rx)

	err = client2.Send(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DelegateClient:", err)
	}

	expectEnvelope(t, client1.Rx)
}

// TestRoutingDelegateClientToDelegateClientIndirect
func TestRoutingDelegateClientToDelegateClientIndirect(t *testing.T) {
	peer1, peer1Cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], "", DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peer1Cleanup()

	peer2, peer2Cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peer2Cleanup()

	client1, clientCleanup1, err := SetupDelegateClient(
		AgentsTestKeys[2],
		DefaultLocalHost,
		DefaultDelegatePort,
		FetchAITestPublicKeys[0],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDelegateClient(
		AgentsTestKeys[3],
		DefaultLocalHost,
		DefaultDelegatePort+1,
		FetchAITestPublicKeys[1],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup2()

	ensureAddressAnnounced(peer1, peer2)

	err = client1.Send(&aea.Envelope{
		To:     AgentsTestAddresses[3],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DelegateClient:", err)
	}

	expectEnvelope(t, client2.Rx)

	err = client2.Send(&aea.Envelope{
		To:     AgentsTestAddresses[2],
		Sender: AgentsTestAddresses[3],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DelegateClient:", err)
	}

	expectEnvelope(t, client1.Rx)
}

// TestRoutingDelegateClientToDHTClientDirect
func TestRoutingDelegateClientToDHTClientDirect(t *testing.T) {
	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], "", DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	dhtClient, dhtClientCleanup, err := SetupDHTClient(
		FetchAITestKeys[1], AgentsTestKeys[1], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup()

	delegateClient, delegateClientCleanup, err := SetupDelegateClient(
		AgentsTestKeys[2],
		DefaultLocalHost,
		DefaultDelegatePort,
		FetchAITestPublicKeys[0],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup()

	rxClientDHT := make(chan *aea.Envelope, 2)
	dhtClient.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDHT <- envel
		return dhtClient.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	time.Sleep(1 * time.Second)
	err = delegateClient.Send(&aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DHTClient:", err)
	}

	expectEnvelope(t, rxClientDHT)
	expectEnvelope(t, delegateClient.Rx)
}

// TestRoutingDelegateClientToDHTClientIndirect
func TestRoutingDelegateClientToDHTClientIndirect(t *testing.T) {
	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	dhtClient, dhtClientCleanup, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestKeys[2], []string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup()

	delegateClient, delegateClientCleanup, err := SetupDelegateClient(
		AgentsTestKeys[3], DefaultLocalHost, DefaultDelegatePort+1, FetchAITestPublicKeys[1],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup()

	rxClientDHT := make(chan *aea.Envelope, 2)
	dhtClient.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDHT <- envel
		return dhtClient.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	ensureAddressAnnounced(peer1, peer2)

	time.Sleep(3 * time.Second)

	err = delegateClient.Send(&aea.Envelope{
		To:     AgentsTestAddresses[2],
		Sender: AgentsTestAddresses[3],
	})
	if err != nil {
		t.Error("Failed to Send envelope from DelegateClient to DHTClient:", err)
	}

	expectEnvelope(t, rxClientDHT)
	expectEnvelope(t, delegateClient.Rx)
}

/*
	DHT network: all-to-all
*/

/*
                                    Network topology

   DHTClient -------                                                 -- DelegateClient
                   |                                                 |
   DHTClient -------                                                 -- DelegateClient
                   |                                                 |
                   |-- DHTPeer --- DHTPeeer -- DHTPeer --- DHTPeer --|
                   |                                                 |
   DelegateClient --                                                 ------- DHTClient
*/

// TestRoutingAlltoAll
func TestRoutingAllToAll(t *testing.T) {
	rxs := []chan *aea.Envelope{}
	send := []func(*aea.Envelope) error{}

	// setup DHTPeers

	dhtPeer1, dhtPeerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestKeys[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup1()

	rxPeerDHT1 := make(chan *aea.Envelope, 100)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeerDHT1 <- envel
		if string(envel.Message) == "ping" {
			err := dhtPeer1.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxPeerDHT1)
	send = append(send, func(envel *aea.Envelope) error {
		return dhtPeer1.RouteEnvelope(envel)
	})

	dhtPeer2, dhtPeerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{dhtPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup2()

	rxPeerDHT2 := make(chan *aea.Envelope, 100)
	dhtPeer2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeerDHT2 <- envel
		if string(envel.Message) == "ping" {
			err := dhtPeer2.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxPeerDHT2)

	send = append(send, func(envel *aea.Envelope) error {
		return dhtPeer2.RouteEnvelope(envel)
	})

	dhtPeer3, dhtPeerCleanup3, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestKeys[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{dhtPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup3()

	rxPeerDHT3 := make(chan *aea.Envelope, 100)
	dhtPeer3.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeerDHT3 <- envel
		if string(envel.Message) == "ping" {
			err := dhtPeer3.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxPeerDHT3)
	send = append(send, func(envel *aea.Envelope) error {
		return dhtPeer3.RouteEnvelope(envel)
	})

	dhtPeer4, dhtPeerCleanup4, err := SetupLocalDHTPeer(
		FetchAITestKeys[3], AgentsTestKeys[3], DefaultLocalPort+3, DefaultDelegatePort+3,
		[]string{dhtPeer2.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup4()

	rxPeerDHT4 := make(chan *aea.Envelope, 100)
	dhtPeer4.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeerDHT4 <- envel
		if string(envel.Message) == "ping" {
			err := dhtPeer4.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxPeerDHT4)
	send = append(send, func(envel *aea.Envelope) error {
		return dhtPeer4.RouteEnvelope(envel)
	})

	// setup DHTClients

	dhtClient1, dhtClientCleanup1, err := SetupDHTClient(
		FetchAITestKeys[4], AgentsTestKeys[4], []string{dhtPeer3.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup1()

	rxClientDHT1 := make(chan *aea.Envelope, 100)
	dhtClient1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDHT1 <- envel
		if string(envel.Message) == "ping" {
			err := dhtClient1.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxClientDHT1)
	send = append(send, func(envel *aea.Envelope) error {
		return dhtClient1.RouteEnvelope(envel)
	})

	dhtClient2, dhtClientCleanup2, err := SetupDHTClient(
		FetchAITestKeys[5], AgentsTestKeys[5], []string{dhtPeer3.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup2()

	rxClientDHT2 := make(chan *aea.Envelope, 100)
	dhtClient2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDHT2 <- envel
		if string(envel.Message) == "ping" {
			err := dhtClient2.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxClientDHT2)
	send = append(send, func(envel *aea.Envelope) error {
		return dhtClient2.RouteEnvelope(envel)
	})

	dhtClient3, dhtClientCleanup3, err := SetupDHTClient(
		FetchAITestKeys[6], AgentsTestKeys[6], []string{dhtPeer4.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup3()

	rxClientDHT3 := make(chan *aea.Envelope, 100)
	dhtClient3.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDHT3 <- envel
		if string(envel.Message) == "ping" {
			err := dhtClient3.RouteEnvelope(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxClientDHT3)
	send = append(send, func(envel *aea.Envelope) error {
		return dhtClient3.RouteEnvelope(envel)
	})

	// setup DelegateClients

	delegateClient1, delegateClientCleanup1, err := SetupDelegateClient(
		AgentsTestKeys[7], DefaultLocalHost, DefaultDelegatePort+2, FetchAITestPublicKeys[2],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup1()

	rxClientDelegate1 := make(chan *aea.Envelope, 100)
	delegateClient1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDelegate1 <- envel
		if string(envel.Message) == "ping" {
			err := delegateClient1.Send(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxClientDelegate1)
	send = append(send, func(envel *aea.Envelope) error {
		return delegateClient1.Send(envel)
	})

	delegateClient2, delegateClientCleanup2, err := SetupDelegateClient(
		AgentsTestKeys[8], DefaultLocalHost, DefaultDelegatePort+3, FetchAITestPublicKeys[3],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup2()

	rxClientDelegate2 := make(chan *aea.Envelope, 100)
	delegateClient2.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDelegate2 <- envel
		if string(envel.Message) == "ping" {
			err := delegateClient2.Send(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxClientDelegate2)
	send = append(send, func(envel *aea.Envelope) error {
		return delegateClient2.Send(envel)
	})

	delegateClient3, delegateClientCleanup3, err := SetupDelegateClient(
		AgentsTestKeys[9], DefaultLocalHost, DefaultDelegatePort+3, FetchAITestPublicKeys[3],
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup3()

	rxClientDelegate3 := make(chan *aea.Envelope, 100)
	delegateClient3.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDelegate3 <- envel
		if string(envel.Message) == "ping" {
			err := delegateClient3.Send(&aea.Envelope{
				To:      envel.Sender,
				Sender:  envel.To,
				Message: []byte("ack"),
			})
			return err
		}
		return nil
	})

	rxs = append(rxs, rxClientDelegate3)
	send = append(send, func(envel *aea.Envelope) error {
		return delegateClient3.Send(envel)
	})

	// Send envelope from everyone to everyone else and expect an echo back

	ensureAddressAnnounced(dhtPeer1, dhtPeer2, dhtPeer3, dhtPeer4)

	for i := range AgentsTestAddresses {
		for j := range AgentsTestAddresses {
			from := len(AgentsTestAddresses) - 1 - i
			target := j

			// Should be able to route to self though
			if from == target {
				continue
			}

			err := send[from](&aea.Envelope{
				To:      AgentsTestAddresses[target],
				Sender:  AgentsTestAddresses[from],
				Message: []byte("ping"),
			})

			if err != nil {
				t.Error("Failed to RouteEnvelope from ", from, "to", target)
			}
		}
	}
	for i := range AgentsTestAddresses {
		for j := range AgentsTestAddresses {
			from := len(AgentsTestAddresses) - 1 - i
			target := j
			if from == target {
				continue
			}
			expectEnvelope(t, rxs[target])
			expectEnvelope(t, rxs[from])
		}
	}

}

/*
	Helpers
	TOFIX(LR) how to share test helpers between packages tests
	 without having circular dependencies
*/

func randSeq(n int) string {
	rand.Seed(time.Now().UnixNano())
	var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
	b := make([]rune, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}

func SetupLocalDHTPeer(
	key string,
	agentKey string,
	dhtPort uint16,
	delegatePort uint16,
	entry []string,
) (*DHTPeer, func(), error) {
	opts := []Option{
		LocalURI(DefaultLocalHost, dhtPort),
		PublicURI(DefaultLocalHost, dhtPort),
		IdentityFromFetchAIKey(key),
		EnableRelayService(),
		BootstrapFrom(entry),
		StoreRecordsTo(path.Join(os.TempDir(), "agents_records_"+randSeq(5))),
	}

	if agentKey != "" {
		agentPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(agentKey)
		if err != nil {
			return nil, nil, err
		}

		agentAddress, err := utils.FetchAIAddressFromPublicKey(agentPubKey)
		if err != nil {
			return nil, nil, err
		}

		peerPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(key)
		if err != nil {
			return nil, nil, err
		}

		signature, err := utils.SignFetchAI([]byte(peerPubKey), agentKey)
		if err != nil {
			return nil, nil, err
		}

		record := &acn.AgentRecord{LedgerId: DefaultLedger}
		record.Address = agentAddress
		record.PublicKey = agentPubKey
		record.PeerPublicKey = peerPubKey
		record.Signature = signature

		opts = append(opts, RegisterAgentAddress(record, func() bool { return true }))
	}

	if delegatePort != 0 {
		opts = append(opts, EnableDelegateService(delegatePort))
	}

	dhtPeer, err := New(opts...)
	if err != nil {
		return nil, nil, err
	}

	return dhtPeer, func() { dhtPeer.Close() }, nil

}

// DHTClient

func SetupDHTClient(
	key string,
	agentKey string,
	entry []string,
) (*dhtclient.DHTClient, func(), error) {

	agentPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(agentKey)
	if err != nil {
		return nil, nil, err
	}

	agentAddress, err := utils.FetchAIAddressFromPublicKey(agentPubKey)
	if err != nil {
		return nil, nil, err
	}

	peerPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(key)
	if err != nil {
		return nil, nil, err
	}

	signature, err := utils.SignFetchAI([]byte(peerPubKey), agentKey)
	if err != nil {
		return nil, nil, err
	}

	record := &acn.AgentRecord{LedgerId: DefaultLedger}
	record.Address = agentAddress
	record.PublicKey = agentPubKey
	record.PeerPublicKey = peerPubKey
	record.Signature = signature

	opts := []dhtclient.Option{
		dhtclient.IdentityFromFetchAIKey(key),
		dhtclient.RegisterAgentAddress(record, func() bool { return true }),
		dhtclient.BootstrapFrom(entry),
	}

	dhtClient, err := dhtclient.New(opts...)
	if err != nil {
		println("dhtclient.New:", err.Error())
		return nil, nil, err
	}

	return dhtClient, func() { dhtClient.Close() }, nil
}

// Delegate tcp client for tests only

type DelegateClient struct {
	AgentAddress    string
	AgentKey        string
	AgentPubKey     string
	PeerPubKey      string
	PoR             string
	Rx              chan *aea.Envelope
	Conn            net.Conn
	processEnvelope func(*aea.Envelope) error
	acn_status_chan chan *acn.StatusBody
}

func (client *DelegateClient) AddAcnStatusMessage(status *acn.StatusBody, counterpartyID string) {
	//client.acn_status_chan <- status
}

func (client *DelegateClient) Close() error {
	return client.Conn.Close()
}

func (client *DelegateClient) Send(envelope *aea.Envelope) error {
	data, err := aea.MakeAcnMessageFromEnvelope(envelope)
	if err != nil {
		println("while serializing envelope:", err.Error())
		return err
	}
	err = utils.WriteBytesConn(client.Conn, data)
	if err != nil {
		println("while sending envelope:", err.Error())
		return err
	}
	return err
}

func (client *DelegateClient) ProcessEnvelope(fn func(*aea.Envelope) error) {
	client.processEnvelope = fn
}

func ValidateTLSSignature(
	tlsSignature []byte,
	sessionPubKey *ecdsa.PublicKey,
	peerPubKey string,
) error {
	sessionPubKeyBytes := elliptic.Marshal(sessionPubKey.Curve, sessionPubKey.X, sessionPubKey.Y)
	verifyKey, err := utils.PubKeyFromFetchAIPublicKey(peerPubKey)
	if err != nil {
		return err
	}
	ok, err := verifyKey.Verify(sessionPubKeyBytes, tlsSignature)

	if err != nil {
		return err
	}
	if !ok {
		return errors.New("error on signature validation for tls start")
	}
	return nil
}

func SetupDelegateClient(
	key string,
	host string,
	port uint16,
	peerPubKey string,
) (*DelegateClient, func(), error) {
	var err error
	client := &DelegateClient{}
	client.AgentKey = key

	client.acn_status_chan = make(chan *acn.StatusBody, 10000)

	pubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(key)
	if err != nil {
		return nil, nil, err
	}
	client.AgentPubKey = pubKey

	address, err := utils.FetchAIAddressFromPublicKey(pubKey)
	if err != nil {
		return nil, nil, err
	}
	client.AgentAddress = address

	signature, err := utils.SignFetchAI([]byte(peerPubKey), key)
	if err != nil {
		return nil, nil, err
	}
	client.PoR = signature

	client.Rx = make(chan *aea.Envelope, 2)
	conf := &tls.Config{
		InsecureSkipVerify: true,
	}
	client.Conn, err = tls.Dial("tcp", host+":"+strconv.FormatInt(int64(port), 10), conf)

	if err != nil {
		return nil, nil, err
	}

	certPubKey := client.Conn.(*tls.Conn).ConnectionState().PeerCertificates[0].PublicKey.(*ecdsa.PublicKey)

	tlsSignature, _ := utils.ReadBytesConn(client.Conn)
	err = ValidateTLSSignature(tlsSignature, certPubKey, peerPubKey)
	if err != nil {
		return nil, nil, err
	}

	record := &acn.AgentRecord{LedgerId: DefaultLedger}
	record.Address = address
	record.PublicKey = pubKey
	record.PeerPublicKey = peerPubKey
	record.Signature = signature
	registration := &acn.RegisterPerformative{Record: record}
	msg := &acn.AcnMessage{
		Performative: &acn.Register{Register: registration},
	}
	data, err := proto.Marshal(msg)
	ignore(err)
	err = utils.WriteBytesConn(client.Conn, data)
	ignore(err)
	data, err = utils.ReadBytesConn(client.Conn)
	if err != nil {
		return nil, nil, err
	}
	response := &acn.AcnMessage{}
	err = proto.Unmarshal(data, response)
	if err != nil {
		return nil, nil, err
	}

	// Get Status message
	var status *acn.StatusPerformative
	switch pl := response.Performative.(type) {
	case *acn.Status:
		status = pl.Status
	default:
		return nil, nil, err
	}

	if status.Body.Code != acn.SUCCESS {
		println("Registration error:", status.Body.String())
		return nil, nil, errors.New(status.Body.String())
	}

	pipe := utils.ConnPipe{Conn: client.Conn}
	go func() {
		for {
			envel, err := aea.HandleAcnMessageFromPipe(pipe, client, "")
			if err != nil {
				break
			}
			if envel == nil {
				continue
			}
			_ = acn.SendAcnSuccess(pipe)

			if client.processEnvelope != nil {
				err = client.processEnvelope(envel)
				ignore(err)
			} else {
				client.Rx <- envel
			}
		}
	}()

	return client, func() { client.Close() }, nil
}

func expectEnvelope(t *testing.T, rx chan *aea.Envelope) {
	timeout := time.After(EnvelopeDeliveryTimeout)
	select {
	case envel := <-rx:
		t.Log("Received envelope", envel)
	case <-timeout:
		t.Error("Failed to receive envelope before timeout")
	}
}

func expectEnvelopeOrdered(t *testing.T, rx chan *aea.Envelope, counter int) {
	timeout := time.After(EnvelopeDeliveryTimeout)
	select {
	case envel := <-rx:
		t.Log("Received envelope", envel)
		if envel == nil {
			t.Log("Empty envelope. exit")
			return
		}
		message, _ := strconv.Atoi(string(envel.Message))
		if message != counter {
			log.Fatal(fmt.Sprintf("Expected counter %d received counter %d", counter, message))
		}
	case <-timeout:
		t.Error("Failed to receive envelope before timeout")
	}
}

func ensureAddressAnnounced(peers ...*DHTPeer) {
	for _, peer := range peers {
		ctx, cancel := context.WithTimeout(context.Background(), DHTPeerSetupTimeout)
		defer cancel()
	L:
		for !peer.IsAddressAnnounced(peer.myAgentAddress) {
			select {
			case <-ctx.Done():
				break L
			case <-time.After(5 * time.Millisecond):
			}
		}
	}
}

func TestFetchAICrypto(t *testing.T) {
	publicKey := "02358e3e42a6ba15cf6b2ba6eb05f02b8893acf82b316d7dd9cda702b0892b8c71"
	address := "fetch19dq2mkcpp6x0aypxt9c9gz6n4fqvax0x9a7t5r"
	peerPublicKey := "027af21aff853b9d9589867ea142b0a60a9611fc8e1fae04c2f7144113fa4e938e"
	pySigStrCanonize := "N/GOa7/m3HU8/gpLJ88VCQ6vXsdrfiiYcqnNtF+c2N9VG9ZIiycykN4hdbpbOCGrChMYZQA3G1GpozsShrUBgg=="

	addressFromPublicKey, _ := utils.FetchAIAddressFromPublicKey(publicKey)
	if address != addressFromPublicKey {
		t.Error("[ERR] Addresses don't match")
	} else {
		t.Log("[OK] Agent address matches its public key")
	}

	valid, err := utils.VerifyFetchAISignatureBTC(
		[]byte(peerPublicKey),
		pySigStrCanonize,
		publicKey,
	)
	if !valid {
		t.Errorf("Signature using BTC don't match %s", err.Error())
	}
	valid, err = utils.VerifyFetchAISignatureLibp2p(
		[]byte(peerPublicKey),
		pySigStrCanonize,
		publicKey,
	)
	if !valid {
		t.Errorf("Signature using LPP don't match %s", err.Error())
	}
}

func TestEthereumCrypto(t *testing.T) {
	//privateKey := "0xb60fe8027fb82f1a1bd6b8e66d4400f858989a2c67428a4e7f589441700339b0"
	publicKey := "0xf753e5a9e2368e97f4db869a0d956d3ffb64672d6392670572906c786b5712ada13b6bff882951b3ba3dd65bdacc915c2b532efc3f183aa44657205c6c337225"
	address := "0xb8d8c62d4a1999b7aea0aebBD5020244a4a9bAD8"
	publicKeySignature := "0x304c2ba4ae7fa71295bfc2920b9c1268d574d65531f1f4d2117fc1439a45310c37ab75085a9df2a4169a4d47982b330a4387b1ded0c8881b030629db30bbaf3a1c"

	addFromPublicKey, err := utils.EthereumAddressFromPublicKey(publicKey)
	if err != nil || addFromPublicKey != address {
		t.Error(
			"Error when computing address from public key or address and public key don't match",
		)
	}

	_, err = utils.BTCPubKeyFromEthereumPublicKey(publicKey)
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

	valid, err := utils.VerifyEthereumSignatureETH([]byte(publicKey), publicKeySignature, publicKey)
	if err != nil {
		t.Error(err.Error())
	}

	if !valid {
		t.Errorf("Signer address don't match %s", addFromPublicKey)
	}
}

// Perform tests for tls signature generation and checking
func TestTLSSignatureValidation(t *testing.T) {
	key1, pubKey, _ := utils.KeyPairFromFetchAIKey(FetchAITestKeys[0])
	key2, _, _ := utils.KeyPairFromFetchAIKey(FetchAITestKeys[1])
	peerPubKey, _ := utils.FetchAIPublicKeyFromPubKey(pubKey)

	cert, err := generate_x509_cert()
	sessionPubKey := cert.PrivateKey.(*ecdsa.PrivateKey).Public().(*ecdsa.PublicKey)

	if err != nil {
		t.Fatal("Failed to generate certificate")
	}

	// valid
	tlsSignature, err := makeSessionKeySignature(cert, key1)
	if err != nil {
		t.Fatal("Failed to make signature")
	}
	err = ValidateTLSSignature(tlsSignature, sessionPubKey, peerPubKey)
	if err != nil {
		t.Fatal("Signature is invalid, but expected to be ok")
	}

	//invalid
	tlsSignature, err = makeSessionKeySignature(cert, key2)
	if err != nil {
		t.Fatal("Failed to make signature")
	}
	err = ValidateTLSSignature(tlsSignature, sessionPubKey, peerPubKey)
	if err == nil {
		t.Fatal("Signature is valid, but shoud not")
	}
}
