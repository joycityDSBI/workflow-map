"""ORM model registry.

Importing this package ensures all models are registered with Base.metadata,
which is required for Alembic autogenerate and for `Base.metadata.create_all`.
"""

from app.models.base import Base, OntologyMixin
from app.models.users import User
from app.models.objects import Object
from app.models.links import Link
from app.models.actions import Action
from app.models.rules import Rule
from app.models.expert_domain_map import ExpertDomainMap
from app.models.extraction_jobs import ExtractionJob
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "OntologyMixin",
    "User",
    "Object",
    "Link",
    "Action",
    "Rule",
    "ExpertDomainMap",
    "ExtractionJob",
    "AuditLog",
]
