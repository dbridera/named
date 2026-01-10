"""Guardrails - blocking conditions that prevent renaming."""

from typing import TYPE_CHECKING

from named.rules.models import Guardrail

if TYPE_CHECKING:
    from named.analysis.extractor import Symbol

GUARDRAILS: list[Guardrail] = [
    # G1: Immutable Contracts - Serialization/persistence annotations
    Guardrail(
        id="G1_IMMUTABLE_CONTRACTS",
        name="Contratos inamovibles",
        name_en="Immutable Contracts",
        description=(
            "No se deben renombrar símbolos con anotaciones de serialización "
            "o persistencia (@JsonProperty, @Column, @SerializedName)."
        ),
        description_en=(
            "Don't rename symbols with serialization or persistence annotations "
            "(@JsonProperty, @Column, @SerializedName)."
        ),
        check_type="annotation",
        blocked_annotations=[
            # Jackson JSON
            "JsonProperty",
            "JsonAlias",
            "JsonSetter",
            "JsonGetter",
            # JPA/Hibernate
            "Column",
            "Table",
            "Entity",
            "Id",
            "JoinColumn",
            # GSON
            "SerializedName",
            # JAXB XML
            "XmlElement",
            "XmlAttribute",
            "XmlRootElement",
            # Protocol Buffers
            "ProtoField",
        ],
    ),
    # G2: Reflection Usage - Code accessed via reflection
    Guardrail(
        id="G2_REFLECTION_USAGE",
        name="Uso de reflexión",
        name_en="Reflection Usage",
        description=(
            "No renombrar elementos accedidos mediante reflexión "
            "(Class.forName, getDeclaredField, etc.)."
        ),
        description_en=(
            "Don't rename elements accessed via reflection "
            "(Class.forName, getDeclaredField, etc.)."
        ),
        check_type="pattern",
        blocked_patterns=[
            r"Class\.forName\s*\(\s*[\"'][\w.]+[\"']\s*\)",
            r"\.getDeclaredField\s*\(\s*[\"']\w+[\"']\s*\)",
            r"\.getDeclaredMethod\s*\(\s*[\"']\w+[\"']\s*\)",
            r"\.getMethod\s*\(\s*[\"']\w+[\"']\s*\)",
            r"\.getField\s*\(\s*[\"']\w+[\"']\s*\)",
            r"\.getDeclaredFields\s*\(",
            r"\.getDeclaredMethods\s*\(",
        ],
    ),
    # G3: Public API - REST endpoints and public interfaces
    Guardrail(
        id="G3_PUBLIC_API",
        name="API pública",
        name_en="Public API",
        description=(
            "No renombrar elementos expuestos en APIs REST o públicas "
            "(@Path, @GET, @POST, etc.)."
        ),
        description_en=(
            "Don't rename elements exposed in REST or public APIs "
            "(@Path, @GET, @POST, etc.)."
        ),
        check_type="annotation",
        blocked_annotations=[
            # JAX-RS
            "Path",
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "HEAD",
            "OPTIONS",
            "QueryParam",
            "PathParam",
            "HeaderParam",
            "FormParam",
            "BeanParam",
            "MatrixParam",
            "CookieParam",
            # Spring MVC
            "RequestMapping",
            "GetMapping",
            "PostMapping",
            "PutMapping",
            "DeleteMapping",
            "PatchMapping",
            "RequestParam",
            "PathVariable",
            "RequestBody",
            "ResponseBody",
            # Quarkus specific
            "ConfigProperty",
        ],
    ),
    # G4: Confidence Threshold - LLM confidence check
    Guardrail(
        id="G4_CONFIDENCE_THRESHOLD",
        name="Umbral de confianza",
        name_en="Confidence Threshold",
        description=(
            "Bloquear cambios generados por la IA con una confianza menor a 0.80."
        ),
        description_en=(
            "Block AI-generated changes with confidence below 0.80."
        ),
        check_type="confidence",
        threshold=0.80,
    ),
]


def get_guardrail(guardrail_id: str) -> Guardrail | None:
    """Get a guardrail by its ID.

    Args:
        guardrail_id: The guardrail identifier (e.g., "G1_IMMUTABLE_CONTRACTS")

    Returns:
        The Guardrail if found, None otherwise
    """
    return next((g for g in GUARDRAILS if g.id == guardrail_id), None)


def check_annotation_guardrails(annotations: list[str]) -> list[tuple[str, str]]:
    """Check if any annotations trigger guardrails.

    Args:
        annotations: List of annotation names (without @)

    Returns:
        List of (guardrail_id, reason) tuples for each blocking guardrail
    """
    blocked = []
    for guardrail in GUARDRAILS:
        if guardrail.check_type == "annotation":
            for ann in annotations:
                # Check exact match or match without package prefix
                ann_simple = ann.split(".")[-1] if "." in ann else ann
                if ann_simple in guardrail.blocked_annotations:
                    blocked.append(
                        (guardrail.id, f"Has @{ann_simple} annotation")
                    )
                    break  # Only report once per guardrail
    return blocked


def check_confidence_guardrail(confidence: float) -> tuple[str, str] | None:
    """Check if confidence level triggers the threshold guardrail.

    Args:
        confidence: The confidence score (0.0 to 1.0)

    Returns:
        (guardrail_id, reason) tuple if blocked, None otherwise
    """
    for guardrail in GUARDRAILS:
        if guardrail.check_type == "confidence" and guardrail.threshold is not None:
            if confidence < guardrail.threshold:
                return (
                    guardrail.id,
                    f"Confidence {confidence:.2f} < threshold {guardrail.threshold}",
                )
    return None


def check_all_guardrails(
    annotations: list[str],
    confidence: float = 1.0,
) -> list[tuple[str, str]]:
    """Check all guardrails for a symbol.

    Args:
        annotations: List of annotation names
        confidence: The confidence score for the suggestion

    Returns:
        List of (guardrail_id, reason) tuples for each blocking guardrail
    """
    blocked = []

    # Check annotation-based guardrails
    blocked.extend(check_annotation_guardrails(annotations))

    # Check confidence guardrail
    confidence_block = check_confidence_guardrail(confidence)
    if confidence_block:
        blocked.append(confidence_block)

    return blocked


def is_blocked(annotations: list[str], confidence: float = 1.0) -> bool:
    """Quick check if a symbol would be blocked by any guardrail.

    Args:
        annotations: List of annotation names
        confidence: The confidence score for the suggestion

    Returns:
        True if any guardrail blocks the rename
    """
    return len(check_all_guardrails(annotations, confidence)) > 0
