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

	"libp2p_node/acn"
	"libp2p_node/aea"
	"libp2p_node/dht/dhtnode"
	"libp2p_node/dht/dhttests"
	utils "libp2p_node/utils"
)

//
const (
	DefaultFetchAIKey       = "04ab8ac134ec727917cf4f9e47685e84622151bc8b12838bc54c8ffe5d44d04a"
	DefaultFetchAIPublicKey = "03b07ef4513e3f0372245b3d6d474d871ba58eacaf3a2a07c487af6d82006b86b4"
	DefaultAgentKey         = "f76137a61c1ad3ee8a0a9a185bc8e6fa51be1a2528f86042c11f9cc00880024a"
	DefaultAgentPublicKey   = "021820ce23b5f3a6ef01988149e724af854f89d37b9cabc3b1702cc5287f617b92"
	DefaultAgentAddress     = "fetch1ver6u7xdvkjy4dq8xxrkc6ualu98k7ykumv08q"

	EnvelopeDeliveryTimeout = 10 * time.Second

	DefaultLedger = dhtnode.DefaultLedger
)

// TestNew dht client peer
func TestNew(t *testing.T) {

	rxEnvelopesPeer := make(chan *aea.Envelope, 2)
	dhtPeer, cleanup, err := dhttests.NewDHTPeerWithDefaults(rxEnvelopesPeer)
	if err != nil {
		t.Fatal("Failed to create DHTPeer (required for DHTClient):", err)
	}
	defer cleanup()

	signature, err := utils.SignFetchAI([]byte(DefaultFetchAIPublicKey), DefaultAgentKey)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}

	record := &acn.AgentRecord{LedgerId: DefaultLedger}
	record.Address = DefaultAgentAddress
	record.PublicKey = DefaultAgentPublicKey
	record.PeerPublicKey = DefaultFetchAIPublicKey
	record.Signature = signature

	opts := []Option{
		IdentityFromFetchAIKey(DefaultFetchAIKey),
		RegisterAgentAddress(record, func() bool { return true }),
		BootstrapFrom([]string{dhtPeer.MultiAddr()}),
	}

	t.Log(dhtPeer.MultiAddr())

	dhtClient, err := New(opts...)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClient.Close()

	rxEnvelopesClient := make(chan *aea.Envelope, 2)
	dhtClient.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxEnvelopesClient <- envel
		return nil
	})

}

// TestRouteEnvelopeToPeerAgent send envelope from DHTClient agent to DHTPeer agent
func TestRouteEnvelopeToPeerAgent(t *testing.T) {

	rxEnvelopesPeer := make(chan *aea.Envelope, 2)
	dhtPeer, cleanup, err := dhttests.NewDHTPeerWithDefaults(rxEnvelopesPeer)
	if err != nil {
		t.Fatal("Failed to create DHTPeer (required for DHTClient):", err)
	}
	defer cleanup()

	signature, err := utils.SignFetchAI([]byte(DefaultFetchAIPublicKey), DefaultAgentKey)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}

	record := &acn.AgentRecord{LedgerId: DefaultLedger}
	record.Address = DefaultAgentAddress
	record.PublicKey = DefaultAgentPublicKey
	record.PeerPublicKey = DefaultFetchAIPublicKey
	record.Signature = signature

	opts := []Option{
		IdentityFromFetchAIKey(DefaultFetchAIKey),
		RegisterAgentAddress(record, func() bool { return true }),
		BootstrapFrom([]string{dhtPeer.MultiAddr()}),
	}

	t.Log(dhtPeer.MultiAddr())

	dhtClient, err := New(opts...)
	if err != nil {
		t.Fatal("Failed to initialize DHTClient:", err)
	}
	defer dhtClient.Close()

	rxEnvelopesClient := make(chan *aea.Envelope, 2)
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
