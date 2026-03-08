package com.bank.repository;

import com.bank.model.Account;
import java.util.List;
import java.util.Optional;

/**
 * Repository interface demonstrating naming conventions.
 * Standard CRUD methods (findById, findAll, save, delete) are well-named
 * and should NOT be renamed. The other methods demonstrate naming violations.
 */
public interface AccountRepository {

    // Standard repository methods (good names, no rename needed)
    Optional<Account> findById(Long id);
    List<Account> findAll();
    Account save(Account account);
    void delete(Account account);

    // R1: Vague query method names
    List<Account> getData();  // Get what data?
    Object getInfo();         // What info?

    // R7: Inconsistent naming - mixing find/get/fetch/retrieve
    Account getByAccountNumber(String accountNumber);
    Account fetchByCustomerId(Long customerId);
    Account retrieveByEmail(String email);
    // Should all use the same prefix (preferably 'find')

    // R2: Misleading return type in name
    // Method says "List" but returns single Account
    Account findAccountList(String criteria);

    // R4: Abbreviated parameter names
    List<Account> searchAccounts(String q, int pg, int sz);
    // Better: query, page, pageSize

    // R6: Single letter in method signature
    void updateStatus(Account a, String s);
    // Better: account, status

    // R3: Noise words
    Account findTheAccountByTheId(Long theId);
    List<Account> getAllTheAccounts();

    // R5: Type in method name
    String getAccountNumberString(Long accountId);
    Long getBalanceLong(String accountNumber);

    Optional<Account> findByAccountNumberAndStatus(String accountNumber, String status);
}
