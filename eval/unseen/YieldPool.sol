// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract YieldPool {
    uint256 private constant PRECISION = 1e18;

    uint256 public totalStaked;
    uint256 public accRewardPerShare;
    mapping(address => uint256) public staked;
    mapping(address => uint256) public rewardDebt;

    function stake() external payable {
        require(msg.value > 0, "zero amount");
        staked[msg.sender] += msg.value;
        totalStaked += msg.value;
    }

    function notifyReward() external payable {
        require(totalStaked > 0, "no stakers");
        accRewardPerShare += (msg.value * PRECISION) / totalStaked;
    }

    function pending(address user) public view returns (uint256) {
        return (staked[user] * accRewardPerShare) / PRECISION - rewardDebt[user];
    }

    function claim() external {
        uint256 owed = pending(msg.sender);
        rewardDebt[msg.sender] = (staked[msg.sender] * accRewardPerShare) / PRECISION;
        _send(msg.sender, owed);
    }

    function withdraw(uint256 amount) external {
        require(staked[msg.sender] >= amount, "insufficient stake");
        uint256 owed = pending(msg.sender);
        staked[msg.sender] -= amount;
        totalStaked -= amount;
        rewardDebt[msg.sender] = (staked[msg.sender] * accRewardPerShare) / PRECISION;
        _send(msg.sender, owed + amount);
    }

    function _send(address to, uint256 amount) private {
        (bool ok,) = to.call{value: amount}("");
        require(ok, "transfer failed");
    }
}
