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
	"fmt"
	"time"

	"github.com/multiformats/go-multiaddr"
	"github.com/rs/zerolog"

	acn "libp2p_node/acn"
	utils "libp2p_node/utils"
)

// Option for dhtpeer.New
type Option func(*DHTPeer) error

// IdentityFromFetchAIKey for dhtpeer.New
func IdentityFromFetchAIKey(key string) Option {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.key, dhtPeer.publicKey, err = utils.KeyPairFromFetchAIKey(key)
		if err != nil {
			return err
		}
		return nil
	}
}

// RegisterAgentAddress for dhtpeer.New
func RegisterAgentAddress(record *acn.AgentRecord, isReady func() bool) Option {
	return func(dhtPeer *DHTPeer) error {
		pbRecord := &acn.AgentRecord{}
		pbRecord.Address = record.Address
		pbRecord.PublicKey = record.PublicKey
		pbRecord.PeerPublicKey = record.PeerPublicKey
		pbRecord.Signature = record.Signature
		pbRecord.ServiceId = record.ServiceId
		pbRecord.LedgerId = record.LedgerId

		dhtPeer.myAgentAddress = record.Address
		dhtPeer.myAgentRecord = pbRecord
		dhtPeer.myAgentReady = isReady
		return nil
	}
}

// BootstrapFrom for dhtpeer.New
func BootstrapFrom(entryPeers []string) Option {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.bootstrapPeers, err = utils.GetPeersAddrInfo(entryPeers)
		if err != nil {
			return err
		}
		return nil
	}
}

// LocalURI for dhtpeer.New
func LocalURI(host string, port uint16) Option {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.localMultiaddr, err =
			multiaddr.NewMultiaddr(fmt.Sprintf("/ip4/%s/tcp/%d", host, port))
		if err != nil {
			return err
		}
		dhtPeer.host = host
		dhtPeer.port = port
		return nil
	}
}

// PublicURI for dhtpeer.New
func PublicURI(host string, port uint16) Option {
	return func(dhtPeer *DHTPeer) error {
		var err error
		dhtPeer.publicMultiaddr, err =
			multiaddr.NewMultiaddr(fmt.Sprintf("/dns4/%s/tcp/%d", host, port))
		if err != nil {
			return err
		}
		dhtPeer.publicHost = host
		dhtPeer.publicPort = port
		return nil
	}
}

// EnableDelegateService for dhtpeer.New
func EnableDelegateService(port uint16) Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.delegatePort = port
		return nil
	}
}

// EnableMailboxService for dhtpeer.New
func EnableMailboxService(hostport string) Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.mailboxHostPort = hostport
		return nil
	}
}

// EnableRelayService for dhtpeer.New
func EnableRelayService() Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.enableRelay = true
		return nil
	}

}

// LoggingLevel for dhtpeer.New
func LoggingLevel(lvl zerolog.Level) Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.logger = dhtPeer.logger.Level(lvl)
		return nil
	}
}

// EnablePrometheusMonitoring for dhtpeer.New
func EnablePrometheusMonitoring(port uint16) Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.monitoringPort = port
		return nil
	}
}

// WithRegistrationDelay for dhtpeer.New
func WithRegistrationDelay(delay time.Duration) Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.registrationDelay = delay
		return nil
	}
}

// StoreRecordsTo for dhtpeer.New
func StoreRecordsTo(path string) Option {
	return func(dhtPeer *DHTPeer) error {
		dhtPeer.persistentStoragePath = path
		return nil
	}
}
