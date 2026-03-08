package com.example.payment;

public interface Payable {
    void pay(double amount);
    String getReceipt();
}
