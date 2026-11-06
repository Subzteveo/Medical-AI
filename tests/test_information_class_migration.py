"""Alpha3 A1 — denial-preserving legacy information-class migration tests.

Legacy ``InformationClass`` values map to the A1 ``InformationClassification`` only
through verified boundary adapters. ``SENSITIVE`` has no assumed-safe mapping and
becomes ``UNKNOWN``; no legacy flag may be promoted to a de-identified or restricted
class, which would require a separate authorised determination.
"""

from __future__ import annotations

from medical_ai.authority import InformationClassification, migrate_information_class
from medical_ai.schemas import InformationClass


def test_public_maps_to_public_evidence() -> None:
    assert migrate_information_class(InformationClass.PUBLIC) is InformationClassification.PUBLIC_EVIDENCE


def test_phi_maps_to_identifiable() -> None:
    assert (
        migrate_information_class(InformationClass.PHI)
        is InformationClassification.IDENTIFIABLE_HEALTH_INFORMATION
    )


def test_sensitive_is_deny_preserving_unknown() -> None:
    assert migrate_information_class(InformationClass.SENSITIVE) is InformationClassification.UNKNOWN


def test_unknown_stays_unknown() -> None:
    assert migrate_information_class(InformationClass.UNKNOWN) is InformationClassification.UNKNOWN


def test_migration_never_invents_deidentified_or_restricted() -> None:
    produced = {migrate_information_class(value) for value in InformationClass}
    assert InformationClassification.DEIDENTIFIED_HEALTH_INFORMATION not in produced
    assert InformationClassification.RESTRICTED_RESEARCH_DATA not in produced


def test_every_legacy_value_is_mapped() -> None:
    # No legacy value falls through to an implicit permissive default.
    for value in InformationClass:
        assert isinstance(migrate_information_class(value), InformationClassification)
