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
     * R4: Unpronounceable abbreviations
     */
    public void prcTxn(String txnId, double amt, String acctNbr) {
        // Process transaction - but the name is cryptic
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
}
