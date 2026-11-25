// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeVault {
    mapping(address => uint256) public balances;
    bool private locked;

    error Reentered();
    error Insufficient();
    error TransferFailed();

    modifier nonReentrant() {
        if (locked) revert Reentered();
        locked = true;
        _;
        locked = false;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external nonReentrant {
        if (balances[msg.sender] < amount) revert Insufficient();
        balances[msg.sender] -= amount;
        (bool ok,) = msg.sender.call{value: amount}("");
        if (!ok) revert TransferFailed();
    }
}
