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

// Package dhtnode (in progress) contains the common interface between dhtpeer and dhtclient
package dhtnode

import "libp2p_node/aea"

// DHTNode libp2p node interface
type DHTNode interface {
	RouteEnvelope(*aea.Envelope) error
	ProcessEnvelope(func(*aea.Envelope) error)
	MultiAddr() string
	Close() []error
}
