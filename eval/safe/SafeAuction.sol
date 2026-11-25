// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeAuction {
    address public immutable seller;
    uint256 public immutable endTime;
    address public highestBidder;
    uint256 public highestBid;
    bool public settled;
    mapping(address => uint256) public pendingReturns;

    constructor(uint256 duration) {
        seller = msg.sender;
        endTime = block.timestamp + duration;
    }

    function bid() external payable {
        require(block.timestamp < endTime, "ended");
        require(msg.value > highestBid, "bid too low");
        if (highestBidder != address(0)) {
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
    }

    function withdrawRefund() external {
        uint256 amount = pendingReturns[msg.sender];
        require(amount > 0, "nothing to withdraw");
        pendingReturns[msg.sender] = 0;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
    }

    function settle() external {
        require(block.timestamp >= endTime, "not ended");
        require(!settled, "already settled");
        settled = true;
        (bool ok,) = seller.call{value: highestBid}("");
        require(ok, "transfer failed");
    }
}
