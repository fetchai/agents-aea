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

import "../openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../openzeppelin/contracts/access/AccessControl.sol";
import "../openzeppelin/contracts/math/SafeMath.sol";


/**
 @dev The contract *INTENTIONALLY* does not contain the `receive()` or fallback functions in order to ensure that all
      unsolicited direct ETH transfers in to this contract (in direct Transaction) will fail.
      Only way how to make successful fee transfer in ETH currency (*IF* contract is initialised for ETH as fee currency),
      is to make transfer ETH to caller(client) contract and client contract then is responsible for further
      *programmatic* (= *not* via Tx) transfer of fee to this this contract.
 */
contract FetchOracle is AccessControl {
    using SafeMath for uint256;


    enum  FeeCurrency { ERC20, ETH }

    struct OracleValue {
        uint256 value;
        uint8 decimals;
        uint256 updatedAtEthBlockNumber;
    }

    event FeeUpdated(uint256 fee);
    event Pause(uint256 sinceBlock);
    event ExcessTokenWithdrawal(address targetAddress, uint256 amount);
    event AccruedFeesWithdrawal(address targetAddress, uint256 amount);
    event ContractDeleted();
    event OracleValueUpdated(uint256 atBlock); 


    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant DELEGATE_ROLE = keccak256("DELEGATE_ROLE");
    uint256 public constant DELETE_PROTECTION_PERIOD = 370285;// 60*24*60*60[s] / (14[s/block]) = 370285[block];

    IERC20 public _token;
    uint256 public _earliestDelete;
    uint256 public _pausedSinceBlock;
    uint256 public _fee;
    uint256 public _accruedFeesAmount;
    OracleValue private _oracleValue;
    FeeCurrency public _feeCurrency;

    function _isOwner() internal view returns(bool) {
        return hasRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /* Only callable by owner */
    modifier onlyOwner() {
        require(_isOwner(), "Caller is not an administrator");
        _;
    }

    /* Only callable by owner or delegate */
    modifier onlyDelegate() {
        require(_isOwner() || hasRole(DELEGATE_ROLE, msg.sender), "Caller is neither owner nor delegate");
        _;
    }

    /* Only callable by oracle */
    modifier onlyOracle() {
        require(hasRole(ORACLE_ROLE, msg.sender), "Caller is not an oracle");
        _;
    }

    modifier verifyTxExpiration(uint256 expirationBlock) {
        require(_getBlockNumber() <= expirationBlock, "Transaction expired");
        _;
    }

    modifier verifyNotPaused() {
        require(_pausedSinceBlock > _getBlockNumber(), "Contract has been paused");
        _;
    }


    /*******************
    Contract start
    *******************/
    /**
     * @param ERC20Address address of the ERC20 contract
     */
    constructor(address ERC20Address, uint256 initialFee) public {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);

        if (ERC20Address == address(0)) {
            _feeCurrency = FeeCurrency.ETH;
        } else {
            _feeCurrency = FeeCurrency.ERC20;
            _token = IERC20(ERC20Address);
        }

        _earliestDelete = _getBlockNumber().add(DELETE_PROTECTION_PERIOD);
        _pausedSinceBlock = ~uint256(0);
        _fee = initialFee;
    }


    function updateOracleValue(
        uint256 value,
        uint8 decimals,
        uint256 txExpirationBlock
        )
        external
        verifyTxExpiration(txExpirationBlock)
        onlyOracle
    {
        _oracleValue.value = value;
        _oracleValue.decimals = decimals;
        _oracleValue.updatedAtEthBlockNumber = _getBlockNumber();
        emit OracleValueUpdated(_oracleValue.updatedAtEthBlockNumber); 
    }


    function queryOracleValue()
        public payable
        returns (uint256 value, uint8 decimals, uint256 updatedAtEthBlockNumber)
    {
        _withdrawFee();
        value = _oracleValue.value;
        decimals = _oracleValue.decimals;
        updatedAtEthBlockNumber = _oracleValue.updatedAtEthBlockNumber;
    }


    /**
     * @dev Pause the non-administrative interaction with the contract
     * @param fee - value of fee
     * @param txExpirationBlock - block number defined by Tx sender beyond which transaction becomes invalid
     * @dev Owners only
     */
    function setFee(uint256 fee, uint256 txExpirationBlock)
        external
        verifyTxExpiration(txExpirationBlock)
        onlyDelegate
    {
        _fee = fee;
        emit FeeUpdated(_fee);
    }


    /**
     * @dev Pause the non-administrative interaction with the contract
     * @param block_number disallow non-admin. interactions with contract for a _getBlockNumber() >= block_number
     * @dev Owners only
     */
    function pauseSince(uint256 block_number, uint256 txExpirationBlock)
        external
        verifyTxExpiration(txExpirationBlock)
        onlyDelegate
    {
        uint256 curr_block_number = _getBlockNumber();
        _pausedSinceBlock = block_number < curr_block_number ? curr_block_number : block_number;
        emit Pause(_pausedSinceBlock);
    }


    /**
     * @dev Withdraw whole balance of all fees accrued in the contract so far.
     * @param targetAddress : address to send tokens to
     * @param txExpirationBlock : block number until which is the transaction valid (inclusive).
     *                            When transaction is processed after this block, it fails.
     * @dev Owners only
     */
    function withdrawAccruedFees(address payable targetAddress, uint256 txExpirationBlock)
        external
        verifyTxExpiration(txExpirationBlock)
        onlyOwner
    {
        if (_accruedFeesAmount == 0) {
            return;
        }

        // The following method will revert in the case of issue (e.g. not enough balance for transfer, zero address):
        _withdrawFromContract(targetAddress, _accruedFeesAmount);

        emit AccruedFeesWithdrawal(targetAddress, _accruedFeesAmount);
        _accruedFeesAmount = 0;
    }


    /**
     * @dev Withdraw "excess" tokens, which were sent to contract address directly via direct ERC20 transfer(...) or transferFrom(...),
     *      without interacting with API of this (FetchOracle) contract, what could be done only by mistake.
     *      Thus this method is meant to be used primarily for rescue purposes, enabling withdrawal of such
     *      "excess" tokens out of contract.
     * @param targetAddress : address to send tokens to
     * @param txExpirationBlock : block number until which is the transaction valid (inclusive).
     *                            When transaction is processed after this block, it fails.
     */
    function withdrawExcessTokens(address payable targetAddress, uint256 txExpirationBlock)
        external
        verifyTxExpiration(txExpirationBlock)
        onlyOwner
    {
        uint256 contractBalance;

        if (_feeCurrency == FeeCurrency.ETH)
        {
            contractBalance = address(this).balance;
        }
        else if (_feeCurrency == FeeCurrency.ERC20) {
            contractBalance = _token.balanceOf(address(this));
        } // NOTE(pb): Final else{...} is not necessary since it is checked in the `_withdrawFromContract(...)` call bellow

        // NOTE(pb): The following subtraction shall *fail* (revert) IF the contract is in *INCONSISTENT* state,
        //           = when contract balance is less than minial expected balance:
        uint256 excessAmount = contractBalance.sub(_accruedFeesAmount);
        _withdrawFromContract(targetAddress, excessAmount);
        emit ExcessTokenWithdrawal(targetAddress, excessAmount);
    }


    /**
     * @dev Delete the contract, transfers the remaining token and ether balance to the specified
       payoutAddress
     * @param payoutAddress address to transfer the balances to. Ensure that this is able to handle ERC20 tokens
     * @dev owner only + only on or after `_earliestDelete` block
     */
    function deleteContract(address payable payoutAddress, uint256 txExpirationBlock)
        external
        verifyTxExpiration(txExpirationBlock)
        onlyOwner
    {
        require(_earliestDelete >= _getBlockNumber(), "Earliest delete not reached");
        if (_feeCurrency == FeeCurrency.ERC20) {
            uint256 contractBalance = _token.balanceOf(address(this));
            require(_token.transfer(payoutAddress, contractBalance));
        }
        emit ContractDeleted();
        // The selfdestruct, by design, transfers *whole* ETH balance from this contract to targetAddress:
        selfdestruct(payoutAddress);
    }


    function oracleValueLastUpdated() external view returns(uint256)
    {
        return _oracleValue.updatedAtEthBlockNumber;
    }

    function _getBlockNumber() internal view virtual returns(uint256)
    {
        return block.number;
    }


    /**
     * @dev Withdraw fee from the caller.
     */
    function _withdrawFee() internal
    {
        if (_feeCurrency == FeeCurrency.ETH)
        {
           if (msg.value == _fee)
           {
               // No action necessary, since exact expected fee amount has been already transferred by caller,
               // this this is just placeholder block to capture the logical condition.
           }
           else if (msg.value > _fee)
           {
               // Refund (back to caller) the excess caller paid on top of the expected _fee value:
               msg.sender.transfer(msg.value.sub(_fee));
           }
           else
           {
               require(false, "Insuf. ETH amount sent by caller");
           }
        }
        else if (_feeCurrency == FeeCurrency.ERC20)
        {
            require(_token.transferFrom(msg.sender, address(this), _fee), "Insuf. FET allow. on caller addr");
        }
        else
        {
            require(false, "Unexpected contract fee currency");
        }

        _accruedFeesAmount = _accruedFeesAmount.add(_fee);
    }


    function _withdrawFromContract(address payable targetAddress, uint256 amount) internal
    {
        require(targetAddress != address(0), "Target is zero address");

        if (_feeCurrency == FeeCurrency.ETH)
        {
            // NOTE(pb): The following transfer shall *fail* with revert IF contract balance is insufficient for transfer
            targetAddress.transfer(amount);
        }
        else if (_feeCurrency == FeeCurrency.ERC20)
        {
            // NOTE(pb): The following transfer shall *fail* with revert IF contract balance is insufficient for transfer
            require(_token.transfer(targetAddress, amount), "Insuff. FET funds on contr. addr");
        }
        else
        {
            require(false, "Unexpected contract fee currency");
        }
    }
}
