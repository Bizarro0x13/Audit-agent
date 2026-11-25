// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeVoucher {
    address public admin;
    mapping(address => uint256) public credits;

    event Granted(address indexed to, uint256 amount);
    event Spent(address indexed account, address indexed origin, uint256 amount);

    constructor(address _admin) {
        admin = _admin;
    }

    function grant(address to, uint256 amount) external {
        require(msg.sender == admin, "not admin");
        credits[to] += amount;
        emit Granted(to, amount);
    }

    function spend(uint256 amount) external {
        require(credits[msg.sender] >= amount, "insufficient");
        credits[msg.sender] -= amount;
        emit Spent(msg.sender, tx.origin, amount);
    }

    function changeAdmin(address next) external {
        require(msg.sender == admin, "not admin");
        admin = next;
    }
}
