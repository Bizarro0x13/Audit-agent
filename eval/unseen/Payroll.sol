// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IToken {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address who) external view returns (uint256);
}

/// The employer funds this contract with the payroll token and schedules payments.
/// Anyone may trigger a scheduled payment so that payees do not depend on the employer.
contract Payroll {
    struct Payment {
        address payee;
        uint256 amount;
        bool paid;
    }

    IToken public immutable token;
    address public immutable employer;
    Payment[] public payments;

    constructor(IToken token_) {
        token = token_;
        employer = msg.sender;
    }

    function schedule(address payee, uint256 amount) external returns (uint256 id) {
        require(msg.sender == employer, "not employer");
        payments.push(Payment(payee, amount, false));
        id = payments.length - 1;
    }

    function pay(uint256 id) external {
        Payment storage p = payments[id];
        require(!p.paid, "already paid");
        p.paid = true;
        token.transfer(p.payee, p.amount);
    }
}
