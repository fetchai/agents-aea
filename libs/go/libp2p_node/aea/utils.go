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

package aea

import (
	"errors"

	acn "libp2p_node/acn"
	common "libp2p_node/common"

	proto "google.golang.org/protobuf/proto"
)

func HandleAcnMessageFromPipe(
	pipe common.Pipe,
	statusQueue acn.StatusQueue,
	counterpartyID string,
) (*Envelope, error) {
	envelope := &Envelope{}
	var acn_err error

	data, err := pipe.Read()

	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return nil, &common.PipeError{Err: err, Msg: "Pipe error during envelope read"}
	}

	msg_type, acn_envelope, status, acnErr := acn.DecodeAcnMessage(data)

	if acnErr != nil {
		logger.Error().Str("err", acnErr.Error()).Msg("while handling acn message")
		acn_err = acn.SendAcnError(
			pipe,
			acnErr.Error(),
			acnErr.ErrorCode,
		)
		if acn_err != nil {
			logger.Error().Str("err", acn_err.Error()).Msg("on acn send error")
		}
		return envelope, acnErr
	}

	switch msg_type {
	case "aea_envelope":
		{
			err = proto.Unmarshal(acn_envelope.Envelope, envelope)
			if err != nil {
				logger.Error().Str("err", err.Error()).Msg("while decoding envelope")
				acn_err = acn.SendAcnError(
					pipe,
					"error on decoding envelope",
					acn.ERROR_DECODE,
				)
				if acn_err != nil {
					logger.Error().Str("err", acn_err.Error()).Msg("on acn send error")
				}
				return envelope, err
			}
			err = acn.SendAcnSuccess(pipe)
			return envelope, err

		}
	case "status":
		{
			logger.Debug().Msgf("got acn status %d", status.Code)
			statusQueue.AddAcnStatusMessage(status, counterpartyID)
			return nil, nil

		}
	default:
		{
			acn_err = acn.SendAcnError(pipe, "Unsupported ACN message")
			if acn_err != nil {
				logger.Error().Str("err", acn_err.Error()).Msg("on acn send error")
			}
			return nil, errors.New("unsupported ACN message")
		}
	}
}
