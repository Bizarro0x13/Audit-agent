// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IClaimReceiver {
    function onClaim(address operator, uint256 amount) external returns (bytes4);
}

/// Eligible accounts each claim a fixed amount of a capped airdrop supply, once.
contract AirdropClaim {
    uint256 public constant CLAIM_AMOUNT = 100e18;
    uint256 public constant MAX_SUPPLY = 10_000e18;

    address public immutable admin;
    uint256 public totalClaimed;
    mapping(address => uint256) public balanceOf;
    mapping(address => bool) public eligible;
    mapping(address => bool) public claimed;

    constructor() {
        admin = msg.sender;
    }

    function setEligible(address[] calldata accounts) external {
        require(msg.sender == admin, "not admin");
        for (uint256 i = 0; i < accounts.length; i++) {
            eligible[accounts[i]] = true;
        }
    }

    function claim() external {
        require(eligible[msg.sender], "not eligible");
        require(!claimed[msg.sender], "already claimed");
        require(totalClaimed + CLAIM_AMOUNT <= MAX_SUPPLY, "airdrop exhausted");
        totalClaimed += CLAIM_AMOUNT;
        balanceOf[msg.sender] += CLAIM_AMOUNT;
        _notify(msg.sender, CLAIM_AMOUNT);
        claimed[msg.sender] = true;
    }

    function _notify(address to, uint256 amount) private {
        if (to.code.length == 0) return;
        bytes4 answer = IClaimReceiver(to).onClaim(msg.sender, amount);
        require(answer == IClaimReceiver.onClaim.selector, "receiver rejected");
    }
}
