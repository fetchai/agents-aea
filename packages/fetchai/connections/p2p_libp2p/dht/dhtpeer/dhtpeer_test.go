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
	"net"
	"strconv"
	"testing"
	"time"

	"libp2p_node/aea"
	"libp2p_node/dht/dhtclient"
	"libp2p_node/utils"
)

/*
	DHTPeer and DHT network routing tests
*/

const (
	DefaultLocalHost    = "127.0.0.1"
	DefaultLocalPort    = 2000
	DefaultFetchAIKey   = "5071fbef50ed1fa1061d84dbf8152c7811f9a3a992ca6c43ae70b80c5ceb56df"
	DefaultAgentAddress = "2FRCqDBo7Yw3E2VJc1tAkggppWzLnCCYjPN9zHrQrj8Fupzmkr"
	DefaultDelegatePort = 3000

	EnvelopeDeliveryTimeout = 20 * time.Second
	DHTPeerSetupTimeout     = 5 * time.Second
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

	AgentsTestAddresses = []string{
		"PMRHuYJRhrbRHDagMMtkwfdFwJi7cbG9oxWkf9Au5zTi4kqng",
		"19SkNL4ozZbnL3xenQiCq8267KDmRpy1BTFtQoYRbVruXDamH",
		"2U1id59VqSx4cD6pxRDGnDQJA8UQj1r8X4iyti7k4F6u3Aayfb",
		"sgaaoJ3rW3g9vkvUdUMTqMW6ZTD3bdnr6Drg8Ro9FcenNo6RM",
		"2Rn9GTp5NHt8B8k4w5Ct44RrDKErRYsu5sgBrHAqBTkfCCKqLP",
		"2sTsbPFCxbfVUENtLt62bNjTYFPffdASbZAUGast4ZZUVdkN4r",
		"2EBBRDJWJ3NoRUJK1sjNh6gi3iRpMcUHqGU9JHiuuvVyuZyA4n",
		"fTFcTd8wJ4PmiffhTwFhP2J45A6V6XuMDWrA59hheHaWgdrPv",
		"roiuioMXPhu1PRFSYqpnMgvUrDCmRY3canmBQu16CTZozyQAc",
		"2LcDvsoiTmUPkFFdMTAGEUdZY7Y2xyYCQxEXvLD8MoMhTe4Ldi",
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
		IdentityFromFetchAIKey(DefaultFetchAIKey),
		RegisterAgentAddress(DefaultAgentAddress, func() bool { return true }),
		EnableRelayService(),
		EnableDelegateService(DefaultDelegatePort),
	}

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
		To: DefaultAgentAddress,
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup1()

	dhtPeer2, cleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{dhtPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup2()

	rxPeer1 := make(chan *aea.Envelope)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup()

	dhtPeer1, cleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup1()

	dhtPeer2, cleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestAddresses[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup2()

	rxPeer1 := make(chan *aea.Envelope)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup()

	entryPeer2, cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup()

	time.Sleep(1 * time.Second)
	dhtPeer1, cleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestAddresses[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{entryPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup1()

	dhtPeer2, cleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[3], AgentsTestAddresses[3], DefaultLocalPort+3, DefaultDelegatePort+3,
		[]string{entryPeer2.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer cleanup2()

	rxPeer1 := make(chan *aea.Envelope)
	dhtPeer1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan *aea.Envelope)
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
			FetchAITestKeys[i], AgentsTestAddresses[i],
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

		rx := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client, clientCleanup, err := SetupDHTClient(
		FetchAITestKeys[1], AgentsTestAddresses[1], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup()

	rxPeer := make(chan *aea.Envelope)
	peer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer <- envel
		return peer.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer entryPeerCleanup()

	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	time.Sleep(1 * time.Second)
	client, clientCleanup, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestAddresses[2], []string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup()

	rxPeer := make(chan *aea.Envelope)
	peer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer <- envel
		return peer.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client1, clientCleanup1, err := SetupDHTClient(
		FetchAITestKeys[1], AgentsTestAddresses[1], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestAddresses[2], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup2()

	rxClient1 := make(chan *aea.Envelope)
	client1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient1 <- envel
		return client1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient2 := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	client1, clientCleanup1, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestAddresses[2], []string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDHTClient(
		FetchAITestKeys[3], AgentsTestAddresses[3], []string{peer2.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer clientCleanup2()

	rxClient1 := make(chan *aea.Envelope)
	client1.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClient1 <- envel
		return client1.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	rxClient2 := make(chan *aea.Envelope)
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
func TestRoutingDelegateClientToDHTPeer(t *testing.T) {
	peer, peerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client, clientCleanup, err := SetupDelegateClient(AgentsTestAddresses[1], DefaultLocalHost, DefaultDelegatePort)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	time.Sleep(1 * time.Second)
	client, clientCleanup, err := SetupDelegateClient(AgentsTestAddresses[2], DefaultLocalHost, DefaultDelegatePort+1)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer1 := make(chan *aea.Envelope)
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

// TestRoutingDelegateClientToDHTPeerIndirectTwoHops
func TestRoutingDelegateClientToDHTPeerIndirectTwoHops(t *testing.T) {
	entryPeer, entryPeerCleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer entryPeerCleanup()

	peer1, peerCleanup1, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[2], AgentsTestAddresses[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{entryPeer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	time.Sleep(1 * time.Second)
	client, clientCleanup, err := SetupDelegateClient(AgentsTestAddresses[3], DefaultLocalHost, DefaultDelegatePort+2)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup()

	rxPeer1 := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	client1, clientCleanup1, err := SetupDelegateClient(AgentsTestAddresses[1], DefaultLocalHost, DefaultDelegatePort)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDelegateClient(AgentsTestAddresses[2], DefaultLocalHost, DefaultDelegatePort)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peer1Cleanup()

	peer2, peer2Cleanup, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peer2Cleanup()

	client1, clientCleanup1, err := SetupDelegateClient(AgentsTestAddresses[2], DefaultLocalHost, DefaultDelegatePort)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer clientCleanup1()

	client2, clientCleanup2, err := SetupDelegateClient(AgentsTestAddresses[3], DefaultLocalHost, DefaultDelegatePort+1)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup()

	dhtClient, dhtClientCleanup, err := SetupDHTClient(
		FetchAITestKeys[1], AgentsTestAddresses[1], []string{peer.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup()

	delegateClient, delegateClientCleanup, err := SetupDelegateClient(AgentsTestAddresses[2], DefaultLocalHost, DefaultDelegatePort)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup()

	rxClientDHT := make(chan *aea.Envelope)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup1()

	peer2, peerCleanup2, err := SetupLocalDHTPeer(
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer peerCleanup2()

	dhtClient, dhtClientCleanup, err := SetupDHTClient(
		FetchAITestKeys[2], AgentsTestAddresses[2], []string{peer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup()

	delegateClient, delegateClientCleanup, err := SetupDelegateClient(
		AgentsTestAddresses[3], DefaultLocalHost, DefaultDelegatePort+1,
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup()

	rxClientDHT := make(chan *aea.Envelope)
	dhtClient.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxClientDHT <- envel
		return dhtClient.RouteEnvelope(&aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
	})

	ensureAddressAnnounced(peer1, peer2)

	time.Sleep(1 * time.Second)
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
		FetchAITestKeys[0], AgentsTestAddresses[0], DefaultLocalPort, DefaultDelegatePort,
		[]string{},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup1()

	rxPeerDHT1 := make(chan *aea.Envelope)
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
		FetchAITestKeys[1], AgentsTestAddresses[1], DefaultLocalPort+1, DefaultDelegatePort+1,
		[]string{dhtPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup2()

	rxPeerDHT2 := make(chan *aea.Envelope)
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
		FetchAITestKeys[2], AgentsTestAddresses[2], DefaultLocalPort+2, DefaultDelegatePort+2,
		[]string{dhtPeer1.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup3()

	rxPeerDHT3 := make(chan *aea.Envelope)
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
		FetchAITestKeys[3], AgentsTestAddresses[3], DefaultLocalPort+3, DefaultDelegatePort+3,
		[]string{dhtPeer2.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTPeer:", err)
	}
	defer dhtPeerCleanup4()

	rxPeerDHT4 := make(chan *aea.Envelope)
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
		FetchAITestKeys[4], AgentsTestAddresses[4], []string{dhtPeer3.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup1()

	rxClientDHT1 := make(chan *aea.Envelope)
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
		FetchAITestKeys[5], AgentsTestAddresses[5], []string{dhtPeer3.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup2()

	rxClientDHT2 := make(chan *aea.Envelope)
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
		FetchAITestKeys[6], AgentsTestAddresses[6], []string{dhtPeer4.MultiAddr()},
	)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClientCleanup3()

	rxClientDHT3 := make(chan *aea.Envelope)
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
		AgentsTestAddresses[7], DefaultLocalHost, DefaultDelegatePort+2,
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup1()

	rxClientDelegate1 := make(chan *aea.Envelope)
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
		AgentsTestAddresses[8], DefaultLocalHost, DefaultDelegatePort+3,
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup2()

	rxClientDelegate2 := make(chan *aea.Envelope)
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
		AgentsTestAddresses[9], DefaultLocalHost, DefaultDelegatePort+3,
	)
	if err != nil {
		t.Fatal("Failed to initialize DelegateClient:", err)
	}
	defer delegateClientCleanup3()

	rxClientDelegate3 := make(chan *aea.Envelope)
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

func SetupLocalDHTPeer(key string, addr string, dhtPort uint16, delegatePort uint16, entry []string) (*DHTPeer, func(), error) {
	opts := []Option{
		LocalURI(DefaultLocalHost, dhtPort),
		PublicURI(DefaultLocalHost, dhtPort),
		IdentityFromFetchAIKey(key),
		EnableRelayService(),
		BootstrapFrom(entry),
		WithRegistrationDelay(5 * time.Second),
	}

	if addr != "" {
		opts = append(opts, RegisterAgentAddress(addr, func() bool { return true }))
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

func SetupDHTClient(key string, address string, entry []string) (*dhtclient.DHTClient, func(), error) {
	opts := []dhtclient.Option{
		dhtclient.IdentityFromFetchAIKey(key),
		dhtclient.RegisterAgentAddress(address, func() bool { return true }),
		dhtclient.BootstrapFrom(entry),
	}

	dhtClient, err := dhtclient.New(opts...)
	if err != nil {
		return nil, nil, err
	}

	return dhtClient, func() { dhtClient.Close() }, nil
}

// Delegate tcp client for tests only

type DelegateClient struct {
	AgentAddress    string
	Rx              chan *aea.Envelope
	Conn            net.Conn
	processEnvelope func(*aea.Envelope) error
}

func (client *DelegateClient) Close() error {
	return client.Conn.Close()
}

func (client *DelegateClient) Send(envel *aea.Envelope) error {
	return utils.WriteEnvelopeConn(client.Conn, envel)
}

func (client *DelegateClient) ProcessEnvelope(fn func(*aea.Envelope) error) {
	client.processEnvelope = fn
}

func SetupDelegateClient(address string, host string, port uint16) (*DelegateClient, func(), error) {
	var err error
	client := &DelegateClient{}
	client.AgentAddress = address
	client.Rx = make(chan *aea.Envelope)
	client.Conn, err = net.Dial("tcp", host+":"+strconv.FormatInt(int64(port), 10))
	if err != nil {
		return nil, nil, err
	}

	err = utils.WriteBytesConn(client.Conn, []byte(address))
	ignore(err)
	_, err = utils.ReadBytesConn(client.Conn)
	if err != nil {
		return nil, nil, err
	}

	go func() {
		for {
			envel, err := utils.ReadEnvelopeConn(client.Conn)
			if err != nil {
				break
			}
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

func ensureAddressAnnounced(peers ...*DHTPeer) {
	for _, peer := range peers {
		ctx, cancel := context.WithTimeout(context.Background(), DHTPeerSetupTimeout)
		defer cancel()
		for !peer.addressAnnounced {
			select {
			case <-ctx.Done():
				break
			case <-time.After(5 * time.Millisecond):
			}
		}
	}
}
