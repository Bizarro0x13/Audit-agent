// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeEscrow {
    struct Deal {
        address buyer;
        address seller;
        uint256 amount;
        uint256 deadline;
        bool closed;
    }

    Deal[] public deals;

    function open(address seller, uint256 duration) external payable returns (uint256 id) {
        require(msg.value > 0, "no value");
        require(duration >= 1 days && duration <= 90 days, "bad duration");
        deals.push(Deal(msg.sender, seller, msg.value, block.timestamp + duration, false));
        id = deals.length - 1;
    }

    function release(uint256 id) external {
        Deal storage d = deals[id];
        require(msg.sender == d.buyer, "not buyer");
        require(!d.closed, "closed");
        d.closed = true;
        (bool ok,) = d.seller.call{value: d.amount}("");
        require(ok, "transfer failed");
    }

    function refund(uint256 id) external {
        Deal storage d = deals[id];
        require(msg.sender == d.buyer, "not buyer");
        require(!d.closed, "closed");
        require(block.timestamp >= d.deadline, "too early");
        d.closed = true;
        (bool ok,) = d.buyer.call{value: d.amount}("");
        require(ok, "transfer failed");
    }
}
