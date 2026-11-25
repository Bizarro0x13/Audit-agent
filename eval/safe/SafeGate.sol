// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeGate {
    address public immutable operator;
    mapping(address => bool) public allowed;
    address public lastEntrant;

    event AllowedSet(address indexed who, bool ok);

    constructor() {
        operator = msg.sender;
    }

    function setAllowed(address who, bool ok) external {
        require(msg.sender == operator, "not operator");
        allowed[who] = ok;
        emit AllowedSet(who, ok);
    }

    function enter() external {
        require(allowed[msg.sender], "not allowed");
        lastEntrant = msg.sender;
    }
}
