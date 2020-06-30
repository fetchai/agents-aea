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

// Package dhttests offers utilities to facilitate tests of dhtpeer, dhtclient, and dhtnetwork packages
package dhttests

import (
	"libp2p_node/aea"
	"libp2p_node/dht/dhtpeer"
	"log"
)

//
const (
	DHTPeerDefaultLocalHost    = "127.0.0.1"
	DHTPeerDefaultLocalPort    = 2000
	DHTPeerDefaultFetchAIKey   = "5071fbef50ed1fa1061d84dbf8152c7811f9a3a992ca6c43ae70b80c5ceb56df"
	DHTPeerDefaultAgentAddress = "2FRCqDBo7Yw3E2VJc1tAkggppWzLnCCYjPN9zHrQrj8Fupzmkr"
	DHTPeerDefaultDelegatePort = 3000

	DHTClientDefaultFetchAIKey   = "3916b301d1a0ec09de1db4833b0c945531004290caee0b4a5d7b554caa39dbf1"
	DHTClientDefaultAgentAddress = "2TsHmM9JXeFgK928LYc6HV96gi78pBv6sWprJAXaS6ydg9MTC6"
)

// NewDHTPeerWithDefaults for testing
func NewDHTPeerWithDefaults(inbox chan<- *aea.Envelope) (*dhtpeer.DHTPeer, func(), error) {
	opts := []dhtpeer.Option{
		dhtpeer.LocalURI(DHTPeerDefaultLocalHost, DHTPeerDefaultLocalPort),
		dhtpeer.PublicURI(DHTPeerDefaultLocalHost, DHTPeerDefaultLocalPort),
		dhtpeer.IdentityFromFetchAIKey(DHTPeerDefaultFetchAIKey),
		dhtpeer.RegisterAgentAddress(DHTPeerDefaultAgentAddress, func() bool { return true }),
		dhtpeer.EnableRelayService(),
		dhtpeer.EnableDelegateService(DHTPeerDefaultDelegatePort),
	}

	dhtPeer, err := dhtpeer.New(opts...)
	if err != nil {
		return nil, nil, err
	}

	cleanup := func() {
		errs := dhtPeer.Close()
		if len(errs) > 0 {
			log.Println("ERROR while stoping DHTPeer:", errs)
		}
	}

	dhtPeer.ProcessEnvelope(func(envel *aea.Envelope) error {
		inbox <- envel
		return nil
	})

	return dhtPeer, cleanup, nil
}
