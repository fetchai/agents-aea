# Author: Sören Steiger, github.com/ssteiger
# Author: Fetch.ai, github.com/fetchai
# License: MIT

# ERC1155 Token Standard
# https://eips.ethereum.org/EIPS/eip-1155

########################EXTERNAL-CONTRACTS####################################

contract ERC1155TokenReceiver:
    # Note: The ERC-165 identifier for this interface is 0x4e2312e0.

    def onERC1155Received(_operator: address, _from: address, _id: uint256, _value: uint256,
                          _data: bytes[256]) -> bytes32: modifying  # TODO: should return bytes4
    #        """
    #       @notice Handle the receipt of a single ERC1155 token type.
    #       @dev An ERC1155-compliant smart contract MUST call this function on the token recipient contract, at the end of a `safeTransferFrom` after the balance has been updated.        
    #       This function MUST return `bytes4(keccak256("onERC1155Received(address,address,uint256,uint256,bytes)"))` (i.e. 0xf23a6e61) if it accepts the transfer.
    #       This function MUST revert if it rejects the transfer.
    #       Return of any other value than the prescribed keccak256 generated value MUST result in the transaction being reverted by the caller.
    #       @param _operator  The address which initiated the transfer (i.e. msg.sender)
    #       @param _from      The address which previously owned the token
    #       @param _id        The ID of the token being transferred
    #       @param _value     The amount of tokens being transferred
    #       @param _data      Additional data with no specified format
    #       @return           `bytes4(keccak256("onERC1155Received(address,address,uint256,uint256,bytes)"))`
    #       """

    def onERC1155BatchReceived(_operator: address, _from: address, _ids: uint256[BATCH_SIZE], _values: uint256[BATCH_SIZE],
                               _data: bytes[256]) -> bytes32: modifying  # TODO: should return bytes4
    #       """
    #       @notice Handle the receipt of multiple ERC1155 token types.
    #       @dev An ERC1155-compliant smart contract MUST call this function on the token recipient contract, at the end of a `safeBatchTransferFrom` after the balances have been updated.        
    #       This function MUST return `bytes4(keccak256("onERC1155BatchReceived(address,address,uint256[],uint256[],bytes)"))` (i.e. 0xbc197c81) if it accepts the transfer(s).
    #       This function MUST revert if it rejects the transfer(s).
    #       Return of any other value than the prescribed keccak256 generated value MUST result in the transaction being reverted by the caller.
    #       @param _operator  The address which initiated the batch transfer (i.e. msg.sender)
    #       @param _from      The address which previously owned the token
    #       @param _ids       An array containing ids of each token being transferred (order and length must match _values array)
    #       @param _values    An array containing amounts of each token being transferred (order and length must match _ids array)
    #       @param _data      Additional data with no specified format
    #       @return           `bytes4(keccak256("onERC1155BatchReceived(address,address,uint256[],uint256[],bytes)"))`
    #       """

########################END-EXTERNAL-CONTRACTS####################################
########################EVENTS####################################

MAX_URI_SIZE: constant(uint256) = 1024

TransferSingle: event({_operator: indexed(address), _from: indexed(address), _to: indexed(address), _id: uint256,
                       _value: uint256})
#   @dev Either `TransferSingle` or `TransferBatch` MUST emit when tokens are transferred, including zero value transfers as well as minting or burning (see "Safe Transfer Rules" section of the standard).
#        The `_operator` argument MUST be the address of an account/contract that is approved to make the transfer (SHOULD be msg.sender).
#        The `_from` argument MUST be the address of the holder whose balance is decreased.
#        The `_to` argument MUST be the address of the recipient whose balance is increased.
#        The `_id` argument MUST be the token type being transferred.
#        The `_value` argument MUST be the number of tokens the holder balance is decreased by and match what the recipient balance is increased by.
#        When minting/creating tokens, the `_from` argument MUST be set to `0x0` (i.e. zero address).
#        When burning/destroying tokens, the `_to` argument MUST be set to `0x0` (i.e. zero address).


TransferBatch: event({_operator: indexed(address), _from: indexed(address), _to: indexed(address),
                      _ids: uint256[BATCH_SIZE], _values: uint256[BATCH_SIZE]})
#   @dev Either `TransferSingle` or `TransferBatch` MUST emit when tokens are transferred, including zero value transfers as well as minting or burning (see "Safe Transfer Rules" section of the standard).
#        The `_operator` argument MUST be the address of an account/contract that is approved to make the transfer (SHOULD be msg.sender).
#        The `_from` argument MUST be the address of the holder whose balance is decreased.
#        The `_to` argument MUST be the address of the recipient whose balance is increased.
#        The `_ids` argument MUST be the list of tokens being transferred.
#        The `_values` argument MUST be the list of number of tokens (matching the list and order of tokens specified in _ids) the holder balance is decreased by and match what the recipient balance is increased by.
#        When minting/creating tokens, the `_from` argument MUST be set to `0x0` (i.e. zero address).
#        When burning/destroying tokens, the `_to` argument MUST be set to `0x0` (i.e. zero address).


ApprovalForAll: event({_owner: indexed(address), _operator: indexed(address), _approved: bool})
#   @dev MUST emit when approval for a second party/operator address to manage all tokens for an owner address is enabled or disabled (absence of an event assumes disabled).


URI: event({_value: string[MAX_URI_SIZE], _id: indexed(uint256)})
#   @dev MUST emit when the URI is updated for a token ID.
#        URIs are defined in RFC 3986.
#        The URI MUST point to a JSON file that conforms to the "ERC-1155 Metadata URI JSON Schema".

########################END-EVENTS####################################
########################INITIALIZATION####################################

supportedInterfaces: map(bytes32, bool)
# https://eips.ethereum.org/EIPS/eip-165
ERC165_INTERFACE_ID: constant(bytes32)  = 0x0000000000000000000000000000000000000000000000000000000001ffc9a7
ERC1155_INTERFACE_ID: constant(bytes32) = 0x00000000000000000000000000000000000000000000000000000000d9b67a26
tokensIdCount: uint256
owner: public(address)

balancesOf: map(address, map(uint256, uint256))
noncesOf: map(address, map(uint256, bool))
uri: map(uint256, string[256])
operators: map(address, map(address, bool))
token_ids: map(uint256, bool)

# This is to be set before contract migration!
BATCH_SIZE: constant(uint256) = 10


@public
def __init__():
    """
    @notice Called once and only upon contract deployment.
    """
    self.tokensIdCount = convert(0, uint256)
    self.supportedInterfaces[ERC165_INTERFACE_ID] = True
    self.supportedInterfaces[ERC1155_INTERFACE_ID] = True
    self.owner = msg.sender

########################END-INITIALIZATION####################################
########################PRIVATE-FUNCTIONS####################################


######### THIS IS A TEMPORARY SOLUTION #################
@public
@constant
def getAddress(_addr: address) -> bytes32:
    hash: bytes32 = convert(_addr, bytes32)
    return hash
##################### END ##############################

@private
@constant
def _getHash(_from: address, _to: address, _ids: uint256[BATCH_SIZE], _from_supplies: uint256[BATCH_SIZE], _to_supplies: uint256[BATCH_SIZE], _value_eth: uint256, _nonce: uint256) -> bytes32:
    """
    @notice Get the hash from the tx values.
    @param _from          The address of the sender.
    @param _to            The address of the receiver.
    @param _ids           The ids of the tokens.
    @param _from_supplies The supply of token values that will send the _from.
    @param _to_supplies   The supply of token values that will send the _from.
    @param _value_eth     The value of the ether.
    @param _nonce         The nonce.
    @return the hash
    """
    aggregate_hash: bytes32 = keccak256(concat(convert(_ids[0], bytes32), convert(_from_supplies[0], bytes32), convert(_to_supplies[0], bytes32)))
    for i in range(BATCH_SIZE):
      if not i == 0:
        aggregate_hash = keccak256(concat(aggregate_hash, convert(_ids[i], bytes32), convert(_from_supplies[i], bytes32), convert(_to_supplies[i], bytes32)))
    hash: bytes32 = keccak256(concat(convert(_from, bytes32),
                              convert(_to, bytes32),
                              aggregate_hash,
                              convert(_value_eth, bytes32),
                              convert(_nonce, bytes32)))
    return hash


@public
@constant
def getHash(_from: address, _to: address, _ids: uint256[BATCH_SIZE], _from_supplies: uint256[BATCH_SIZE], _to_supplies: uint256[BATCH_SIZE], _value_eth: uint256, _nonce: uint256) -> bytes32:
    """
    @notice Get the hash from the tx values.
    @param _from          The address of the sender.
    @param _to            The address of the receiver.
    @param _ids           The ids of the tokens.
    @param _from_supplies The supply of token values that will send the _from.
    @param _to_supplies   The supply of token values that will send the _from.
    @param _value_eth     The value of the ether.
    @param _nonce         The nonce.
    @return the hash
    """
    return self._getHash(_from, _to, _ids, _from_supplies, _to_supplies, _value_eth, _nonce)


@private
@constant
def getHashOld(_from: address, _to: address, _ids: uint256[BATCH_SIZE], _from_supplies: uint256[BATCH_SIZE], _to_supplies: uint256[BATCH_SIZE], _value_eth: uint256, _nonce: uint256) -> bytes32:
    """
    @notice Get the hash from the tx values.
    @param _from          The address of the sender.
    @param _to            The address of the receiver.
    @param _ids           The ids of the tokens.
    @param _from_supplies The supply of token values that will send the _from.
    @param _to_supplies   The supply of token values that will send the _from.
    @param _value_eth     The value of the ether.
    @param _nonce         The nonce.
    @return the hash
    """
    hash: bytes32 = keccak256(concat(convert(_from, bytes32),
                              convert(_to, bytes32),
                              convert(_ids[0], bytes32),
                              convert(_ids[1], bytes32),
                              convert(_ids[2], bytes32),
                              convert(_ids[3], bytes32),
                              convert(_ids[4], bytes32),
                              convert(_ids[5], bytes32),
                              convert(_ids[6], bytes32),
                              convert(_ids[7], bytes32),
                              convert(_ids[8], bytes32),
                              convert(_ids[9], bytes32),
                              convert(_from_supplies[0], bytes32),
                              convert(_from_supplies[1], bytes32),
                              convert(_from_supplies[2], bytes32),
                              convert(_from_supplies[3], bytes32),
                              convert(_from_supplies[4], bytes32),
                              convert(_from_supplies[5], bytes32),
                              convert(_from_supplies[6], bytes32),
                              convert(_from_supplies[7], bytes32),
                              convert(_from_supplies[8], bytes32),
                              convert(_from_supplies[9], bytes32),
                              convert(_to_supplies[0], bytes32),
                              convert(_to_supplies[1], bytes32),
                              convert(_to_supplies[2], bytes32),
                              convert(_to_supplies[3], bytes32),
                              convert(_to_supplies[4], bytes32),
                              convert(_to_supplies[5], bytes32),
                              convert(_to_supplies[6], bytes32),
                              convert(_to_supplies[7], bytes32),
                              convert(_to_supplies[8], bytes32),
                              convert(_to_supplies[9], bytes32),
                              convert(_value_eth, bytes32),
                              convert(_nonce, bytes32)))
    return hash


@private
@constant
def _getSingleHash(_from: address, _to: address, _id: uint256, _from_supply: uint256, _to_supply: uint256, _value_eth: uint256, _nonce: uint256) -> bytes32:
    """
    @notice Get the hash from the tx values.
    @param _from            The address of the sender.
    @param _to              The address of the receiver.
    @param _id              The id of the tokens.
    @param _from_supply     The from token value. (_from sends)
    @param _to_supply       The to token value (_to sends).
    @param _value_eth       The value of the ether.
    @param _nonce           The nonce.
    @return the hash
    """
    hash: bytes32 = keccak256(concat(convert(_from, bytes32),
                              convert(_to, bytes32),
                              convert(_id, bytes32),
                              convert(_from_supply, bytes32),
                              convert(_to_supply, bytes32),
                              convert(_value_eth, bytes32),
                              convert(_nonce, bytes32)))
    return hash


@public
@constant
def getSingleHash(_from: address, _to: address, _id: uint256, _from_supply: uint256, _to_supply: uint256, _value_eth: uint256, _nonce: uint256) -> bytes32:
    """
    @notice Get the hash from the tx values.
    @param _from            The address of the sender.
    @param _to              The address of the receiver.
    @param _id              The id of the tokens.
    @param _from_supply     The from token value. (_from sends)
    @param _to_supply       The to token value (_to sends).
    @param _value_eth       The value of the ether.
    @param _nonce           The nonce.
    @return the hash
    """
    return self._getSingleHash(_from, _to, _id, _from_supply, _to_supply, _value_eth, _nonce)


@private
@constant
def ecrecoverSig(_hash: bytes32, _sig: bytes[65]) -> address:
    """
    @notice Check whether the the signature matches the hash.
    @param _hash The hash to be checked.
    @param _sig  The signature which is meant to match the hash.
    @return the address which signed the signature or the zero address
    """
    if len(_sig) != 65:
        return ZERO_ADDRESS
    # ref. https://gist.github.com/axic/5b33912c6f61ae6fd96d6c4a47afde6d
    # The signature format is a compact form of:
    # {bytes32 r}{bytes32 s}{uint8 v}
    r: bytes32 = extract32(_sig, 0, type=bytes32)
    s: bytes32 = extract32(_sig, 32, type=bytes32)
    v: int128 = convert(slice(_sig, start=64, len=1), int128)
    # Version of signature should be 27 or 28, but 0 and 1 are also possible versions.
    # geth uses [0, 1] and some clients have followed. This might change, see:
    # https://github.com/ethereum/go-ethereum/issues/2053
    if v < 27:
        v += 27
    if v in [27, 28]:
        return ecrecover(_hash, convert(v, uint256), convert(r, uint256), convert(s, uint256))
    return ZERO_ADDRESS


@private
@constant
def decode_id(id: uint256) -> int128:
    """
    @notice Decodes the id of the token inorder to find out if it NFT or FT.
    @param id: uint256
    @return token_id : int128 (Specified id for FT and NFT.)
    @dev shift(x, -y): returns x with the bits shifted to the right by y places, which is equivalent to dividing x by 2**y.
    """
    decoded_token_id: int128 = convert(shift(id, -128), int128)
    decoded_index: int128 = convert(id % 2 ** 128, int128)
    return decoded_token_id

########################END-PRIVATE-FUNCTIONS################################
########################PUBLIC-FUNCTIONS#####################################

@public
@constant
def supportsInterface(_interfaceID: bytes32) -> bool:
    """
    @notice Check whether the interface id is supported.
    @param _interfaceID The interface id
    @return True if the interface id is supported.
    """
    return self.supportedInterfaces[_interfaceID]

@public
@constant
def is_nonce_used(addr: address, nonce: uint256) -> bool:
    """
    @notice Checks if the given nonce for the give address is unused.
    @param nonce: uint256 the counter of the transaction
    @param address: the address that want to transact.
    """
    return self.noncesOf[addr][nonce]

@public
@constant
def is_token_id_exists(token_id: uint256) -> bool:
    """
    @notice Checks if the given token_id is already created.
    @param token_id: uint256 the id of the token.
    """
    return self.token_ids[token_id]

@public
def safeTransferFrom(_from: address, _to: address, _id: uint256, _value: uint256, _data: bytes[256]):
    """
    @notice Transfers `_value` amount of an `_id` from the `_from` address to the `_to` address specified (with safety call).
    @dev Caller must be approved to manage the tokens being transferred out of the `_from` account (see "Approval" section of the standard).
         MUST revert if `_to` is the zero address.
         MUST revert if balance of holder for token `_id` is lower than the `_value` sent.
         MUST revert on any other error.
         MUST emit the `TransferSingle` event to reflect the balance change (see "Safe Transfer Rules" section of the standard).
         After the above conditions are met, this function MUST check if `_to` is a smart contract (e.g. code size > 0). If so, it MUST call `onERC1155Received` on `_to` and act appropriately (see "Safe Transfer Rules" section of the standard).
    @param _from    Source address
    @param _to      Target address
    @param _id      ID of the token type
    @param _value   Transfer amount
    @param _data    Additional data with no specified format, MUST be sent unaltered in call to `onERC1155Received` on `_to`
    @return None
    """
    assert _from == msg.sender or (self.operators[_from])[msg.sender]
    assert _to != ZERO_ADDRESS, "Cannot transfer to zero address."
    assert self.balancesOf[_from][_id] >= _value, "Not enough tokens."

    self.balancesOf[_from][_id] -= _value
    self.balancesOf[_to][_id] += _value

    log.TransferSingle(msg.sender, _from, _to, _id, _value)

    if _to.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_to).onERC1155Received(msg.sender, _from, _id, _value, _data)
        assert returnValue == method_id("onERC1155Received(address,address,uint256,uint256,bytes)", bytes32)


@public
def safeBatchTransferFrom(_from: address, _to: address, _ids: uint256[BATCH_SIZE], _values: uint256[BATCH_SIZE], _data: bytes[256]):
    """
    @notice Transfers `_values` amount(s) of `_ids` from the `_from` address to the `_to` address specified (with safety call).
    @dev Caller must be approved to manage the tokens being transferred out of the `_from` account (see "Approval" section of the standard).
        MUST revert if `_to` is the zero address.
        MUST revert if length of `_ids` is not the same as length of `_values`.
        MUST revert if any of the balance(s) of the holder(s) for token(s) in `_ids` is lower than the respective amount(s) in `_values` sent to the recipient.
        MUST revert on any other error.
        MUST emit `TransferSingle` or `TransferBatch` event(s) such that all the balance changes are reflected (see "Safe Transfer Rules" section of the standard).
        Balance changes and events MUST follow the ordering of the arrays (_ids[0]/_values[0] before _ids[1]/_values[1], etc).
        After the above conditions for the transfer(s) in the batch are met, this function MUST check if `_to` is a smart contract (e.g. code size > 0). If so, it MUST call the relevant `ERC1155TokenReceiver` hook(s) on `_to` and act appropriately (see "Safe Transfer Rules" section of the standard).
    @param _from    Source address
    @param _to      Target address
    @param _ids     IDs of each token type (order and length must match _values array)
    @param _values  Transfer amounts per token type (order and length must match _ids array)
    @param _data    Additional data with no specified format, MUST be sent unaltered in call to the `ERC1155TokenReceiver` hook(s) on `_to`
    @return None
    """
    assert _from == msg.sender or (self.operators[_from])[msg.sender]
    assert _to != ZERO_ADDRESS, "Cannot transfer to zero address."
    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        assert self.balancesOf[_from][id] >= _values[i]

    log.TransferBatch(msg.sender, _from, _to, _ids, _values)

    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        self.balancesOf[_from][id] -= _values[i]
        self.balancesOf[_to][id] += _values[i]

    if _to.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_to).onERC1155BatchReceived(msg.sender, _from, _ids, _values, _data)
        assert returnValue == method_id("onERC1155BatchReceived(address,address,uint256[BATCH_SIZE],uint256[BATCH_SIZE],bytes)", bytes32)


@public
@constant
def balanceOf(_owner: address, _id: uint256) -> uint256:
    """
    @notice Get the balance of an account's tokens.
    @param  _owner The address of the token holder
    @param  _id    ID of the token
    @return The _owner's balance of the token type requested
    """
    return self.balancesOf[_owner][_id]


@public
@constant
def balanceOfBatch( _owner: address[BATCH_SIZE], _ids: uint256[BATCH_SIZE]) -> uint256[BATCH_SIZE]:
    """
    @notice Get the balance of multiple account/token pairs
    @param _owners The addresses of the token holders
    @param _ids    ID of the tokens
    @return The _owner's balance of the token types requested (i.e. balance for each (owner, id) pair)
    """
    returnBalances: uint256[BATCH_SIZE]
    for i in range(BATCH_SIZE):
        returnBalances[i] = self.balancesOf[_owner[i]][_ids[i]]
    return returnBalances


@public
def setApprovalForAll(_operator: address, _approved: bool):
    """
    @notice Enable or disable approval for a third party ("operator") to manage all of the caller's tokens.
    @dev MUST emit the ApprovalForAll event on success.
    @param _operator  Address to add to the set of authorized operators
    @param _approved  True if the operator is approved, false to revoke approval
    @return None
    """
    (self.operators[msg.sender])[_operator] = _approved
    log.ApprovalForAll(msg.sender, _operator, _approved)


@public
@constant
def isApprovedForAll(_owner: address, _operator: address) -> bool:
    """
    @notice Queries the approval status of an operator for a given owner.
    @param _owner     The owner of the tokens.
    @param _operator  Address of authorized operator.
    @return True if the operator is approved, false if not
    """
    return (self.operators[_owner])[_operator]


@public
def createSingle(_item_owner: address, _id: uint256, _path: string[256]):
    """
    @notice Create a new token type that we can mint later.
    @param _item_owner The owner of the item.
    @param _id         The id of the token.
    @param _path       The path to the token data.
    @return None
    """
    assert _item_owner != ZERO_ADDRESS
    assert self.owner == msg.sender, "Owner only can create item."
    self.balancesOf[_item_owner][_id] = 0
    self.tokensIdCount += 1
    self.token_ids[_id] = True
    self.uri[_id] = _path
    log.URI(_path, _id)
    log.TransferSingle(msg.sender, ZERO_ADDRESS, _item_owner, _id, 0)


@public
def createBatch(_items_owner: address, _ids: uint256[BATCH_SIZE]):
    """
    @notice Create new token types that we can mint later.
    @param _items_owner The owner of the items.
    @param _ids         The ids of the tokens.
    @return None
    """
    assert _items_owner != ZERO_ADDRESS
    assert self.owner == msg.sender, "Owner only can create items."
    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        self.balancesOf[_items_owner][id] = 0
        self.tokensIdCount += 1
        self.token_ids[id] = True
    zero_supply: uint256[BATCH_SIZE] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    log.TransferBatch(msg.sender, ZERO_ADDRESS, _items_owner, _ids, zero_supply)


@public
def mint(_to: address, _id: uint256, _supply: uint256, _data: bytes[256]=""):
    """
    @notice Mint a token.
    @dev This is not part of the standard.
    @param _to      The address of the receiver.
    @param _id      The id of the token.
    @param _supply  The supply to be minted for the token.
    @param _data    The data.
    @return None
    """
    assert _to != ZERO_ADDRESS
    assert self.owner == msg.sender, "Owner only can mint items."
    decoded_id: int128 = self.decode_id(_id)
    assert decoded_id == 1 or decoded_id == 2
    if decoded_id == 1 :
        assert _supply == 1, "Cannot mint NFT with _supply more than 1"
    self.balancesOf[_to][_id] = _supply

    log.TransferSingle(msg.sender, ZERO_ADDRESS, _to, _id, _supply)

    if _to.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_to).onERC1155Received(msg.sender, ZERO_ADDRESS, _id, _supply, _data)
        assert returnValue == method_id("onERC1155Received(address,address,uint256,uint256,bytes)", bytes32)


@public
def mintBatch(_to: address, _ids: uint256[BATCH_SIZE], _supplies: uint256[BATCH_SIZE], _data: bytes[256]=""):
    """
    @notice Mint a batch of tokens.
    @dev This is not part of the standard.
    @param _to      The address of the receiver.
    @param _ids     The ids of the tokens.
    @param _supplies The supply to be minted for each token.
    @param _data    The data.
    @return None
    """
    assert _to != ZERO_ADDRESS
    assert self.owner == msg.sender, "Owner only can mint items."

    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        decoded_id: int128 = self.decode_id(id)
        assert decoded_id == 1 or decoded_id == 2

        if decoded_id == 1 :
            assert _supplies[i] == 1

        self.balancesOf[_to][id] = _supplies[i]

    log.TransferBatch(msg.sender, ZERO_ADDRESS, _to, _ids, _supplies)

    for i in range(BATCH_SIZE):
        if _to.is_contract:
            returnValue: bytes32 = ERC1155TokenReceiver(_to).onERC1155Received(msg.sender, ZERO_ADDRESS, _ids[i], _supplies[i], _data)
            assert returnValue == method_id("onERC1155Received(address,address,uint256,uint256,bytes)", bytes32)


@public
def burn(_id: uint256, _supply: uint256):
    """
    @notice Burns the supply of the specified token.
    @param _id        The id of the token
    @param _supply    Supply to be burned
    @return None
    """
    assert self.balancesOf[msg.sender][_id] >= _supply, "Not enough tokens to burn."
    self.balancesOf[msg.sender][_id] -= _supply
    log.TransferSingle(msg.sender, msg.sender, ZERO_ADDRESS, _id, _supply)


@public
def burnBatch(_ids: uint256[BATCH_SIZE], _supplies: uint256[BATCH_SIZE]):
    """
    @notice Burns the supply of the specified tokens.
    @dev At this point anyone can burn items if they own it.
    @param _ids        The ids of the token
    @param _supplies   Supplies to be burned
    @return None
    """
    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        assert self.balancesOf[msg.sender][id] >= _supplies[i]

    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        self.balancesOf[msg.sender][id] -= _supplies[i]
    log.TransferBatch(msg.sender, msg.sender, ZERO_ADDRESS, _ids, _supplies)


@public
@payable
def tradeBatch(_from: address, _to: address, _ids: uint256[BATCH_SIZE], _from_supplies: uint256[BATCH_SIZE], _to_supplies: uint256[BATCH_SIZE], _value_eth: uint256, _nonce: uint256, _signature: bytes[65], _data: bytes[256]=""):
    """
    @notice Trade (atomically swap) tokens with tokens or eth.
    @dev Caller must be approved to manage the tokens being transferred out of the `_from` account (see "Approval" section of the standard).
        MUST revert if `_to` is the zero address.
        MUST revert if _from_supplies[i] > 0 and _to_supplies[i] > 0
        MUST revert if len(_ids) != len(_from_supplies) != len(_to_supplies)
        MUST revert if _value_eth != msg.value
        MUST revert if any of the balance(s) of the holder(s) for token(s) in `_ids` is lower than the respective amount(s) in `positive and negative values` sent to the recipient.
        MUST revert on any other error.
        MUST emit `TransferSingle` or `TransferBatch` event(s) such that all the balance changes are reflected (see "Safe Transfer Rules" section of the standard).
        Balance changes and events MUST follow the ordering of the arrays (_ids[0]/_values[0] before _ids[1]/_values[1], etc).
        After the above conditions for the transfer(s) in the batch are met, this function MUST check if `_to` is a smart contract (e.g. code size > 0). If so, it MUST call the relevant `ERC1155TokenReceiver` hook(s) on `_to` and act appropriately (see "Safe Transfer Rules" section of the standard).
    @param _from          The address of the sender.
    @param _to            The address of the receiver.
    @param _ids           The ids of the tokens.
    @param _from_supplies The supply of token values that will send the _from.
    @param _to_supplies   The supply of token values that will send the _from.
    @param _value_eth     The value of the ether.
    @param _nonce         The nonce.
    @param _signature    The signature of the _to address.
    @param _data    The data.
    @return None
    """
    # Assert the value of the transaction is less than the balance of A.

    assert _from == msg.sender or (self.operators[_from])[msg.sender], "_from must be the sender or approved address"
    assert _to != ZERO_ADDRESS, "Destination address must be non-zero."
    assert self.noncesOf[_from][_nonce] == False, "Nonce must be unused."
    assert _value_eth == msg.value, "Sender has not provided enough ether."

    for i in range(BATCH_SIZE):
       id: uint256 = _ids[i]
       if _from_supplies[i] > 0:
           assert _to_supplies[i] == 0
           assert self.balancesOf[_from][id] >= _from_supplies[i]
       else:
           assert _from_supplies[i] == 0
           assert self.balancesOf[_to][id] >= _to_supplies[i]

    # Create hash from variables.
    hash: bytes32 = self._getHash(_from, _to, _ids, _from_supplies, _to_supplies, _value_eth, _nonce)

    # Assert that the ecrecover(address,signature) returns true.
    recovered_to: address = self.ecrecoverSig(hash, _signature)
    assert recovered_to == _to, "Signer does not match signature."

    # Store the nonce
    self.noncesOf[msg.sender][_nonce] = True

    # Update the balances
    for i in range(BATCH_SIZE):
        id: uint256 = _ids[i]
        if _from_supplies[i] > 0:
            self.balancesOf[_from][id] -= _from_supplies[i]
            self.balancesOf[_to][id] += _from_supplies[i]
        else:
            self.balancesOf[_from][id] += _to_supplies[i]
            self.balancesOf[_to][id] -= _to_supplies[i]

    send(_to, msg.value)

    log.TransferBatch(msg.sender, _from, _to, _ids, _from_supplies)
    log.TransferBatch(msg.sender, _to, _from, _ids, _to_supplies)


    if _to.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_to).onERC1155BatchReceived(msg.sender, _to, _ids, _from_supplies, _data)
        assert returnValue == method_id("onERC1155BatchReceived(address,address,uint256,uint256,bytes)", bytes32)
    if _from.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_from).onERC1155BatchReceived(msg.sender, _from, _ids, _to_supplies, _data)
        assert returnValue == method_id("onERC1155BatchReceived(address,address,uint256,uint256,bytes)", bytes32)



@public
@payable
def trade(_from: address, _to: address, _id: uint256, _from_supply: uint256, _to_supply: uint256, _value_eth: uint256, _nonce: uint256, _signature: bytes[65], _data: bytes[256]=""):
    """
    @notice Trade (atomically swap) tokens with tokens or eth.
    @dev Caller must be approved to manage the tokens being transferred out of the `_from` account (see "Approval" section of the standard).
        MUST revert if `_to` is the zero address.
        MUST revert if _from_supply > 0 and _to_supply > 0
        MUST revert if _value_eth != msg.value
        MUST revert if any of the balance(s) of the holder(s) for token(s) in `_id` is lower than the respective amount in `positive or negative value` sent to the recipient.
        MUST revert on any other error.
        MUST emit `TransferSingle` or `TransferBatch` event(s) such that all the balance changes are reflected (see "Safe Transfer Rules" section of the standard).
        Balance changes and events MUST follow the ordering of the arrays (_ids[0]/_values[0] before _ids[1]/_values[1], etc).
        After the above conditions for the transfer(s) in the batch are met, this function MUST check if `_to` is a smart contract (e.g. code size > 0). If so, it MUST call the relevant `ERC1155TokenReceiver` hook(s) on `_to` and act appropriately (see "Safe Transfer Rules" section of the standard).
    @param _from            The from address (seller of eth, potential receiver of tokens).
    @param _to              The receiver address (receiver of tokens).
    @param _id              The id of the token
    @param _from_supply     The change in value of token (for _from)
    @param _to_supply       The change in value of token (for _to)
    @param _value_eth       The value of the ETH sent to the _from address.
    @param _nonce           The nonce.
    @param _signature       The signature of the _to address.
    @param _data    The data.
    @return None
    """
    # Assert the value of the transaction is less than the balance of A.
    assert _from == msg.sender or (self.operators[_from])[msg.sender]
    assert _to != ZERO_ADDRESS, "Destination address must be non-zero."
    assert self.noncesOf[_from][_nonce] == False, "Nonce must be unused."
    assert _value_eth == msg.value, "Sender has not provided enough ether."
    if _from_supply > 0:
        assert _to_supply == 0
        assert self.balancesOf[_from][_id] >= _from_supply
    else:
        assert _from_supply == 0
        assert self.balancesOf[_to][_id] >= _to_supply

    # Create hash from variables.
    hash: bytes32 = self._getSingleHash(_from, _to, _id, _from_supply, _to_supply, _value_eth, _nonce)

    # Assert that the ecrecover(address,signature) returns true.
    recovered_to: address = self.ecrecoverSig(hash, _signature)
    assert recovered_to == _to, "Signer does not match signature."

    # Store the nonce
    self.noncesOf[msg.sender][_nonce] = True

    # Update the balances
    if _from_supply > 0:
        self.balancesOf[_from][_id] -= _from_supply
        self.balancesOf[_to][_id] += _from_supply
    else:
        self.balancesOf[_from][_id] += _to_supply
        self.balancesOf[_to][_id] -= _to_supply

    send(_to, msg.value)

    log.TransferSingle(msg.sender, _from, _to, _id, _from_supply)
    log.TransferSingle(msg.sender, _to, _from, _id, _to_supply)

    if _to.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_to).onERC1155Received(msg.sender, _to, _id, _from_supply, _data)
        assert returnValue == method_id("onERC1155BatchReceived(address,address,uint256,uint256,bytes)", bytes32)
    if _from.is_contract:
        returnValue: bytes32 = ERC1155TokenReceiver(_from).onERC1155Received(msg.sender, _from, _id, _to_supply, _data)
        assert returnValue == method_id("onERC1155BatchReceived(address,address,uint256,uint256,bytes)", bytes32)
