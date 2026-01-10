package com.bank.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

/**
 * Account entity - demonstrates naming violations and guardrails.
 */
@Entity
@Table(name = "accounts")
public class Account {

    @Id
    @Column(name = "account_id")
    private Long id;  // OK - short but standard for ID

    @Column(name = "account_number")
    private String acctNum;  // R4: Not pronounceable

    private String data;  // R1: Generic name, doesn't reveal intent

    private String info;  // R1: Generic name

    private Double bal;  // R4: Abbreviation, R1: unclear intent

    private String accountTypeString;  // R5: Type encoding in name

    private Boolean boolIsActive;  // R5: Hungarian notation

    private String x;  // R6: Single letter variable

    private String tmp;  // R1: Generic temporary name

    // R3: Meaningless distinctions
    private String accountData;
    private String accountInfo;

    // Good names
    private String ownerName;
    private String emailAddress;
    private Double currentBalance;

    public Account() {}

    // R1: Method name doesn't reveal intent
    public void process() {
        // What does this process?
    }

    // R1: Another generic name
    public Object doIt() {
        return null;
    }

    // R4: Unpronounceable method name
    public void updAcctBal(Double amt) {
        this.bal = amt;
    }

    // Good method name
    public void depositAmount(Double amount) {
        this.currentBalance += amount;
    }

    // R6: Single letter parameters
    public void transfer(Account a, Double b) {
        // a and b don't explain anything
    }

    // Good parameter names
    public void transferFunds(Account targetAccount, Double transferAmount) {
        // Clear and descriptive
    }

    // Getters and setters with guardrails (should not be renamed)
    @Column(name = "account_number")
    public String getAcctNum() {
        return acctNum;
    }

    public void setAcctNum(String acctNum) {
        this.acctNum = acctNum;
    }

    public Double getBal() {
        return bal;
    }

    public void setBal(Double bal) {
        this.bal = bal;
    }
}
