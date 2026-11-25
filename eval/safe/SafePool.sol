// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
}

contract SafePool {
    IERC20 public immutable tokenA;
    IERC20 public immutable tokenB;
    address public immutable owner;
    uint256 public reserveA;
    uint256 public reserveB;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "reentered");
        locked = true;
        _;
        locked = false;
    }

    constructor(IERC20 a, IERC20 b) {
        require(address(a) != address(b), "same token");
        tokenA = a;
        tokenB = b;
        owner = msg.sender;
    }

    function seed(uint256 amountA, uint256 amountB) external nonReentrant {
        require(msg.sender == owner, "not owner");
        require(reserveA == 0 && reserveB == 0, "already seeded");
        require(amountA > 0 && amountB > 0, "zero amount");
        reserveA = _pull(tokenA, amountA);
        reserveB = _pull(tokenB, amountB);
    }

    function swap(address tokenIn, uint256 amountIn, uint256 minOut) external nonReentrant returns (uint256 out) {
        require(tokenIn == address(tokenA) || tokenIn == address(tokenB), "bad token");
        bool aIn = tokenIn == address(tokenA);
        (IERC20 inToken, IERC20 outToken) = aIn ? (tokenA, tokenB) : (tokenB, tokenA);
        (uint256 rIn, uint256 rOut) = aIn ? (reserveA, reserveB) : (reserveB, reserveA);
        require(rIn > 0 && rOut > 0, "no liquidity");

        uint256 received = _pull(inToken, amountIn);
        uint256 inWithFee = received * 997;
        out = (inWithFee * rOut) / (rIn * 1000 + inWithFee);
        require(out > 0 && out >= minOut, "slippage");

        if (aIn) {
            reserveA = rIn + received;
            reserveB = rOut - out;
        } else {
            reserveB = rIn + received;
            reserveA = rOut - out;
        }
        _call(address(outToken), abi.encodeCall(IERC20.transfer, (msg.sender, out)));
    }

    function _pull(IERC20 token, uint256 amount) private returns (uint256 received) {
        uint256 before = token.balanceOf(address(this));
        _call(address(token), abi.encodeCall(IERC20.transferFrom, (msg.sender, address(this), amount)));
        received = token.balanceOf(address(this)) - before;
    }

    function _call(address target, bytes memory data) private {
        (bool ok, bytes memory ret) = target.call(data);
        require(ok && (ret.length == 0 || abi.decode(ret, (bool))), "token call failed");
    }
}
