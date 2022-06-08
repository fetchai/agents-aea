/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2022 Fetch.AI Limited
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

// Package dhtpeer provides an implementation of an Agent Communication Network node
// using libp2p. It participates in data storage and routing for the network.
// It offers RelayService for dhtclient and DelegateService for tcp clients.
package dhtpeer

import (
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/multiformats/go-multiaddr"
	"github.com/rs/zerolog"
)

// Notifee Handle DHTClient network events
type Notifee struct {
	logger zerolog.Logger
}

// Listen called when network starts listening on an addr
func (notifee *Notifee) Listen(network.Network, multiaddr.Multiaddr) {}

// ListenClose called when network stops listening on an addr
func (notifee *Notifee) ListenClose(network.Network, multiaddr.Multiaddr) {}

// Connected called when a connection opened
func (notifee *Notifee) Connected(net network.Network, conn network.Conn) {
	notifee.logger.Info().Msgf(
		"Connected to peer %s",
		conn.RemotePeer().Pretty(),
	)

}

// Disconnected called when a connection closed
// Reconnects if connection is to relay peer and not currenctly closing connection.
func (notifee *Notifee) Disconnected(net network.Network, conn network.Conn) {
	notifee.logger.Info().Msgf(
		"Disconnected from peer %s",
		conn.RemotePeer().Pretty(),
	)
}

// OpenedStream called when a stream opened
func (notifee *Notifee) OpenedStream(network.Network, network.Stream) {}

// ClosedStream called when a stream closed
func (notifee *Notifee) ClosedStream(network.Network, network.Stream) {}
