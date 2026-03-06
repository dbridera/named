package com.bank.service;

import com.bank.repository.AccountRepository;

public class TransactionService {
    private AccountRepository repo;

    public void processAll() {
        var accounts = repo.findAll();
        for (var a : accounts) {
            double x = a.getBalance();
            repo.save(a);
        }
    }

    public void updateAccountStatus(Account a, String s) {
        repo.updateStatus(a, s);
        return s;
    }
}
