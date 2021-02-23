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

package identity

import (
	"os"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog"
)

var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{
	Out:        os.Stdout,
	NoColor:    false,
	TimeFormat: "15:04:05.000",
}).
	With().Timestamp().
	Str("package", "AgentIdentity").
	Logger()

type AgentIdentity struct {
	LedgerId   string
	Address    string
	PublicKey  string
	PrivateKey string
}

func (agent_id *AgentIdentity) InitFromEnv() error {
	env_file := os.Args[1]
	logger.Debug().Msgf("env_file: %s", env_file)
	err := godotenv.Overload(env_file)
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("Error loading env file")
		return err
	}
	agent_id.LedgerId = os.Getenv("AEA_LEDGER_ID")
	agent_id.Address = os.Getenv("AEA_ADDRESS")
	agent_id.PublicKey = os.Getenv("AEA_PUBLIC_KEY")
	agent_id.PrivateKey = os.Getenv("AEA_PRIVATE_KEY")
	return nil
}
