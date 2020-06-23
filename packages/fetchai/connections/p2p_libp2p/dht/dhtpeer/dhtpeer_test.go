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

	"libp2p_node/aea"
)

//
const (
	DefaultLocalHost    = "127.0.0.1"
	DefaultLocalPort    = 2000
	DefaultFetchAIKey   = "5071fbef50ed1fa1061d84dbf8152c7811f9a3a992ca6c43ae70b80c5ceb56df"
	DefaultAgentAddress = "2FRCqDBo7Yw3E2VJc1tAkggppWzLnCCYjPN9zHrQrj8Fupzmkr"
	DefaultDelegatePort = 3000
)

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
