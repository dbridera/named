"""The 9 naming rules based on banking code quality guidelines."""

from named.rules.models import NamingRule, RuleCategory, Severity

NAMING_RULES: list[NamingRule] = [
    # Rule 1: Reveal Intent
    NamingRule(
        id="R1_REVEAL_INTENT",
        name="Revelar intención",
        name_en="Reveal Intent",
        description=(
            "Los nombres deben explicar por sí mismos para qué existe el elemento, "
            "para qué se utiliza y cómo se usa."
        ),
        description_en=(
            "Names must self-explain why the element exists, what it's used for, and how it's used."
        ),
        category=RuleCategory.SEMANTIC,
        severity=Severity.ERROR,
        examples_good=[
            "calculateTotalPrice",
            "isUserAuthenticated",
            "customerEmailAddress",
            "fetchActiveOrders",
        ],
        examples_bad=["data", "info", "temp", "doIt", "process", "handle", "stuff"],
        detect_patterns=[
            r"^(data|info|temp|tmp|obj|val|var|stuff|thing)$",
            r"^do[A-Z].*",  # doSomething is too vague
            r"^process[A-Z].*",  # processSomething is too vague
            r"^handle[A-Z].*",  # handleSomething is too vague
        ],
        tokens_to_avoid=[
            "data",
            "info",
            "object",
            "manager",
            "util",
            "helper",
            "temp",
            "tmp",
            "stuff",
            "thing",
        ],
    ),
    # Rule 2: No Disinformation
    NamingRule(
        id="R2_NO_DISINFORMATION",
        name="Evitar desinformación",
        name_en="Avoid Disinformation",
        description=(
            "No usar nombres que lleven a conclusiones incorrectas o que varíen "
            "solo en detalles mínimos (ej. isAccount vs isActiveAccount)."
        ),
        description_en=(
            "Don't use names that lead to incorrect conclusions or vary only "
            "in minimal details (e.g., isAccount vs isActiveAccount)."
        ),
        category=RuleCategory.SEMANTIC,
        severity=Severity.ERROR,
        examples_good=[
            "activeUserAccounts",
            "pendingOrdersList",
            "customerMap",
        ],
        examples_bad=[
            "accountList (when not a List)",
            "hp (ambiguous)",
            "aix (platform-specific)",
        ],
        detect_patterns=[
            # These patterns detect potential type mismatches - actual validation
            # requires type information from the parser
            r".*List$",
            r".*Map$",
            r".*Set$",
            r".*Array$",
        ],
    ),
    # Rule 3: Meaningful Distinctions
    NamingRule(
        id="R3_MEANINGFUL_DISTINCTIONS",
        name="Distinciones significativas",
        name_en="Meaningful Distinctions",
        description=(
            "Evitar etiquetas genéricas (a1, b2), ruidos semánticos "
            "(ej. ProductInfo vs ProductData) y redundancias innecesarias."
        ),
        description_en=(
            "Avoid generic labels (a1, b2), semantic noise "
            "(e.g., ProductInfo vs ProductData), and unnecessary redundancies."
        ),
        category=RuleCategory.SEMANTIC,
        severity=Severity.ERROR,
        examples_good=[
            "sourceAccount",
            "targetAccount",
            "productDetails",
            "customerRecord",
        ],
        examples_bad=[
            "a1",
            "a2",
            "ProductInfo",
            "ProductData",
            "theCustomer",
            "aUser",
        ],
        detect_patterns=[
            r"^[a-z]\d+$",  # a1, b2, etc.
            r"^[a-z]{1,2}\d*$",  # short meaningless names
            r".*(Info|Data)$",  # Noise words
            r"^(the|a|an)[A-Z].*",  # Unnecessary articles
        ],
        tokens_to_avoid=["Info", "Data", "Object", "Thing", "Item", "Entity"],
    ),
    # Rule 4: Pronounceable Names
    NamingRule(
        id="R4_PRONOUNCEABLE",
        name="Nombres pronunciables",
        name_en="Pronounceable Names",
        description=(
            "Evitar abreviaturas difíciles de decir; por ejemplo, usar "
            "generationTimestamp en lugar de genymdhms."
        ),
        description_en=(
            "Avoid hard-to-pronounce abbreviations; for example, use "
            "generationTimestamp instead of genymdhms."
        ),
        category=RuleCategory.SYNTACTIC,
        severity=Severity.WARNING,
        examples_good=[
            "generationTimestamp",
            "customerRecord",
            "modificationDate",
            "recordCount",
        ],
        examples_bad=[
            "genymdhms",
            "cstmrRcrd",
            "modDt",
            "rcrdCnt",
            "pszName",
        ],
        detect_patterns=[
            r"^[bcdfghjklmnpqrstvwxz]{4,}",  # 4+ consecutive consonants
            r".*[bcdfghjklmnpqrstvwxz]{5,}.*",  # 5+ consonants anywhere
        ],
    ),
    # Rule 5: No Type Encoding
    NamingRule(
        id="R5_NO_TYPE_ENCODING",
        name="Evitar tipo en el nombre",
        name_en="No Type Encoding",
        description=(
            "No incluir tipos de datos en el nombre (ej. evitar phoneString) "
            "ni prefijos de interfaces como la 'I'."
        ),
        description_en=(
            "Don't include data types in names (e.g., avoid phoneString) "
            "or interface prefixes like 'I'."
        ),
        category=RuleCategory.SYNTACTIC,
        severity=Severity.ERROR,
        examples_good=[
            "phoneNumber",
            "Customer",
            "isValid",
            "accountBalance",
        ],
        examples_bad=[
            "phoneString",
            "ICustomer",
            "boolIsValid",
            "intCount",
            "strName",
        ],
        detect_patterns=[
            r".*(String|Integer|Boolean|Long|Double|Float|Int|Bool)$",
            r"^I[A-Z][a-z].*",  # Interface prefix like ICustomer
            r"^(str|int|bool|lng|dbl|flt|obj)[A-Z].*",  # Hungarian notation
            r"^[a-z]+(String|Int|Bool|Long|Double|Float)$",
        ],
    ),
    # Rule 6: No Mental Mapping
    NamingRule(
        id="R6_NO_MENTAL_MAPPING",
        name="Evitar mapeo mental",
        name_en="No Mental Mapping",
        description=(
            "No usar variables de una sola letra, con la única excepción "
            "de i, j y k en bucles cortos."
        ),
        description_en=(
            "Don't use single-letter variables, except for i, j, and k in short loops."
        ),
        category=RuleCategory.SEMANTIC,
        severity=Severity.ERROR,
        examples_good=[
            "index",
            "counter",
            "element",
            "customer",
            "orderItem",
        ],
        examples_bad=["a", "b", "x", "n", "t", "e", "d"],
        detect_patterns=[r"^[a-z]$"],  # Single letter
        exceptions=["i", "j", "k"],  # Allowed in loops
    ),
    # Rule 7: One Word Per Concept
    NamingRule(
        id="R7_ONE_WORD_PER_CONCEPT",
        name="Una palabra por concepto",
        name_en="One Word Per Concept",
        description=(
            "Mantener consistencia técnica; por ejemplo, no mezclar Mapper "
            "con Converter para un mismo concepto."
        ),
        description_en=(
            "Maintain technical consistency; for example, don't mix Mapper "
            "with Converter for the same concept."
        ),
        category=RuleCategory.CONSISTENCY,
        severity=Severity.WARNING,
        examples_good=[
            "UserMapper (consistent with other Mappers)",
            "OrderConverter (consistent with other Converters)",
            "fetchCustomer (consistent with other fetch methods)",
        ],
        examples_bad=[
            "UserMapper + OrderConverter (inconsistent)",
            "fetch + retrieve + get (mixed verbs)",
            "Controller + Manager (same concept)",
        ],
        # This rule requires project-wide analysis
        detect_patterns=[],
    ),
    # Rule 8: Context-Aware Naming
    NamingRule(
        id="R8_CONTEXT_NAMING",
        name="Nombrar según contexto",
        name_en="Context-Aware Naming",
        description=(
            "Usar nombres alineados a patrones de diseño (ej. AccountVisitor) "
            "y ser específicos para evitar ambigüedad (ej. billingAddress)."
        ),
        description_en=(
            "Use names aligned to design patterns (e.g., AccountVisitor) "
            "and be specific to avoid ambiguity (e.g., billingAddress)."
        ),
        category=RuleCategory.SEMANTIC,
        severity=Severity.WARNING,
        examples_good=[
            "AccountVisitor",
            "OrderFactory",
            "billingAddress",
            "shippingAddress",
            "PaymentStrategy",
        ],
        examples_bad=[
            "Visitor (too generic)",
            "address (ambiguous)",
            "Factory (missing context)",
            "impl (non-descriptive)",
        ],
        # This rule requires context analysis
        detect_patterns=[
            r"^(Impl|Implementation)$",
            r".*Impl$",  # Just "Impl" suffix without meaning
        ],
    ),
    # Rule 9: Correct Language
    NamingRule(
        id="R9_CORRECT_LANGUAGE",
        name="Idioma correcto",
        name_en="Correct Language",
        description=(
            "Utilizar inglés correcto, evitando el 'spanglish' y los errores de ortografía."
        ),
        description_en=("Use correct English, avoiding 'spanglish' and spelling errors."),
        category=RuleCategory.SYNTACTIC,
        severity=Severity.ERROR,
        examples_good=[
            "customer",
            "invoice",
            "payment",
            "calculate",
            "processOrder",
        ],
        examples_bad=[
            "cliente",
            "factura",
            "calcular",
            "getUsuario",
            "procesarPago",
            "obtenerCliente",
        ],
        # Spanish word detection patterns
        detect_patterns=[
            r".*(cion|ción)$",  # Spanish suffixes
            r".*(mente)$",  # Spanish adverb suffix
            r"^(obtener|calcular|procesar|guardar|enviar|crear|eliminar)[A-Z].*",
        ],
    ),
]


def get_rule(rule_id: str) -> NamingRule | None:
    """Get a rule by its ID.

    Args:
        rule_id: The rule identifier (e.g., "R1_REVEAL_INTENT")

    Returns:
        The NamingRule if found, None otherwise
    """
    return next((r for r in NAMING_RULES if r.id == rule_id), None)


def get_rules_by_category(category: RuleCategory) -> list[NamingRule]:
    """Get all rules in a specific category.

    Args:
        category: The category to filter by

    Returns:
        List of rules in that category
    """
    return [r for r in NAMING_RULES if r.category == category]


def get_rules_by_severity(severity: Severity) -> list[NamingRule]:
    """Get all rules with a specific severity level.

    Args:
        severity: The severity to filter by

    Returns:
        List of rules with that severity
    """
    return [r for r in NAMING_RULES if r.severity == severity]
