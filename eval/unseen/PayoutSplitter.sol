// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Members join freely; anyone can trigger an equal split of the contract balance.
contract PayoutSplitter {
    address[] public members;
    mapping(address => bool) public isMember;

    receive() external payable {}

    function join() external {
        require(!isMember[msg.sender], "already member");
        isMember[msg.sender] = true;
        members.push(msg.sender);
    }

    function distribute() external {
        uint256 count = members.length;
        require(count > 0, "no members");
        uint256 share = address(this).balance / count;
        for (uint256 i = 0; i < count; i++) {
            (bool ok,) = members[i].call{value: share}("");
            require(ok, "payout failed");
        }
    }
}
