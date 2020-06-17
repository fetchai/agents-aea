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
	"github.com/libp2p/go-libp2p-core/peer"

	aea "libp2p_node/aea"
)

// panics if err is not nil
func check(err error) {
	if err != nil {
		panic(err)
	}
}

// DHTClient
// A restricted libp2p node for the Agents Communication Network
// It use a `DHTPeer` to communicate with other peers.
type DHTClient struct {
	bootstrapPeers  []peer.AddrInfo
	relayPeer       peer.ID
	processEnvelope func(aea.Envelope) error
}
