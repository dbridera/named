# Named Analysis Report

**Generated**: 2026-01-23 10:10:58
**Project**: `/Users/danielbridera/Work/named/samples/banking-app`
**Model**: gpt-4o

---

## Summary

| Metric | Value |
|--------|-------|
| Total Symbols Analyzed | 224 |
| Suggestions Generated | 127 |
| Valid Suggestions | 95 |
| Blocked by Guardrails | 0 |

## Violations by Rule

| Rule | Count |
|------|-------|
| R1_REVEAL_INTENT | 104 |
| R2_NO_DISINFORMATION | 4 |
| R3_MEANINGFUL_DISTINCTIONS | 15 |
| R4_PRONOUNCEABLE | 12 |
| R5_NO_TYPE_ENCODING | 13 |
| R6_NO_MENTAL_MAPPING | 25 |
| R7_ONE_WORD_PER_CONCEPT | 7 |
| R8_CONTEXT_NAMING | 1 |
| R9_CORRECT_LANGUAGE | 3 |

## Rename Impact Analysis

This section shows which files will be affected by each suggested rename.

### Impact Distribution

| Risk Level | Count | Percentage |
|------------|-------|------------|
| High (11+) | 0 | 0% |
| Medium (4-10) | 0 | 0% |
| Low (1-3) | 127 | 100% |

**Total unique files affected**: 5 files across all suggestions

---

### Low Impact Changes (1-3 files)

**127 low-impact changes** affecting 1-3 files each.

<details>
<summary>Click to expand low-impact changes</summary>

- `findAll` → `findAllAccounts` (method, 0 files, 95%)
- `save` → `saveAccount` (method, 0 files, 95%)
- `delete` → `deleteAccount` (method, 0 files, 95%)
- `getData` → `getAccountList` (method, 0 files, 95%)
- `getInfo` → `getAccountDetails` (method, 0 files, 95%)
- `getByAccountNumber` → `findByAccountNumber` (method, 0 files, 95%)
- `fetchByCustomerId` → `findByCustomerId` (method, 0 files, 95%)
- `retrieveByEmail` → `findByEmail` (method, 0 files, 95%)
- `findAccountList` → `findAccountByCriteria` (method, 0 files, 95%)
- `pg` → `pageNumber` (parameter, 0 files, 95%)
- `updateStatus` → `updateAccountStatus` (method, 0 files, 95%)
- `a` → `status` (parameter, 1 files, 95%)
- `s` → `status` (parameter, 1 files, 95%)
- `findTheAccountByTheId` → `findAccountById` (method, 0 files, 95%)
- `theId` → `accountId` (parameter, 0 files, 95%)
- `getAllTheAccounts` → `getAllAccounts` (method, 0 files, 95%)
- `getAccountNumberString` → `getAccountNumber` (method, 0 files, 95%)
- `getBalanceLong` → `getBalance` (method, 0 files, 95%)
- `RATE` → `interestRate` (constant, 0 files, 95%)
- `genymdhms` → `generationTimestamp` (field, 0 files, 95%)

*... and 107 more*

</details>

## Recommended Changes (High Confidence)

These suggestions have confidence >= 0.85 and should be safe to apply.

### `findAll` → `findAllAccounts`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'findAllAccounts' clearly indicates that the method retrieves all Account objects, improving clarity and intent.
- **Rules Addressed**: R1_REVEAL_INTENT

### `save` → `saveAccount`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'saveAccount' clearly indicates that the method is responsible for saving an Account object, providing better context and intent.
- **Rules Addressed**: R1_REVEAL_INTENT

### `delete` → `deleteAccount`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'deleteAccount' clearly indicates that the method is responsible for deleting an 'Account' object, making the purpose of the method explicit and self-explanatory.
- **Rules Addressed**: R1_REVEAL_INTENT

### `getData` → `getAccountList`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getAccountList' clearly indicates that the method returns a list of accounts, which is more descriptive and aligns with the context provided.
- **Rules Addressed**: R1_REVEAL_INTENT

### `getInfo` → `getAccountDetails`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getAccountDetails' clearly indicates that the method retrieves specific details related to an account, aligning with the context of the surrounding code.
- **Rules Addressed**: R1_REVEAL_INTENT

### `getByAccountNumber` → `findByAccountNumber`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: Using 'find' aligns with other method names in the context, providing consistency and clarity.
- **Rules Addressed**: R7_ONE_WORD_PER_CONCEPT

### `fetchByCustomerId` → `findByCustomerId`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: Using 'find' aligns with the naming convention used in similar methods like 'findByPhoneNumber', ensuring consistency and clarity.
- **Rules Addressed**: R7_ONE_WORD_PER_CONCEPT

### `retrieveByEmail` → `findByEmail`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: Using 'findByEmail' aligns with the naming convention used by other similar methods like 'findByPhoneNumber', ensuring consistency and clarity.
- **Rules Addressed**: R7_ONE_WORD_PER_CONCEPT

### `findAccountList` → `findAccountByCriteria`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'findAccountByCriteria' clearly indicates that the method finds a single account based on the provided criteria, addressing both the disinformation and intent issues.
- **Rules Addressed**: R1_REVEAL_INTENT, R2_NO_DISINFORMATION

### `pg` → `pageNumber`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'pageNumber' clearly indicates the purpose of the parameter, which is likely related to pagination in the searchAccounts method.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `updateStatus` → `updateAccountStatus`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'updateAccountStatus' is more descriptive and clearly indicates that the method updates the status of an account, addressing the need for clarity and specificity.
- **Rules Addressed**: R1_REVEAL_INTENT

### `a` → `status`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'status' provides clarity about the parameter's purpose in the method 'updateStatus', improving code readability and intent revelation.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:51 → `double x = a + b;`

### `s` → `status`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'status' clearly indicates the purpose of the parameter in the context of the method 'updateStatus', addressing R1_REVEAL_INTENT.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - PaymentController.java:69 → `return s;`

### `findTheAccountByTheId` → `findAccountById`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The suggested name 'findAccountById' is more concise and removes redundant words, making it clearer and more aligned with Java naming conventions.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `theId` → `accountId`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'accountId' is more specific and reveals the intent by indicating that the ID is associated with an account, which aligns with the method name 'findTheAccountByTheId'.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `getAllTheAccounts` → `getAllAccounts`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getAllAccounts' is concise and clearly indicates the method's purpose of retrieving all accounts without unnecessary semantic noise.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `getAccountNumberString` → `getAccountNumber`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: Removing the type encoding 'String' aligns with Java naming conventions and makes the method name more concise and clear.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `getBalanceLong` → `getBalance`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The suggested name 'getBalance' removes type encoding, making it more aligned with Java naming conventions and focusing on the method's purpose rather than its return type.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `RATE` → `interestRate`

- **Kind**: constant
- **Confidence**: 95%
- **Rationale**: The name 'interestRate' provides clear context and intent, indicating that the constant likely represents an interest rate, which is more descriptive and meaningful.
- **Rules Addressed**: R1_REVEAL_INTENT

### `genymdhms` → `generationTimestamp`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'generationTimestamp' is more descriptive and easier to understand, indicating that it likely represents a timestamp related to generation, which addresses the clarity and pronunciation issues.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `modymdhms` → `modificationTimestamp`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'modificationTimestamp' is clear and self-explanatory, indicating it likely stores a timestamp related to a modification event.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `l` → `dataList`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'dataList' provides a clearer understanding of the field's purpose, assuming it holds a list of data elements.
- **Rules Addressed**: R6_NO_MENTAL_MAPPING, R1_REVEAL_INTENT

### `check` → `isValueNonNull`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'isValueNonNull' clearly indicates that the method checks if the provided value is not null, making the purpose of the method explicit.
- **Rules Addressed**: R1_REVEAL_INTENT

### `data` → `formattedContent`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'formattedContent' provides a clearer indication of the parameter's purpose in the context of a method named 'format'.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - PaymentController.java:73 → `return data != null;`

### `theRequest` → `request`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'request' is concise and directly conveys the parameter's purpose without unnecessary semantic noise.
- **Rules Addressed**: R3_MEANINGFUL_DISTINCTIONS

### `strFormat` → `formatString`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'formatString' removes type encoding and better describes the method's purpose, aligning with Java naming conventions.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `intParse` → `parseInteger`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'parseInteger' avoids type encoding and clearly describes the method's purpose of parsing a String into an Integer.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `boolCheck` → `isNotNull`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'isNotNull' clearly indicates that the method checks if an object is not null, which aligns with its functionality.
- **Rules Addressed**: R1_REVEAL_INTENT, R5_NO_TYPE_ENCODING

### `dateString` → `transactionDate`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'transactionDate' reveals the purpose of the parameter without encoding the type, aligning with R1_REVEAL_INTENT and R5_NO_TYPE_ENCODING.
- **Rules Addressed**: R1_REVEAL_INTENT, R5_NO_TYPE_ENCODING

### `makeActive` → `activate`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'activate' aligns with the consistent terminology used in similar methods such as 'activateAccount', providing clarity and consistency.
- **Rules Addressed**: R7_ONE_WORD_PER_CONCEPT

### `obj` → `account`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'account' is more descriptive and likely aligns with the method's purpose of making something active, which could be an account. This name provides better context and intent.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `setInactive` → `deactivate`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'deactivate' aligns with the consistent pattern of activate/deactivate used in similar methods, improving clarity and consistency.
- **Rules Addressed**: R7_ONE_WORD_PER_CONCEPT

### `doEnable` → `enableObject`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'enableObject' clearly indicates the action being performed and aligns with the enable/disable terminology used in the code context.
- **Rules Addressed**: R1_REVEAL_INTENT

### `performDisable` → `disable`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'disable' aligns with the concept of enabling/disabling, providing consistency with 'doEnable'.
- **Rules Addressed**: R7_ONE_WORD_PER_CONCEPT

### `nombre` → `customerName`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerName' is in English and clearly indicates that it represents the name of a customer, addressing both the language and context issues.
- **Rules Addressed**: R1_REVEAL_INTENT, R9_CORRECT_LANGUAGE
- **Used in 1 location(s)**:
  - Customer.java:52 → `return nombre;`

### `apellido` → `lastName`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'lastName' is in English and clearly indicates the field's purpose, aligning with Java naming conventions.
- **Rules Addressed**: R9_CORRECT_LANGUAGE

### `direccion` → `address`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'address' is in English and clearly indicates that the field stores an address, aligning with Java naming conventions.
- **Rules Addressed**: R1_REVEAL_INTENT, R9_CORRECT_LANGUAGE
- **Used in 1 location(s)**:
  - Customer.java:56 → `return direccion;`

### `ICustomerType` → `customerType`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerType' removes the type encoding prefix 'I' and clearly describes the field's purpose without implying an interface.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `theCustomerName` → `customerName`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerName' is more concise and removes unnecessary semantic noise, aligning with Java naming conventions.
- **Rules Addressed**: R3_MEANINGFUL_DISTINCTIONS

### `aCustomerAddress` → `customerAddress`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerAddress' is more concise and removes the unnecessary article, making it clearer and more meaningful.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `obj` → `customerData`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerData' provides a clearer indication of the field's purpose, assuming it holds data related to a customer, thus addressing the intent revelation issue.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `str` → `customerName`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerName' provides clear intent about the field's purpose, likely representing a customer's name, and removes type encoding.
- **Rules Addressed**: R5_NO_TYPE_ENCODING, R6_NO_MENTAL_MAPPING

### `num` → `customerNumber`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerNumber' clearly indicates that the field likely represents a unique identifier or number associated with a customer, aligning with the context of the Customer class.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `cstmrPrfl` → `customerProfile`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'customerProfile' is clear, self-explanatory, and easy to pronounce, improving readability and understanding of the code.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `txnHstry` → `transactionHistory`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'transactionHistory' is more descriptive and easy to understand, clearly indicating that the field stores a history of transactions.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `retrievePhone` → `getPhoneNumber`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getPhoneNumber' clearly indicates that the method retrieves a phone number, aligning with Java naming conventions and improving clarity.
- **Rules Addressed**: R1_REVEAL_INTENT

### `update` → `updateAccountDetails`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'updateAccountDetails' provides clear intent by specifying what is being updated, which aligns with the method's purpose.
- **Rules Addressed**: R1_REVEAL_INTENT

### `data` → `accountDetails`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'accountDetails' provides a clearer understanding of what the field represents in the context of an Account, addressing the need for intent-revealing names.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - PaymentController.java:73 → `return data != null;`

### `info` → `accountDetails`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'accountDetails' provides a clearer understanding of what information the field holds, aligning with the context of an Account.
- **Rules Addressed**: R1_REVEAL_INTENT

### `bal` → `balance`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'balance' is clear and self-explanatory, indicating that the field represents the account balance.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 4 location(s)**:
  - Account.java:59 → `this.bal = amt;`
  - Account.java:88 → `return bal;`
  - Account.java:92 → `this.bal = bal;`
  - Account.java:92 → `this.bal = bal;`

### `accountTypeString` → `accountType`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'accountType' is clear and concise, removing unnecessary type encoding while still conveying the purpose of the field.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `boolIsActive` → `isActive`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'isActive' removes the type encoding and clearly indicates that the field is a boolean representing whether the account is active.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `x` → `balance`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'balance' provides clear intent and context within an 'Account' class, indicating it likely represents the account balance.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:52 → `double y = x * c;`

### `tmp` → `temporaryBalance`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'temporaryBalance' provides clear intent that the field is used to store a balance temporarily, aligning with the context of an Account.
- **Rules Addressed**: R1_REVEAL_INTENT

### `doIt` → `executeTask`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'executeTask' provides a clearer indication of the method's purpose, suggesting that it performs a specific task, which aligns with R1_REVEAL_INTENT.
- **Rules Addressed**: R1_REVEAL_INTENT

### `updAcctBal` → `updateAccountBalance`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'updateAccountBalance' is clear, pronounceable, and explicitly describes the method's functionality, addressing both R1_REVEAL_INTENT and R4_PRONOUNCEABLE.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `amt` → `amount`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'amount' is clear and self-explanatory, indicating that it represents a monetary value to be used in updating the account balance.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - Account.java:59 → `this.bal = amt;`

### `transfer` → `transferFunds`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'transferFunds' clearly indicates that the method is responsible for transferring monetary funds, improving clarity and intent.
- **Rules Addressed**: R1_REVEAL_INTENT

### `a` → `amount`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'amount' clearly indicates that the parameter likely represents a monetary value involved in the transfer, which improves readability and understanding.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:51 → `double x = a + b;`

### `b` → `balance`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'balance' is more descriptive and indicates that the parameter likely represents a monetary balance involved in the transfer method.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:51 → `double x = a + b;`

### `setAcctNum` → `setAccountNumber`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'setAccountNumber' is clear and self-explanatory, revealing the method's purpose to set the account number. It addresses the issues of abbreviation and pronunciation.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `acctNum` → `accountNumber`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'accountNumber' is more descriptive and self-explanatory, clearly indicating that the parameter represents an account number.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 3 location(s)**:
  - Account.java:80 → `return acctNum;`
  - Account.java:84 → `this.acctNum = acctNum;`
  - Account.java:84 → `this.acctNum = acctNum;`

### `getBal` → `getBalance`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getBalance' clearly indicates that the method retrieves the balance, making it more understandable and pronounceable.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `setBal` → `setBalance`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'setBalance' clearly indicates that the method is setting a balance value, which improves readability and understanding.
- **Rules Addressed**: R1_REVEAL_INTENT

### `bal` → `balance`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'balance' is more descriptive and clearly indicates that the parameter represents a balance, eliminating the need for mental mapping.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 4 location(s)**:
  - Account.java:59 → `this.bal = amt;`
  - Account.java:88 → `return bal;`
  - Account.java:92 → `this.bal = bal;`
  - Account.java:92 → `this.bal = bal;`

### `manager` → `transactionManager`

- **Kind**: field
- **Confidence**: 95%
- **Rationale**: The name 'transactionManager' provides clearer intent by specifying that the manager is related to transactions, aligning with the context of TransactionService.
- **Rules Addressed**: R1_REVEAL_INTENT

### `a` → `amount`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'amount' provides context and clarity, indicating the parameter's likely role in a calculation.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:51 → `double x = a + b;`

### `b` → `balance`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'balance' provides clear context and intent, aligning with the method 'calculate' which likely involves financial calculations.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:51 → `double x = a + b;`

### `prcTxn` → `processTransaction`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'processTransaction' clearly describes the method's purpose, making it more understandable and pronounceable.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `txnId` → `transactionId`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'transactionId' is more descriptive and self-explanatory, making it clear that the parameter represents an identifier for a transaction.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `amt` → `amount`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'amount' is more descriptive and self-explanatory, clearly indicating that the parameter represents an amount, likely of money or quantity.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - Account.java:59 → `this.bal = amt;`

### `acctNbr` → `accountNumber`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'accountNumber' is clear, self-explanatory, and easily pronounceable, which improves code readability and maintainability.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `getAccountString` → `getAccountDetails`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getAccountDetails' removes the type encoding and better describes the method's purpose, addressing R5_NO_TYPE_ENCODING and R1_REVEAL_INTENT.
- **Rules Addressed**: R5_NO_TYPE_ENCODING, R1_REVEAL_INTENT

### `getBalanceInteger` → `getBalance`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'getBalance' is clear and concise, avoiding type encoding while maintaining the method's purpose.
- **Rules Addressed**: R5_NO_TYPE_ENCODING

### `getIsActiveBoolean` → `isActive`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'isActive' removes type encoding and clearly indicates the method's purpose of checking or returning an active status.
- **Rules Addressed**: R1_REVEAL_INTENT, R5_NO_TYPE_ENCODING

### `perform` → `calculateMonthlyInterest`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The suggested name 'calculateMonthlyInterest' clearly indicates the specific action being performed, aligning with the example provided and improving clarity.
- **Rules Addressed**: R1_REVEAL_INTENT

### `data` → `customerData`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'customerData' provides more context about the data being handled, suggesting it relates to customer information, which aligns with the method name 'create'.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - PaymentController.java:73 → `return data != null;`

### `obj` → `updateData`

- **Kind**: parameter
- **Confidence**: 95%
- **Rationale**: The name 'updateData' clearly indicates that the parameter is related to the data being updated, which improves the readability and intent of the code.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `proc` → `processData`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'processData' clearly indicates that the method is intended to process some data, addressing the need for clarity and intent.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `fmt` → `formatString`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'formatString' is more descriptive and self-explanatory, addressing the purpose of the method to format a string.
- **Rules Addressed**: R4_PRONOUNCEABLE, R6_NO_MENTAL_MAPPING

### `chk` → `isDataValid`

- **Kind**: method
- **Confidence**: 95%
- **Rationale**: The name 'isDataValid' clearly indicates that the method checks if the data is valid, addressing both the pronounceability issue and revealing the method's intent.
- **Rules Addressed**: R1_REVEAL_INTENT, R4_PRONOUNCEABLE

### `criteria` → `accountSearchCriteria`

- **Kind**: parameter
- **Confidence**: 92%
- **Rationale**: The name 'accountSearchCriteria' provides a clearer indication of the parameter's purpose, specifying that it is used for searching accounts, thus addressing the intent revelation issue.
- **Rules Addressed**: R1_REVEAL_INTENT

### `convert` → `convertToTargetType`

- **Kind**: method
- **Confidence**: 92%
- **Rationale**: The name 'convertToTargetType' provides more context about the method's purpose, indicating that it converts the input to a specific target type, which aligns with R1_REVEAL_INTENT.
- **Rules Addressed**: R1_REVEAL_INTENT

### `value` → `amountToCheck`

- **Kind**: parameter
- **Confidence**: 92%
- **Rationale**: The name 'amountToCheck' provides more context about the parameter's purpose in the 'check' method, making it clear that it represents an amount to be verified.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:48 → `return value != null;`

### `processTheData` → `transformInputData`

- **Kind**: method
- **Confidence**: 92%
- **Rationale**: The name 'transformInputData' is more specific and descriptive, indicating the method's purpose of transforming the input data.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `result2` → `transactionOutcome`

- **Kind**: field
- **Confidence**: 92%
- **Rationale**: The name 'transactionOutcome' clearly indicates the field's purpose in the context of a TransactionService, providing a meaningful distinction from other potential results.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `run` → `executeTransaction`

- **Kind**: method
- **Confidence**: 92%
- **Rationale**: The name 'executeTransaction' provides clear intent by specifying that the method is executing a transaction, which is more informative and context-aware.
- **Rules Addressed**: R1_REVEAL_INTENT

### `q` → `query`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'query' provides a clearer indication of the parameter's purpose in the context of a search operation.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `sz` → `searchZone`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'searchZone' provides a clearer indication of the parameter's role in the method, improving readability and understanding.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `status` → `accountStatus`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'accountStatus' is more descriptive and indicates that the status pertains to an account, aligning with the method's purpose.
- **Rules Addressed**: R1_REVEAL_INTENT

### `DataHelper` → `CustomerDataProcessor`

- **Kind**: class
- **Confidence**: 90%
- **Rationale**: The name 'CustomerDataProcessor' suggests that the class is responsible for processing customer-related data, providing clear intent and context.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `MAX` → `MAX_DATA_ENTRIES`

- **Kind**: constant
- **Confidence**: 90%
- **Rationale**: The name 'MAX_DATA_ENTRIES' provides clarity on what the maximum value pertains to, specifically indicating it is related to data entries in the context of DataHelper.
- **Rules Addressed**: R1_REVEAL_INTENT

### `DEFAULT` → `DEFAULT_DATA_FORMAT`

- **Kind**: constant
- **Confidence**: 90%
- **Rationale**: The name 'DEFAULT_DATA_FORMAT' provides a clearer understanding of what the default value is related to, assuming it pertains to data formatting in DataHelper.
- **Rules Addressed**: R1_REVEAL_INTENT

### `n` → `numberOfRecords`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'numberOfRecords' provides clear intent and context, indicating what the field represents.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `s` → `status`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'status' provides a clearer understanding of what the field might represent, improving code readability and maintainability.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - PaymentController.java:69 → `return s;`

### `o` → `dataObject`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'dataObject' provides more context and intent, indicating that it holds a data-related object, which is more descriptive than a single-letter variable.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `init` → `initializeApplication`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: The name 'initializeApplication' provides a clearer understanding of what the method is intended to do, assuming it initializes the application or a major component of it.
- **Rules Addressed**: R1_REVEAL_INTENT

### `input` → `sourceData`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'sourceData' provides more context about the parameter's role in the conversion process, indicating that it is the data to be converted.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 3 location(s)**:
  - DataHelper.java:43 → `return input;`
  - DataHelper.java:67 → `return input;`
  - DataHelper.java:71 → `return Integer.parseInt(input);`

### `format` → `formatToString`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: The name 'formatToString' clearly indicates that the method is formatting the object to a string representation, which aligns with the method's functionality.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:80 → `return String.format("$%.2f", amount);`

### `theData` → `customerData`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'customerData' is more descriptive and indicates the type of data being processed, aligning with the method's likely purpose.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS
- **Used in 1 location(s)**:
  - DataHelper.java:58 → `return theData;`

### `handleTheRequest` → `processClientRequest`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: The suggested name 'processClientRequest' is more specific and descriptive, indicating that the method processes a client request, thus revealing its intent more clearly.
- **Rules Addressed**: R1_REVEAL_INTENT

### `input` → `formatString`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'formatString' clearly indicates that the parameter is a string used for formatting, aligning with the method name 'strFormat'.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 3 location(s)**:
  - DataHelper.java:43 → `return input;`
  - DataHelper.java:67 → `return input;`
  - DataHelper.java:71 → `return Integer.parseInt(input);`

### `input` → `numberString`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'numberString' clearly indicates that the parameter is expected to be a string representing a number, aligning with the method's purpose of parsing an integer.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 3 location(s)**:
  - DataHelper.java:43 → `return input;`
  - DataHelper.java:67 → `return input;`
  - DataHelper.java:71 → `return Integer.parseInt(input);`

### `obj` → `condition`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'condition' suggests that the parameter is used to evaluate a boolean condition, which aligns with the method name 'boolCheck'.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `obj` → `inactiveReason`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'inactiveReason' provides clarity on what the parameter is used for in the context of the 'setInactive' method.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `obj` → `targetObject`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'targetObject' provides more context about the parameter's role in the method, indicating it is the object being enabled.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `obj` → `targetObject`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'targetObject' provides more context about the parameter's role in the method 'performDisable', indicating that it is the object being acted upon.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - DataHelper.java:75 → `return obj != null;`

### `fetchAddress` → `getAddress`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: Using 'getAddress' aligns with common naming conventions for accessor methods and maintains consistency with similar methods, providing clearer intent.
- **Rules Addressed**: R8_CONTEXT_NAMING, R7_ONE_WORD_PER_CONCEPT

### `validate` → `validateUserInput`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: The name 'validateUserInput' provides a clearer understanding of what aspect is being validated, aligning with the method's likely purpose.
- **Rules Addressed**: R1_REVEAL_INTENT

### `accountData` → `accountDetails`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'accountDetails' provides a clearer indication of the field's purpose, suggesting it contains detailed information about the account.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `accountInfo` → `accountDetails`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'accountDetails' provides a clearer indication of what the field represents, suggesting it contains detailed information about the account.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `accountList` → `accounts`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'accounts' is more descriptive and avoids implying a specific data structure, aligning with R2_NO_DISINFORMATION.
- **Rules Addressed**: R2_NO_DISINFORMATION

### `transactionMap` → `transactionsById`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'transactionsById' clearly indicates that the map is used to store transactions indexed by their ID, revealing its purpose and usage more explicitly.
- **Rules Addressed**: R1_REVEAL_INTENT, R2_NO_DISINFORMATION

### `helper` → `transactionHelper`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'transactionHelper' provides more context by indicating that the helper is related to transactions, aligning with the class 'TransactionService'.
- **Rules Addressed**: R1_REVEAL_INTENT

### `handler` → `transactionProcessor`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'transactionProcessor' more clearly indicates that this field is responsible for processing transactions, aligning with the purpose of TransactionService.
- **Rules Addressed**: R1_REVEAL_INTENT

### `value1` → `transactionAmount`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'transactionAmount' is more descriptive and indicates that the field likely holds a monetary value related to a transaction, which aligns with the context of being in a TransactionService.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `value2` → `transactionAmount`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'transactionAmount' provides clear context and intent, indicating that the field likely represents a monetary value associated with a transaction.
- **Rules Addressed**: R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS

### `result1` → `transactionResult`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'transactionResult' provides a clear indication that the field is related to the outcome or result of a transaction, aligning with the context of TransactionService.
- **Rules Addressed**: R3_MEANINGFUL_DISTINCTIONS

### `accountsByNumber` → `accountMapByNumber`

- **Kind**: field
- **Confidence**: 90%
- **Rationale**: The name 'accountMapByNumber' clearly indicates that this field is a Map, which aligns with the likely usage context in a service class dealing with transactions.
- **Rules Addressed**: R2_NO_DISINFORMATION

### `handle` → `processRequest`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: The name 'processRequest' provides a clearer indication of the method's purpose, suggesting it processes a specific type of request.
- **Rules Addressed**: R1_REVEAL_INTENT

### `o` → `operation`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'operation' provides more context about the parameter's purpose, aligning with R1_REVEAL_INTENT.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING

### `c` → `calculationInput`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'calculationInput' provides clarity on the purpose of the parameter, aligning with R1_REVEAL_INTENT by indicating that it is an input for a calculation.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - TransactionService.java:52 → `double y = x * c;`

### `execute` → `executeTransaction`

- **Kind**: method
- **Confidence**: 90%
- **Rationale**: The name 'executeTransaction' provides a clearer indication of the method's purpose, assuming it is related to processing a transaction in a banking context.
- **Rules Addressed**: R1_REVEAL_INTENT

### `o` → `operation`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'operation' provides a clearer understanding of the parameter's purpose, improving readability and maintainability.
- **Rules Addressed**: R6_NO_MENTAL_MAPPING, R1_REVEAL_INTENT

### `s` → `formatString`

- **Kind**: parameter
- **Confidence**: 90%
- **Rationale**: The name 'formatString' provides clarity on the expected type and purpose of the parameter, aligning with R1_REVEAL_INTENT by indicating that it is a string used for formatting.
- **Rules Addressed**: R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING
- **Used in 1 location(s)**:
  - PaymentController.java:69 → `return s;`

### `get` → `getObject`

- **Kind**: method
- **Confidence**: 85%
- **Rationale**: The name 'getObject' provides more context about the method's purpose, suggesting it retrieves an object, which is more informative than 'get'.
- **Rules Addressed**: R1_REVEAL_INTENT

### `data` → `inputData`

- **Kind**: parameter
- **Confidence**: 85%
- **Rationale**: The name 'inputData' provides more context about the parameter being input to the method, which is more descriptive than just 'data'.
- **Rules Addressed**: R1_REVEAL_INTENT
- **Used in 1 location(s)**:
  - PaymentController.java:73 → `return data != null;`

## All Valid Suggestions

| Original | Suggested | Kind | Confidence | Rules |
|----------|-----------|------|------------|-------|
| `findAll` | `findAllAccounts` | method | 95% | R1_REVEAL_INTENT |
| `save` | `saveAccount` | method | 95% | R1_REVEAL_INTENT |
| `delete` | `deleteAccount` | method | 95% | R1_REVEAL_INTENT |
| `getInfo` | `getAccountDetails` | method | 95% | R1_REVEAL_INTENT |
| `getByAccountNumber` | `findByAccountNumber` | method | 95% | R7_ONE_WORD_PER_CONCEPT |
| `fetchByCustomerId` | `findByCustomerId` | method | 95% | R7_ONE_WORD_PER_CONCEPT |
| `retrieveByEmail` | `findByEmail` | method | 95% | R7_ONE_WORD_PER_CONCEPT |
| `findAccountList` | `findAccountByCriteria` | method | 95% | R1_REVEAL_INTENT, R2_NO_DISINFORMATION |
| `pg` | `pageNumber` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `updateStatus` | `updateAccountStatus` | method | 95% | R1_REVEAL_INTENT |
| `a` | `status` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `s` | `status` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `findTheAccountByTheId` | `findAccountById` | method | 95% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `theId` | `accountId` | parameter | 95% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `getAllTheAccounts` | `getAllAccounts` | method | 95% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `getAccountNumberString` | `getAccountNumber` | method | 95% | R5_NO_TYPE_ENCODING |
| `getBalanceLong` | `getBalance` | method | 95% | R5_NO_TYPE_ENCODING |
| `RATE` | `interestRate` | constant | 95% | R1_REVEAL_INTENT |
| `genymdhms` | `generationTimestamp` | field | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `modymdhms` | `modificationTimestamp` | field | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `check` | `isValueNonNull` | method | 95% | R1_REVEAL_INTENT |
| `data` | `formattedContent` | parameter | 95% | R1_REVEAL_INTENT |
| `theRequest` | `request` | parameter | 95% | R3_MEANINGFUL_DISTINCTIONS |
| `boolCheck` | `isNotNull` | method | 95% | R1_REVEAL_INTENT, R5_NO_TYPE_ENCODING |
| `dateString` | `transactionDate` | parameter | 95% | R1_REVEAL_INTENT, R5_NO_TYPE_ENCODING |
| `makeActive` | `activate` | method | 95% | R7_ONE_WORD_PER_CONCEPT |
| `obj` | `account` | parameter | 95% | R1_REVEAL_INTENT |
| `setInactive` | `deactivate` | method | 95% | R7_ONE_WORD_PER_CONCEPT |
| `performDisable` | `disable` | method | 95% | R7_ONE_WORD_PER_CONCEPT |
| `nombre` | `customerName` | field | 95% | R1_REVEAL_INTENT, R9_CORRECT_LANGUAGE |
| `apellido` | `lastName` | field | 95% | R9_CORRECT_LANGUAGE |
| `direccion` | `address` | field | 95% | R1_REVEAL_INTENT, R9_CORRECT_LANGUAGE |
| `ICustomerType` | `customerType` | field | 95% | R5_NO_TYPE_ENCODING |
| `theCustomerName` | `customerName` | field | 95% | R3_MEANINGFUL_DISTINCTIONS |
| `aCustomerAddress` | `customerAddress` | field | 95% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `str` | `customerName` | field | 95% | R5_NO_TYPE_ENCODING, R6_NO_MENTAL_MAPPING |
| `num` | `customerNumber` | field | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `cstmrPrfl` | `customerProfile` | field | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `txnHstry` | `transactionHistory` | field | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `retrievePhone` | `getPhoneNumber` | method | 95% | R1_REVEAL_INTENT |
| `update` | `updateAccountDetails` | method | 95% | R1_REVEAL_INTENT |
| `data` | `accountDetails` | field | 95% | R1_REVEAL_INTENT |
| `info` | `accountDetails` | field | 95% | R1_REVEAL_INTENT |
| `bal` | `balance` | field | 95% | R1_REVEAL_INTENT |
| `accountTypeString` | `accountType` | field | 95% | R5_NO_TYPE_ENCODING |
| `boolIsActive` | `isActive` | field | 95% | R5_NO_TYPE_ENCODING |
| `x` | `balance` | field | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `doIt` | `executeTask` | method | 95% | R1_REVEAL_INTENT |
| `updAcctBal` | `updateAccountBalance` | method | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `amt` | `amount` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `transfer` | `transferFunds` | method | 95% | R1_REVEAL_INTENT |
| `a` | `amount` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `b` | `balance` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `setAcctNum` | `setAccountNumber` | method | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `acctNum` | `accountNumber` | parameter | 95% | R1_REVEAL_INTENT |
| `getBal` | `getBalance` | method | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `setBal` | `setBalance` | method | 95% | R1_REVEAL_INTENT |
| `bal` | `balance` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `a` | `amount` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `b` | `balance` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `txnId` | `transactionId` | parameter | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `amt` | `amount` | parameter | 95% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `acctNbr` | `accountNumber` | parameter | 95% | R1_REVEAL_INTENT, R4_PRONOUNCEABLE |
| `getAccountString` | `getAccountDetails` | method | 95% | R5_NO_TYPE_ENCODING, R1_REVEAL_INTENT |
| `getBalanceInteger` | `getBalance` | method | 95% | R5_NO_TYPE_ENCODING |
| `getIsActiveBoolean` | `isActive` | method | 95% | R1_REVEAL_INTENT, R5_NO_TYPE_ENCODING |
| `perform` | `calculateMonthlyInterest` | method | 95% | R1_REVEAL_INTENT |
| `criteria` | `accountSearchCriteria` | parameter | 92% | R1_REVEAL_INTENT |
| `convert` | `convertToTargetType` | method | 92% | R1_REVEAL_INTENT |
| `value` | `amountToCheck` | parameter | 92% | R1_REVEAL_INTENT |
| `result2` | `transactionOutcome` | field | 92% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `run` | `executeTransaction` | method | 92% | R1_REVEAL_INTENT |
| `q` | `query` | parameter | 90% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `sz` | `searchZone` | parameter | 90% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `status` | `accountStatus` | parameter | 90% | R1_REVEAL_INTENT |
| `n` | `numberOfRecords` | field | 90% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `s` | `status` | field | 90% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `init` | `initializeApplication` | method | 90% | R1_REVEAL_INTENT |
| `obj` | `condition` | parameter | 90% | R1_REVEAL_INTENT |
| `obj` | `inactiveReason` | parameter | 90% | R1_REVEAL_INTENT |
| `fetchAddress` | `getAddress` | method | 90% | R8_CONTEXT_NAMING, R7_ONE_WORD_PER_CONCEPT |
| `validate` | `validateUserInput` | method | 90% | R1_REVEAL_INTENT |
| `accountData` | `accountDetails` | field | 90% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `accountInfo` | `accountDetails` | field | 90% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `accountList` | `accounts` | field | 90% | R2_NO_DISINFORMATION |
| `transactionMap` | `transactionsById` | field | 90% | R1_REVEAL_INTENT, R2_NO_DISINFORMATION |
| `handler` | `transactionProcessor` | field | 90% | R1_REVEAL_INTENT |
| `value1` | `transactionAmount` | field | 90% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `value2` | `transactionAmount` | field | 90% | R1_REVEAL_INTENT, R3_MEANINGFUL_DISTINCTIONS |
| `result1` | `transactionResult` | field | 90% | R3_MEANINGFUL_DISTINCTIONS |
| `accountsByNumber` | `accountMapByNumber` | field | 90% | R2_NO_DISINFORMATION |
| `o` | `operation` | parameter | 90% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `c` | `calculationInput` | parameter | 90% | R1_REVEAL_INTENT, R6_NO_MENTAL_MAPPING |
| `execute` | `executeTransaction` | method | 90% | R1_REVEAL_INTENT |
| `o` | `operation` | parameter | 90% | R6_NO_MENTAL_MAPPING, R1_REVEAL_INTENT |

---

*Report generated by [Named](https://github.com/your-org/named) - Intelligent Java Code Refactoring System*
