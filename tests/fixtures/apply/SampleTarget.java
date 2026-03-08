package com.bank.repository;

import java.util.List;

public interface AccountRepository {
    List<Account> findAll();
    Account save(Account a);
    void delete(String id);
    Account findById(String id);
    void updateStatus(Account a, String s);
}
