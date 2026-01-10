# Naming Rules

Named enforces 9 naming rules based on Clean Code principles, adapted for banking industry standards. Each rule has bilingual support (English/Spanish).

## Rule Categories

| Category | Description | Rules |
|----------|-------------|-------|
| **Semantic** | Intent and meaning | R1, R2, R3, R6, R8 |
| **Syntactic** | Format and pronunciation | R4, R5, R9 |
| **Consistency** | Project-wide patterns | R7 |

---

## R1: Reveal Intent (Revelar intención)

**Severity**: ERROR

Names must self-explain why the element exists, what it's used for, and how it's used.

### Good Examples
- `calculateTotalPrice`
- `isUserAuthenticated`
- `customerEmailAddress`

### Bad Examples
- `data`
- `info`
- `temp`
- `doIt`
- `process`
- `handle`

### Detection
- Pattern: `^(data|info|temp|tmp|obj|val|var)$`
- Tokens to avoid: `data`, `info`, `object`, `manager`, `util`, `helper`, `temp`, `tmp`

---

## R2: No Disinformation (Evitar desinformación)

**Severity**: ERROR

Don't use names that lead to incorrect conclusions or vary only in minimal details.

### Good Examples
- `activeUserAccounts`
- `pendingOrdersList`

### Bad Examples
- `accountList` (when not actually a List)
- `isAccount` vs `isActiveAccount` (confusing pair)

### Detection
- Pattern: Names ending in `List`, `Map`, `Set` should match the actual type

---

## R3: Meaningful Distinctions (Distinciones significativas)

**Severity**: ERROR

Avoid generic labels (a1, b2), semantic noise (ProductInfo vs ProductData), and redundancies.

### Good Examples
- `sourceAccount`
- `targetAccount`
- `productDetails`

### Bad Examples
- `a1`, `a2`
- `ProductInfo`, `ProductData`
- `theCustomer`

### Detection
- Pattern: `^[a-z]\d+$` (single letter + number)
- Pattern: `.*(Info|Data)$`
- Tokens to avoid: `Info`, `Data`, `Object`, `Thing`, `Item`

---

## R4: Pronounceable Names (Nombres pronunciables)

**Severity**: WARNING

Avoid hard-to-pronounce abbreviations. Use full words that can be spoken in conversation.

### Good Examples
- `generationTimestamp`
- `customerRecord`
- `modificationDate`

### Bad Examples
- `genymdhms`
- `cstmrRcrd`
- `modDt`

### Detection
- Pattern: `^[bcdfghjklmnpqrstvwxz]{4,}` (4+ consonants in a row)

---

## R5: No Type Encoding (Evitar tipo en el nombre)

**Severity**: ERROR

Don't include data types in names or use Hungarian notation. Avoid interface prefixes like `I`.

### Good Examples
- `phoneNumber`
- `Customer`
- `isValid`

### Bad Examples
- `phoneString`
- `ICustomer`
- `boolIsValid`
- `intCount`

### Detection
- Pattern: `.*(String|Integer|Boolean|Long|Double|Float)$`
- Pattern: `^I[A-Z][a-z].*` (Interface prefix)
- Pattern: `^(str|int|bool|lng|dbl|flt)[A-Z].*` (Hungarian notation)

---

## R6: No Mental Mapping (Evitar mapeo mental)

**Severity**: ERROR

Don't use single-letter variables. The reader shouldn't have to mentally translate a name to understand it.

### Exceptions
- `i`, `j`, `k` in short loop constructs

### Good Examples
- `index`
- `counter`
- `element`
- `customer`

### Bad Examples
- `a`, `b`, `x`, `n`, `t`

### Detection
- Pattern: `^[a-z]$` (single lowercase letter)
- Exceptions: `i`, `j`, `k`

---

## R7: One Word Per Concept (Una palabra por concepto)

**Severity**: WARNING

Maintain technical consistency within the project. Don't mix synonyms for the same concept.

### Good Examples
- Use `Mapper` consistently for all mappers
- Use `Converter` consistently for all converters
- Use `get` consistently (not mixing with `fetch`, `retrieve`)

### Bad Examples
- `UserMapper` + `OrderConverter` (inconsistent suffixes)
- `fetchUser` + `retrieveOrder` + `getProduct` (mixed verbs)

### Detection
- Requires project-wide analysis to detect inconsistencies

---

## R8: Context-Aware Naming (Nombrar según contexto)

**Severity**: WARNING

Use names aligned to design patterns and be specific about context.

### Good Examples
- `AccountVisitor` (design pattern)
- `OrderFactory` (design pattern)
- `billingAddress` (specific context)
- `shippingAddress` (specific context)

### Bad Examples
- `Visitor` (too generic)
- `address` (ambiguous without context)

### Detection
- Requires context analysis to detect generic names

---

## R9: Correct Language (Idioma correcto)

**Severity**: ERROR

Use correct English. Avoid spanglish, misspellings, and non-English words.

### Good Examples
- `customer`
- `invoice`
- `payment`
- `calculate`

### Bad Examples
- `cliente` (Spanish)
- `factura` (Spanish)
- `calcular` (Spanish)
- `getUsuario` (Spanglish)

### Detection
- Requires dictionary lookup to detect non-English words

---

## Rule Enforcement

### In LLM Prompts
All rules are rendered as context for the LLM, guiding it to generate appropriate suggestions.

### In Validation
The validator checks suggested names against rules to ensure they don't introduce new violations.

### In Reports
Each suggestion includes which rules it addresses, helping developers understand the rationale.

## Customization

Rules are defined in `src/named/rules/naming_rules.py`. Each rule specifies:
- Detection patterns (regex)
- Tokens to avoid
- Exceptions
- Good/bad examples
- Severity level

To customize rules for your organization, modify the `NAMING_RULES` list in that file.
