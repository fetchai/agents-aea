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
	"libp2p_node/acn"
	"libp2p_node/aea"
	"libp2p_node/dht/dhtnode"
	"libp2p_node/dht/dhtpeer"
	"libp2p_node/utils"
	"log"
	"math/rand"
	"os"
	"path"
)

//
const (
	DHTPeerDefaultLocalHost    = "127.0.0.1"
	DHTPeerDefaultLocalPort    = 2000
	DHTPeerDefaultDelegatePort = 3000

	DHTPeerDefaultFetchAIKey       = "34604436e55b0eb99b5e62508433e172dd3ee133cf7a2fecb705e69611147605"
	DHTPeerDefaultFetchAIPublicKey = "039e883de988eededb9afaa4d3a6baec9ba74dd1cc237028e810569780b319940a"

	DHTPeerDefaultAgentKey       = "719133dc740d76ff6d1d325e193f7cd63af4c8f3491bfe3010e58b0b58c77795"
	DHTPeerDefaultAgentPublicKey = "039623e63ba1617404b2abbe7bd94d24eb788335f870fac1ae4519e9bc359b7833"
	DHTPeerDefaultAgentAddress   = "fetch134rg4n3wgmwctxsrm7gp6l65uwv6hxtxyfdwgw"
)

func randSeq(n int) string {
	var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
	b := make([]rune, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}

// NewDHTPeerWithDefaults for testing
func NewDHTPeerWithDefaults(inbox chan<- *aea.Envelope) (*dhtpeer.DHTPeer, func(), error) {
	opts := []dhtpeer.Option{
		dhtpeer.LocalURI(DHTPeerDefaultLocalHost, DHTPeerDefaultLocalPort),
		dhtpeer.PublicURI(DHTPeerDefaultLocalHost, DHTPeerDefaultLocalPort),
		dhtpeer.IdentityFromFetchAIKey(DHTPeerDefaultFetchAIKey),
		dhtpeer.EnableRelayService(),
		dhtpeer.EnableDelegateService(DHTPeerDefaultDelegatePort),
		dhtpeer.StoreRecordsTo(path.Join(os.TempDir(), "agents_records_"+randSeq(5))),
	}

	signature, err := utils.SignFetchAI(
		[]byte(DHTPeerDefaultFetchAIPublicKey),
		DHTPeerDefaultAgentKey,
	)
	if err != nil {
		return nil, nil, err
	}

	record := &acn.AgentRecord{LedgerId: dhtnode.DefaultLedger}
	record.Address = DHTPeerDefaultAgentAddress
	record.PublicKey = DHTPeerDefaultAgentPublicKey
	record.PeerPublicKey = DHTPeerDefaultFetchAIPublicKey
	record.Signature = signature

	opts = append(opts, dhtpeer.RegisterAgentAddress(record, func() bool { return true }))

	dhtPeer, err := dhtpeer.New(opts...)
	if err != nil {
		return nil, nil, err
	}

	cleanup := func() {
		errs := dhtPeer.Close()
		if len(errs) > 0 {
			log.Println("ERROR while stopping DHTPeer:", errs)
		}
	}

	dhtPeer.ProcessEnvelope(func(envel *aea.Envelope) error {
		inbox <- envel
		return nil
	})

	return dhtPeer, cleanup, nil
}
