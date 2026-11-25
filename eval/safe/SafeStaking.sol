// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
}

contract SafeStaking {
    IERC20 public immutable token;
    mapping(address => uint256) public staked;
    uint256 public totalStaked;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "reentered");
        locked = true;
        _;
        locked = false;
    }

    constructor(IERC20 token_) {
        token = token_;
    }

    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "zero amount");
        uint256 before = token.balanceOf(address(this));
        _call(abi.encodeCall(IERC20.transferFrom, (msg.sender, address(this), amount)));
        uint256 received = token.balanceOf(address(this)) - before;
        staked[msg.sender] += received;
        totalStaked += received;
    }

    function unstake(uint256 amount) external nonReentrant {
        require(staked[msg.sender] >= amount, "insufficient stake");
        staked[msg.sender] -= amount;
        totalStaked -= amount;
        _call(abi.encodeCall(IERC20.transfer, (msg.sender, amount)));
    }

    function _call(bytes memory data) private {
        (bool ok, bytes memory ret) = address(token).call(data);
        require(ok && (ret.length == 0 || abi.decode(ret, (bool))), "token call failed");
    }
}
