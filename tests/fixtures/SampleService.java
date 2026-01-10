package com.example.service;

import javax.ws.rs.Path;
import javax.ws.rs.GET;
import javax.ws.rs.QueryParam;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Sample service for testing Named analyzer.
 * Contains intentional naming violations for testing.
 */
@Path("/api/users")
public class SampleService {

    // Violation: R1_REVEAL_INTENT - generic name "data"
    private String data;

    // Violation: R3_MEANINGFUL_DISTINCTIONS - noise word "Info"
    private CustomerInfo customerInfo;

    // Violation: R5_NO_TYPE_ENCODING - type in name
    private String phoneString;

    // Good: Descriptive constant name
    public static final int MAX_RETRY_ATTEMPTS = 3;

    // Violation: R4_PRONOUNCEABLE - hard to pronounce
    private String cstmrRcrd;

    // Blocked by G1: Has @JsonProperty annotation
    @JsonProperty("user_name")
    private String userName;

    // Violation: R6_NO_MENTAL_MAPPING - single letter variable
    private int n;

    /**
     * Process data - violation: vague method name
     */
    public void processData(String info) {
        // Violation: R6 - single letter in loop (but 'i' is allowed)
        for (int i = 0; i < 10; i++) {
            // Violation: R6 - 'x' is not allowed
            int x = i * 2;
            System.out.println(x);
        }
    }

    // Blocked by G3: REST endpoint annotation
    @GET
    @Path("/list")
    public String getList(@QueryParam("filter") String filter) {
        return "[]";
    }

    // Violation: R1_REVEAL_INTENT - "handle" is vague
    public void handleStuff(Object obj) {
        // ...
    }

    // Violation: R9_CORRECT_LANGUAGE - Spanish word
    public void calcularTotal() {
        // ...
    }

    // Good: Descriptive method name
    public Customer findCustomerByEmail(String emailAddress) {
        return null;
    }

    // Violation: R5_NO_TYPE_ENCODING - Interface prefix
    interface ICustomerRepository {
        Customer findById(Long id);
    }

    // Inner class for testing
    class CustomerInfo {
        // Violation: R3 - "Data" noise word
        private String customerData;

        // Good name
        private String firstName;
        private String lastName;
    }
}

class Customer {
    private Long id;
    private String name;
}
