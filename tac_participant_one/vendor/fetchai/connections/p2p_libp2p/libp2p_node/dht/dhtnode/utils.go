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

// Package dhtnode contains the common interface between dhtpeer and dhtclient
// TODO: extraction of shared functionality is work in progress
package dhtnode

import (
	"errors"
	"strings"

	acn "libp2p_node/acn"
	utils "libp2p_node/utils"
)

const (
	DefaultLedger  = "fetchai"
	CurrentVersion = "0.1.0"
)

var supportedLedgers = []string{"fetchai", "cosmos", "ethereum"}

func IsValidProofOfRepresentation(
	record *acn.AgentRecord,
	agentAddress string,
	representativePeerPubKey string,
) (*acn.StatusBody, error) {
	// check agent address matches
	if record.Address != agentAddress {
		err := errors.New("Wrong agent address, expected " + agentAddress)
		response := &acn.StatusBody{
			Code: acn.ERROR_WRONG_AGENT_ADDRESS,
			Msgs: []string{err.Error()},
		}
		return response, err
	}

	// check if ledger is supported
	var found = false
	for _, supported := range supportedLedgers {
		if record.LedgerId == supported {
			found = true
			break
		}
	}
	if !found {
		err := errors.New(
			"Unsupported ledger " + record.LedgerId + ", expected " + strings.Join(
				supportedLedgers,
				",",
			),
		)
		response := &acn.StatusBody{Code: acn.ERROR_UNSUPPORTED_LEDGER, Msgs: []string{err.Error()}}
		return response, err
	}

	// check public key matches
	if record.PeerPublicKey != representativePeerPubKey {
		err := errors.New("Wrong peer public key, expected " + representativePeerPubKey)
		response := &acn.StatusBody{Code: acn.ERROR_WRONG_PUBLIC_KEY, Msgs: []string{err.Error()}}
		return response, err
	}

	// check that agent address and public key match
	addrFromPubKey, err := utils.AgentAddressFromPublicKey(record.LedgerId, record.PublicKey)
	if err != nil || addrFromPubKey != record.Address {
		if err == nil {
			err = errors.New("agent address and public key don't match")
		}
		response := &acn.StatusBody{Code: acn.ERROR_WRONG_AGENT_ADDRESS}
		return response, err
	}

	// check that signature is valid
	ok, err := utils.VerifyLedgerSignature(
		record.LedgerId,
		[]byte(record.PeerPublicKey),
		record.Signature,
		record.PublicKey,
	)
	if !ok || err != nil {
		if err == nil {
			err = errors.New("signature is not valid")
		}
		response := &acn.StatusBody{Code: acn.ERROR_INVALID_PROOF}
		return response, err

	}

	// PoR is valid
	response := &acn.StatusBody{Code: acn.SUCCESS}
	return response, nil

}
