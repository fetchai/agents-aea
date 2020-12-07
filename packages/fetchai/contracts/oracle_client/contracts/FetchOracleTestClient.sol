// SPDX-License-Identifier:Apache-2.0
//------------------------------------------------------------------------------
//
//   Copyright 2020 Fetch.AI Limited
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.
//
//------------------------------------------------------------------------------

pragma solidity ^0.6.0;

import "./FetchOracleMock.sol";
import "../interfaces/IFetchOracleClient.sol";

contract FetchOracleTestClient is IFetchOracleClient{
    FetchOracle public _fetch_oracle;

    uint256 public _value;
    uint8 public _decimals;
    uint256 public _updatedAtEthBlockNumber;


    constructor(address fetchOracleContractAddress) public {
        // NOTE(pb): We expect this to de deployed on testnet only:
        _fetch_oracle = FetchOracleMock(fetchOracleContractAddress);
    }


    function queryOracleValue() external override
    {
        _fetch_oracle._token().transferFrom(msg.sender, address(this), _fetch_oracle._fee());
        _fetch_oracle._token().approve(address(_fetch_oracle), _fetch_oracle._fee());
        (_value, _decimals, _updatedAtEthBlockNumber) = _fetch_oracle.queryOracleValue();
    }
}

// Contract created exclusively for more comfortable usage in truffle:
contract FetchOracleTestClientETH is FetchOracleTestClient {
    constructor(address fetchOracleContractAddress) public FetchOracleTestClient(fetchOracleContractAddress) {
    }
}
