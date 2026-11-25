// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeRegistry {
    address public owner;
    address public pendingOwner;
    mapping(bytes32 => address) public records;

    error NotOwner();
    error NotPending();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function transferOwnership(address next) external onlyOwner {
        pendingOwner = next;
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert NotPending();
        owner = msg.sender;
        pendingOwner = address(0);
    }

    function register(bytes32 name) external {
        require(records[name] == address(0), "taken");
        records[name] = msg.sender;
    }

    function release(bytes32 name) external {
        require(records[name] == msg.sender, "not yours");
        delete records[name];
    }

    receive() external payable {
        revert("no direct payments");
    }
}
