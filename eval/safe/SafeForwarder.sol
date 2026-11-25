// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CounterLogic {
    address public owner;
    uint256 public counter;

    function increment() external {
        counter += 1;
    }
}

contract SafeForwarder {
    address public owner;
    uint256 public counter;
    address public immutable logic;

    constructor(address logic_) {
        owner = msg.sender;
        logic = logic_;
    }

    function increment() external {
        (bool ok,) = logic.delegatecall(abi.encodeWithSignature("increment()"));
        require(ok, "delegate failed");
    }
}
