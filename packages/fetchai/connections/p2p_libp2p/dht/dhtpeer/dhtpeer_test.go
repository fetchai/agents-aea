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
	"testing"
	"time"

	"libp2p_node/aea"
)

// TOFIX(LR) how to share test helpers between packages tests without having circular dependencies

const (
	DefaultLocalHost    = "127.0.0.1"
	DefaultLocalPort    = 2000
	DefaultFetchAIKey   = "5071fbef50ed1fa1061d84dbf8152c7811f9a3a992ca6c43ae70b80c5ceb56df"
	DefaultAgentAddress = "2FRCqDBo7Yw3E2VJc1tAkggppWzLnCCYjPN9zHrQrj8Fupzmkr"
	DefaultDelegatePort = 3000

	EnvelopeDeliveryTimeout = 1 * time.Second
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

func SetupLocalDHTPeer(key string, addr string, dhtPort uint16, delegatePort uint16, entry []string) (*DHTPeer, func(), error) {
	opts := []Option{
		LocalURI(DefaultLocalHost, dhtPort),
		PublicURI(DefaultLocalHost, dhtPort),
		IdentityFromFetchAIKey(key),
		RegisterAgentAddress(addr, func() bool { return true }),
		EnableRelayService(),
		EnableDelegateService(delegatePort),
		BootstrapFrom(entry),
	}

	dhtPeer, err := New(opts...)
	if err != nil {
		return nil, nil, err
	}

	return dhtPeer, func() { dhtPeer.Close() }, nil

}

func expectEnvelope(t *testing.T, rx chan aea.Envelope) {
	timeout := time.After(EnvelopeDeliveryTimeout)
	select {
	case envel := <-rx:
		t.Log("Received envelope", envel)
	case <-timeout:
		t.Error("Failed to receive envelope before timeout")
	}
}

// TestNewWithAeaAgent dht peer with agent attached
func TestNewWithAeaAgent(t *testing.T) {
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

	var rxEnvelopes []aea.Envelope
	dhtPeer.ProcessEnvelope(func(envel aea.Envelope) error {
		rxEnvelopes = append(rxEnvelopes, envel)
		return nil
	})

	err = dhtPeer.RouteEnvelope(aea.Envelope{
		To: DefaultAgentAddress,
	})
	if err != nil {
		t.Error("Failed to Route envelope to local Agent")
	}

	if len(rxEnvelopes) == 0 {
		t.Error("Failed to Route & Process envelope to local Agent")
	}

}

func TestRoutingTwoDHTPeers(t *testing.T) {
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

	rxPeer1 := make(chan aea.Envelope)
	dhtPeer1.ProcessEnvelope(func(envel aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan aea.Envelope)
	dhtPeer2.ProcessEnvelope(func(envel aea.Envelope) error {
		rxPeer2 <- envel
		return nil
	})

	err = dhtPeer2.RouteEnvelope(aea.Envelope{
		To:     AgentsTestAddresses[0],
		Sender: AgentsTestAddresses[1],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer 2 to peer 1:", err)
	}

	expectEnvelope(t, rxPeer1)
	expectEnvelope(t, rxPeer2)
}

func TestRoutingTwoDHTPeersIndirect(t *testing.T) {
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

	rxPeer1 := make(chan aea.Envelope)
	dhtPeer1.ProcessEnvelope(func(envel aea.Envelope) error {
		rxPeer1 <- envel
		err := dhtPeer1.RouteEnvelope(aea.Envelope{
			To:     envel.Sender,
			Sender: envel.To,
		})
		return err
	})

	rxPeer2 := make(chan aea.Envelope)
	dhtPeer2.ProcessEnvelope(func(envel aea.Envelope) error {
		rxPeer2 <- envel
		return nil
	})

	err = dhtPeer2.RouteEnvelope(aea.Envelope{
		To:     AgentsTestAddresses[1],
		Sender: AgentsTestAddresses[2],
	})
	if err != nil {
		t.Error("Failed to RouteEnvelope from peer 2 to peer 1:", err)
	}

	expectEnvelope(t, rxPeer1)
	expectEnvelope(t, rxPeer2)
}

func TestRoutingStarFullConnectivity(t *testing.T) {
	peers := []*DHTPeer{}
	rxs := []chan aea.Envelope{}

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

		rx := make(chan aea.Envelope)
		peer.ProcessEnvelope(func(envel aea.Envelope) error {
			rx <- envel
			if string(envel.Message) == "ping" {
				err := peer.RouteEnvelope(aea.Envelope{
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

	for i := range peers {
		for j := range peers {
			if i == j {
				continue
			}

			err := peers[i].RouteEnvelope(aea.Envelope{
				To:      AgentsTestAddresses[j],
				Sender:  AgentsTestAddresses[i],
				Message: []byte("ping"),
			})

			if err != nil {
				t.Error("Failed to RouteEnvelope from ", i, "to", j)
			}

			expectEnvelope(t, rxs[j])
			expectEnvelope(t, rxs[i])
		}
	}
}
