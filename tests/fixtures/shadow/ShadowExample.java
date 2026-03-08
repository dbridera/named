package com.example.shadow;

public class ShadowExample {
    private double bal;
    private String data;

    public double getBalance() {
        double amount = bal * 1.1;
        return amount;
    }

    public void setBalance(double newBal) {
        this.bal = newBal;
    }

    public void processData() {
        String result = data.toUpperCase();
        System.out.println(result);
    }
}
