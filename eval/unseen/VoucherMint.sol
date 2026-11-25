// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// The signer issues off-chain vouchers; holders redeem them for ETH.
contract VoucherMint {
    address public immutable signer;
    mapping(bytes32 => bool) public redeemed;

    constructor(address signer_) payable {
        require(signer_ != address(0), "zero signer");
        signer = signer_;
    }

    function redeem(address payable to, uint256 amount, uint256 nonce, uint8 v, bytes32 r, bytes32 s) external {
        bytes32 digest = keccak256(abi.encodePacked(to, amount, nonce));
        bytes32 prefixed = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", digest));
        require(ecrecover(prefixed, v, r, s) == signer, "bad signature");
        require(!redeemed[digest], "already redeemed");
        redeemed[digest] = true;
        (bool ok,) = to.call{value: amount}("");
        require(ok, "transfer failed");
    }
}
