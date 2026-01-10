package com.bank.service;

import com.bank.model.Account;
import java.util.List;
import java.util.Map;

/**
 * Transaction service with various naming violations.
 */
public class TransactionService {

    // R2: Misleading name - it's a Map, not a List
    private Map<String, Account> accountList;

    // R2: Another misleading collection name
    private List<String> transactionMap;  // It's actually a List!

    // R1: Generic names that don't reveal purpose
    private Object helper;
    private Object manager;
    private Object handler;

    // R3: Meaningless numeric suffixes
    private String value1;
    private String value2;
    private String result1;
    private String result2;

    // Good names
    private Map<String, Account> accountsByNumber;
    private List<String> transactionIds;

    /**
     * R1: What does this method do? Name doesn't tell us.
     */
    public void handle(Object o) {
        // Completely unclear
    }

    /**
     * R1: Another vague method
     */
    public Object get() {
        return null;
    }

    /**
     * R6: Single-letter variables in non-loop context
     */
    public double calculate(double a, double b, double c) {
        double x = a + b;
        double y = x * c;
        double z = y / 2;
        return z;
    }

    /**
     * Better version with meaningful names
     */
    public double calculateCompoundInterest(
            double principal,
            double interestRate,
            double years) {
        double accumulated = principal * Math.pow(1 + interestRate, years);
        return accumulated - principal;
    }

    /**
     * R4: Unpronounceable abbreviations
     */
    public void prcTxn(String txnId, double amt, String acctNbr) {
        // Process transaction - but the name is cryptic
    }

    /**
     * Good: Pronounceable and clear
     */
    public void processTransaction(
            String transactionId,
            double amount,
            String accountNumber) {
        // Clear what this does
    }

    /**
     * R5: Type encoding in method name
     */
    public String getAccountString() {
        return "";
    }

    public Integer getBalanceInteger() {
        return 0;
    }

    public Boolean getIsActiveBoolean() {
        return true;
    }

    /**
     * R8: Too generic, missing context
     */
    public void execute() {
        // Execute what?
    }

    public void run() {
        // Run what?
    }

    public void perform() {
        // Perform what action?
    }

    /**
     * Good: Context-aware naming
     */
    public void executeMonthlyInterestCalculation() {
        // Clear intent
    }

    public void runFraudDetectionCheck() {
        // Specific purpose
    }

    public void performBalanceReconciliation() {
        // Descriptive action
    }
}
