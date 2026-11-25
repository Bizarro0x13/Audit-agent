// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ShareVault {
    uint256 public totalShares;
    mapping(address => uint256) public shares;

    function totalAssets() public view returns (uint256) {
        return address(this).balance;
    }

    function deposit() external payable returns (uint256 minted) {
        require(msg.value > 0, "zero amount");
        uint256 assetsBefore = totalAssets() - msg.value;
        minted = totalShares == 0 ? msg.value : (msg.value * totalShares) / assetsBefore;
        shares[msg.sender] += minted;
        totalShares += minted;
    }

    function redeem(uint256 amount) external {
        require(shares[msg.sender] >= amount, "insufficient shares");
        uint256 assets = (amount * totalAssets()) / totalShares;
        shares[msg.sender] -= amount;
        totalShares -= amount;
        (bool ok,) = msg.sender.call{value: assets}("");
        require(ok, "transfer failed");
    }
}
