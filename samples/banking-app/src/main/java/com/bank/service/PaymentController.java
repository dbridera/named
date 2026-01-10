package com.bank.service;

import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

/**
 * REST Controller demonstrating guardrails.
 * Methods with JAX-RS annotations should NOT be renamed (G3_PUBLIC_API).
 */
@Path("/payments")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class PaymentController {

    // These methods have REST annotations - GUARDRAIL G3 applies
    // Names might be bad but they should NOT be suggested for rename

    @GET
    @Path("/list")
    public Response getList() {  // Bad name but protected by @GET
        return Response.ok().build();
    }

    @GET
    @Path("/{id}")
    public Response get(@PathParam("id") String id) {  // Generic but protected
        return Response.ok().build();
    }

    @POST
    public Response create(Object data) {  // 'data' is vague but protected by @POST
        return Response.ok().build();
    }

    @PUT
    @Path("/{id}")
    public Response upd(  // Abbreviated but protected
            @PathParam("id") String id,
            Object obj) {  // 'obj' is bad but protected
        return Response.ok().build();
    }

    @DELETE
    @Path("/{id}")
    public Response del(@PathParam("id") String x) {  // 'x' is terrible but protected
        return Response.ok().build();
    }

    // Query parameters are also protected
    @GET
    @Path("/search")
    public Response search(
            @QueryParam("q") String q,           // Bad but protected
            @QueryParam("page") int pg,          // Bad but protected
            @QueryParam("size") int sz,          // Bad but protected
            @HeaderParam("X-Request-ID") String reqId) {  // Protected
        return Response.ok().build();
    }

    // Private methods WITHOUT annotations CAN be renamed
    // These should get suggestions:

    private void proc(Object o) {  // R1: vague, R6: single letter
        // process something
    }

    private String fmt(String s) {  // R4: abbreviation, R6: single letter
        return s;
    }

    private boolean chk(Object data) {  // R4: abbreviation
        return data != null;
    }

    private Object hlpr() {  // R4: unpronounceable, R1: vague
        return null;
    }

    // Good private method names (no suggestions needed)
    private void validatePaymentAmount(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
    }

    private String formatPaymentReference(String transactionId) {
        return "PAY-" + transactionId;
    }

    private boolean isValidCurrency(String currencyCode) {
        return currencyCode != null && currencyCode.length() == 3;
    }
}
