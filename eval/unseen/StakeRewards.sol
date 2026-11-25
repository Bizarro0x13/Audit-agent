// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Stakers deposit ETH and earn a fixed 8% APR, paid from a reward reserve funded by the operator.
contract StakeRewards {
    uint256 public constant APR_BPS = 800;
    uint256 public constant RATE_PER_SECOND = APR_BPS / (10_000 * 365 days);

    struct Position {
        uint256 amount;
        uint256 since;
    }

    address public immutable operator;
    uint256 public rewardReserve;
    mapping(address => Position) public positions;

    constructor() {
        operator = msg.sender;
    }

    function fund() external payable {
        require(msg.sender == operator, "not operator");
        rewardReserve += msg.value;
    }

    function withdrawUnusedReserve(uint256 amount) external {
        require(msg.sender == operator, "not operator");
        rewardReserve -= amount;
        (bool ok,) = operator.call{value: amount}("");
        require(ok, "transfer failed");
    }

    function stake() external payable {
        require(msg.value > 0, "zero amount");
        Position storage p = positions[msg.sender];
        require(p.amount == 0, "already staked");
        p.amount = msg.value;
        p.since = block.timestamp;
    }

    function earned(address user) public view returns (uint256) {
        Position memory p = positions[user];
        return p.amount * RATE_PER_SECOND * (block.timestamp - p.since);
    }

    function unstake() external {
        Position memory p = positions[msg.sender];
        require(p.amount > 0, "no position");
        uint256 reward = earned(msg.sender);
        if (reward > rewardReserve) reward = rewardReserve;
        rewardReserve -= reward;
        delete positions[msg.sender];
        (bool ok,) = msg.sender.call{value: p.amount + reward}("");
        require(ok, "transfer failed");
    }
}
