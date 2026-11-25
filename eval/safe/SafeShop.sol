// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeShop {
    address public immutable seller;
    uint256 public immutable price;
    bool public isSold;
    address public buyer;

    constructor(uint256 price_) {
        seller = msg.sender;
        price = price_;
    }

    function buy() external payable {
        require(!isSold, "sold");
        require(msg.value >= price, "too low");
        isSold = true;
        buyer = msg.sender;
        uint256 excess = msg.value - price;
        if (excess > 0) {
            (bool ok,) = msg.sender.call{value: excess}("");
            require(ok, "refund failed");
        }
    }

    function withdraw() external {
        require(msg.sender == seller, "not seller");
        (bool ok,) = seller.call{value: address(this).balance}("");
        require(ok, "transfer failed");
    }
}
