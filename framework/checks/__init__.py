from .write_safety import check_write_safety
from .boundary_enforcement import check_boundary_enforcement
from .consent_auth import check_consent_auth
from .forensics import check_forensics
from .interface_legibility import check_interface_legibility
from .operational_containment import check_operational_containment

DIMENSION_CHECKS = {
    "write_safety": check_write_safety,
    "boundary_enforcement": check_boundary_enforcement,
    "consent_auth": check_consent_auth,
    "forensics": check_forensics,
    "interface_legibility": check_interface_legibility,
    "operational_containment": check_operational_containment,
}
