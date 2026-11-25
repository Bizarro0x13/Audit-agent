// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeDecoder {
    bytes4 private constant SET_LEVEL = bytes4(keccak256("setLevel(uint256)"));
    address public immutable controller;
    uint256 public level;

    constructor() {
        controller = msg.sender;
    }

    function execute(bytes calldata data) external {
        require(msg.sender == controller, "not controller");
        require(data.length == 36, "bad length");
        require(bytes4(data[:4]) == SET_LEVEL, "bad selector");
        uint256 newLevel = abi.decode(data[4:], (uint256));
        require(newLevel <= 10, "too high");
        level = newLevel;
    }
}
