// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeToken {
    mapping(address => uint256) public balanceOf;
    uint256 public immutable totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);

    error InsufficientBalance();

    constructor(uint256 supply) {
        totalSupply = supply;
        balanceOf[msg.sender] = supply;
        emit Transfer(address(0), msg.sender, supply);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        if (balanceOf[msg.sender] < value) revert InsufficientBalance();
        unchecked {
            balanceOf[msg.sender] -= value;
        }
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
