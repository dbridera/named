# Guardrails

Guardrails are hard constraints that prevent Named from suggesting changes that could break the codebase. They override any naming suggestion, regardless of confidence.

## Overview

| ID | Name | Type | Description |
|----|------|------|-------------|
| G1 | Immutable Contracts | Annotation | Don't rename serialization/persistence fields |
| G2 | Reflection Usage | Pattern | Don't rename elements accessed via reflection |
| G3 | Public API | Annotation | Don't rename REST API endpoints |
| G4 | Confidence Threshold | Confidence | Block low-confidence suggestions |

---

## G1: Immutable Contracts (Contratos inamovibles)

**Type**: Annotation-based

Don't rename symbols with serialization or persistence annotations. These names are part of API contracts with external systems.

### Blocked Annotations

| Annotation | Library | Purpose |
|------------|---------|---------|
| `@JsonProperty` | Jackson | JSON serialization |
| `@JsonAlias` | Jackson | JSON deserialization aliases |
| `@Column` | JPA/Hibernate | Database column mapping |
| `@SerializedName` | Gson | JSON field name |
| `@XmlElement` | JAXB | XML element name |
| `@XmlAttribute` | JAXB | XML attribute name |

### Example

```java
public class User {
    @JsonProperty("user_id")
    private String userId;  // DO NOT RENAME - breaks JSON contract

    @Column(name = "email_address")
    private String email;   // DO NOT RENAME - breaks database mapping

    private String name;    // Can be renamed - no contract
}
```

### Why This Matters

Renaming these fields would break:
- API responses/requests (JSON mismatch)
- Database queries (column not found)
- XML documents (schema violation)
- Third-party integrations

---

## G2: Reflection Usage (Uso de reflexión)

**Type**: Pattern-based

Don't rename elements accessed via Java reflection. These references use string-based lookups that won't update automatically.

### Blocked Patterns

| Pattern | Example |
|---------|---------|
| `Class.forName("...")` | Dynamic class loading |
| `.getDeclaredField("...")` | Field access by name |
| `.getDeclaredMethod("...")` | Method access by name |
| `.getMethod("...")` | Public method access |
| `.getField("...")` | Public field access |

### Example

```java
// If "processOrder" is renamed, this will throw NoSuchMethodException
Method method = OrderService.class.getDeclaredMethod("processOrder", Order.class);

// If "orderStatus" is renamed, this will throw NoSuchFieldException
Field field = Order.class.getDeclaredField("orderStatus");
```

### Why This Matters

Reflection uses string-based lookups. If you rename:
- `processOrder` → `handleOrder`: `NoSuchMethodException` at runtime
- `orderStatus` → `status`: `NoSuchFieldException` at runtime

These errors only appear at runtime, not compile time.

---

## G3: Public API (API pública)

**Type**: Annotation-based

Don't rename elements exposed in REST or public APIs. These are part of the external contract.

### Blocked Annotations

| Annotation | Framework | Purpose |
|------------|-----------|---------|
| `@Path` | JAX-RS | URL path |
| `@GET` | JAX-RS | HTTP GET endpoint |
| `@POST` | JAX-RS | HTTP POST endpoint |
| `@PUT` | JAX-RS | HTTP PUT endpoint |
| `@DELETE` | JAX-RS | HTTP DELETE endpoint |
| `@PATCH` | JAX-RS | HTTP PATCH endpoint |
| `@QueryParam` | JAX-RS | Query parameter name |
| `@PathParam` | JAX-RS | Path parameter name |
| `@HeaderParam` | JAX-RS | Header parameter name |
| `@FormParam` | JAX-RS | Form parameter name |
| `@RequestMapping` | Spring | URL mapping |

### Example

```java
@Path("/users")
public class UserController {

    @GET
    @Path("/{id}")
    public User getUser(@PathParam("id") String id) {  // Protected by @GET, @PathParam
        // Method name "getUser" could be renamed internally,
        // but the parameter "id" is part of the URL contract
    }

    @POST
    public User createUser(@QueryParam("notify") boolean notify) {  // Protected
        // Parameter "notify" is part of the API query string
    }
}
```

### Why This Matters

Renaming API elements would:
- Break client applications
- Invalidate API documentation
- Cause 404/400 errors
- Require coordinated client updates

---

## G4: Confidence Threshold (Umbral de confianza)

**Type**: Confidence-based

Block suggestions with confidence below 80%. Low-confidence suggestions indicate uncertainty and higher risk of incorrect changes.

### Threshold

- **Default**: 0.80 (80%)
- **Configurable**: Via settings

### Example

```
Suggestion: data → customerRecord (confidence: 0.92) ✓ ALLOWED
Suggestion: obj → entity (confidence: 0.75) ✗ BLOCKED
Suggestion: tmp → temporaryValue (confidence: 0.65) ✗ BLOCKED
```

### Why This Matters

Low confidence indicates:
- Ambiguous context
- Multiple valid interpretations
- Insufficient information
- Higher risk of wrong suggestion

---

## Pre-filtering vs Post-validation

### Pre-filtering (Before LLM)

Symbols with blocking annotations are filtered **before** sending to the LLM:
- Saves API costs
- Speeds up analysis
- Clear separation

### Post-validation (After LLM)

The confidence threshold is checked **after** receiving suggestions:
- LLM provides confidence score
- Threshold applied to filter results

---

## Report Handling

### Blocked Symbols Section

The report includes a section for blocked symbols:

```markdown
## Blocked Symbols

These symbols were not renamed due to guardrail restrictions.

| Symbol | Kind | Reason |
|--------|------|--------|
| `userId` | field | G1_IMMUTABLE_CONTRACTS: Has @JsonProperty annotation |
| `getUser` | method | G3_PUBLIC_API: Has @GET annotation |
```

### Statistics

The summary includes blocked counts:
- Analyzable symbols: 202
- Blocked by guardrails: 22

---

## Customization

### Adding Annotations

To add new blocking annotations, modify `src/named/rules/guardrails.py`:

```python
Guardrail(
    id="G1_IMMUTABLE_CONTRACTS",
    blocked_annotations=[
        "JsonProperty",
        "Column",
        "MyCustomAnnotation",  # Add your annotation here
    ],
)
```

### Changing Threshold

To change the confidence threshold:

```python
Guardrail(
    id="G4_CONFIDENCE_THRESHOLD",
    threshold=0.85,  # Increase to 85%
)
```

Or via environment variable:
```bash
export NAMED_CONFIDENCE_THRESHOLD=0.85
```

---

## Best Practices

1. **Review blocked symbols**: They might indicate areas needing documentation
2. **Check false negatives**: Some reflection patterns might not be detected
3. **Coordinate API changes**: If you must rename API elements, plan client updates
4. **Monitor confidence**: Many low-confidence suggestions might indicate unclear code
