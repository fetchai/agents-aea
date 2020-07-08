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

package dhtclient

import (
	"testing"
	"time"

	"libp2p_node/aea"
	"libp2p_node/dht/dhttests"
)

//
const (
	DefaultFetchAIKey   = "3916b301d1a0ec09de1db4833b0c945531004290caee0b4a5d7b554caa39dbf1"
	DefaultAgentAddress = "2TsHmM9JXeFgK928LYc6HV96gi78pBv6sWprJAXaS6ydg9MTC6"

	EnvelopeDeliveryTimeout = 10 * time.Second
)

// TestNew dht client peer
func TestNew(t *testing.T) {

	rxEnvelopesPeer := make(chan *aea.Envelope)
	dhtPeer, cleanup, err := dhttests.NewDHTPeerWithDefaults(rxEnvelopesPeer)
	if err != nil {
		t.Fatal("Failed to create DHTPeer (required for DHTClient):", err)
	}
	defer cleanup()

	opts := []Option{
		IdentityFromFetchAIKey(DefaultFetchAIKey),
		RegisterAgentAddress(DefaultAgentAddress, func() bool { return true }),
		BootstrapFrom([]string{dhtPeer.MultiAddr()}),
	}

	t.Log(dhtPeer.MultiAddr())

	dhtClient, err := New(opts...)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClient.Close()

	rxEnvelopesClient := make(chan *aea.Envelope)
	dhtClient.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxEnvelopesClient <- envel
		return nil
	})

}

// TestRouteEnvelopeToPeerAgent send envelope from DHTClient agent to DHTPeer agent
func TestRouteEnvelopeToPeerAgent(t *testing.T) {

	rxEnvelopesPeer := make(chan *aea.Envelope)
	dhtPeer, cleanup, err := dhttests.NewDHTPeerWithDefaults(rxEnvelopesPeer)
	if err != nil {
		t.Fatal("Failed to create DHTPeer (required for DHTClient):", err)
	}
	defer cleanup()

	opts := []Option{
		IdentityFromFetchAIKey(DefaultFetchAIKey),
		RegisterAgentAddress(DefaultAgentAddress, func() bool { return true }),
		BootstrapFrom([]string{dhtPeer.MultiAddr()}),
	}

	t.Log(dhtPeer.MultiAddr())

	dhtClient, err := New(opts...)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClient.Close()

	rxEnvelopesClient := make(chan *aea.Envelope)
	dhtClient.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxEnvelopesClient <- envel
		return nil
	})

	if len(rxEnvelopesPeer) != 0 {
		t.Error("DHTPeer agent inbox should be empty")
	}

	err = dhtClient.RouteEnvelope(&aea.Envelope{
		To:     dhttests.DHTPeerDefaultAgentAddress,
		Sender: DefaultAgentAddress,
	})
	if err != nil {
		t.Error("Failed to Route envelope to DHTPeer agent:", err)
	}

	timeout := time.After(EnvelopeDeliveryTimeout)
	select {
	case envel := <-rxEnvelopesPeer:
		t.Log("DHT received envelope", envel)
	case <-timeout:
		t.Error("Failed to Route envelope to DHTPeer agent")
	}

}
