package com.bank.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import javax.persistence.Entity;
import javax.persistence.Id;

/**
 * Customer entity with naming issues.
 */
@Entity
public class Customer {

    @Id
    private Long id;

    // R9: Spanish/Spanglish names
    private String nombre;  // Should be: firstName
    private String apellido;  // Should be: lastName
    private String direccion;  // Should be: address

    // R5: Interface prefix pattern (wrong for class field)
    private String ICustomerType;

    // R3: Noise words
    private String theCustomerName;
    private String aCustomerAddress;

    // R1: Vague names
    private Object obj;
    private String str;
    private Integer num;

    // R4: Consonant clusters - hard to pronounce
    private String cstmrPrfl;  // customerProfile
    private String txnHstry;   // transactionHistory

    private String phoneNumber;
    private String emailAddress;

    // Guardrail: JsonProperty - should NOT be renamed
    @JsonProperty("customer_id")
    private String customerId;

    @JsonProperty("full_name")
    private String fullName;

    // R7: Inconsistent terminology (mix of get/fetch/retrieve)
    public String getName() {
        return nombre;
    }

    public String fetchAddress() {  // Should use get* like above
        return direccion;
    }

    public String retrievePhone() {  // Another inconsistency
        return phoneNumber;
    }

    // R8: Missing context - too generic
    public void update() {
        // Update what?
    }

    public void validate() {
        // Validate what aspect?
    }

    public boolean validateEmailFormat() {
        return emailAddress != null && emailAddress.contains("@");
    }
}
