package com.example.payment;

public class CreditCard implements Payable {
    private double balance;

    @Override
    public void pay(double amount) {
        this.balance -= amount;
    }

    @Override
    public String getReceipt() {
        return "CreditCard receipt";
    }
}
