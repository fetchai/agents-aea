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

package wallet

import (
	"log"
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
	Str("package", "Wallet").
	Logger()

type Wallet struct {
	LedgerId   string
	Address    string
	PublicKey  string
	PrivateKey string
}

func (wallet *Wallet) InitFromEnv() error {
	env_file := os.Args[1]
	logger.Debug().Msgf("env_file: %s", env_file)
	err := godotenv.Overload(env_file)
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("Error loading env file")
		return err
	}
	wallet.LedgerId = os.Getenv("AEA_LEDGER_ID")
	// todo: make useful with all three supported ledgers
	wallet.Address = os.Getenv("AEA_ADDRESS")
	wallet.PublicKey = os.Getenv("AEA_PUBLIC_KEY")
	wallet.PrivateKey = os.Getenv("AEA_PRIVATE_KEY")
	if wallet.PrivateKey == "" {
		log.Fatal("No private key provided")
	}
	public_key, err := FetchAIPublicKeyFromFetchAIPrivateKey(wallet.PrivateKey)
	if err != nil {
		log.Fatal("Could not derive public key")
	}
	if (wallet.PublicKey != "") && (public_key != wallet.PublicKey) {
		log.Fatal("Derived and provided public_key don't match.")
	}
	wallet.PublicKey = public_key
	address, err := FetchAIAddressFromPublicKey(wallet.PublicKey)
	if err != nil {
		log.Fatal("Could not derive address")
	}
	if (wallet.Address != "") && (address != wallet.Address) {
		log.Fatal("Derived and provided address don't match.")
	}
	wallet.Address = address
	return nil
}
