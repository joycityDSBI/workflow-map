"""001_initial_schema

Revision ID: 001
Revises:
Create Date: 2026-08-20 00:00:00.000000

Creates all seven tables for the JoyCity Ontology Builder:
  objects, links, actions, rules,
  expert_domain_map, extraction_jobs, audit_log

Self-referential FKs (superseded_by, derived_from) are added after the
table exists via ALTER TABLE to avoid circular DDL ordering issues.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ONTOLOGY_STATUS_CHECK = (
    "status IN ('DRAFT','PENDING_REVIEW','PUBLISHED','REJECTED','ARCHIVED')"
)


def upgrade() -> None:
    # ── Enable pgcrypto for gen_random_uuid() ─────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column(
            "role",
            sa.String(32),
            nullable=False,
            server_default="analyst",
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "role IN ('analyst', 'domain_expert', 'admin')",
            name="ck_users_role",
        ),
    )

    # ── objects ───────────────────────────────────────────────────────────────
    op.create_table(
        "objects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column(
            "source_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "source_stale",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Numeric(precision=3, scale=2),
            nullable=True,
        ),
        # superseded_by and derived_from are added below via ALTER TABLE
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("derived_from", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('actor','domain','tx','cs','record')",
            name="ck_objects_category",
        ),
        sa.CheckConstraint(ONTOLOGY_STATUS_CHECK, name="ck_objects_status"),
    )
    op.create_index("ix_objects_name", "objects", ["name"])
    op.create_index("ix_objects_superseded_by", "objects", ["superseded_by"])
    op.create_index("ix_objects_derived_from", "objects", ["derived_from"])

    # Self-referential FKs added after table creation
    op.create_foreign_key(
        "fk_objects_superseded_by",
        "objects",
        "objects",
        ["superseded_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_objects_derived_from",
        "objects",
        "objects",
        ["derived_from"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── links ─────────────────────────────────────────────────────────────────
    op.create_table(
        "links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "from_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", name="fk_links_from_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", name="fk_links_to_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("cardinality", sa.Text(), nullable=True),
        sa.Column(
            "is_derived",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column(
            "source_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "source_stale",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("derived_from", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(ONTOLOGY_STATUS_CHECK, name="ck_links_status"),
    )
    op.create_index("ix_links_from_id", "links", ["from_id"])
    op.create_index("ix_links_to_id", "links", ["to_id"])
    op.create_index("ix_links_from_to", "links", ["from_id", "to_id"])
    op.create_index("ix_links_superseded_by", "links", ["superseded_by"])
    op.create_index("ix_links_derived_from", "links", ["derived_from"])

    op.create_foreign_key(
        "fk_links_superseded_by",
        "links",
        "links",
        ["superseded_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_links_derived_from",
        "links",
        "links",
        ["derived_from"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── actions ───────────────────────────────────────────────────────────────
    op.create_table(
        "actions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "objects.id", name="fk_actions_actor_id", ondelete="SET NULL"
            ),
            nullable=True,
        ),
        sa.Column(
            "reads",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "creates",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updates",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("preconditions", sa.Text(), nullable=True),
        sa.Column("outcomes", sa.Text(), nullable=True),
        sa.Column("trigger", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column(
            "source_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "source_stale",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("derived_from", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(ONTOLOGY_STATUS_CHECK, name="ck_actions_status"),
        sa.CheckConstraint(
            "trigger IN ('manual_ui','scheduled','notion_webhook') OR trigger IS NULL",
            name="ck_actions_trigger",
        ),
    )
    op.create_index("ix_actions_name", "actions", ["name"])
    op.create_index("ix_actions_actor_id", "actions", ["actor_id"])
    op.create_index("ix_actions_superseded_by", "actions", ["superseded_by"])
    op.create_index("ix_actions_derived_from", "actions", ["derived_from"])

    op.create_foreign_key(
        "fk_actions_superseded_by",
        "actions",
        "actions",
        ["superseded_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_actions_derived_from",
        "actions",
        "actions",
        ["derived_from"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── rules ─────────────────────────────────────────────────────────────────
    op.create_table(
        "rules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "applies_to_actions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column(
            "source_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "source_stale",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("derived_from", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(ONTOLOGY_STATUS_CHECK, name="ck_rules_status"),
    )
    op.create_index("ix_rules_title", "rules", ["title"])
    op.create_index("ix_rules_superseded_by", "rules", ["superseded_by"])
    op.create_index("ix_rules_derived_from", "rules", ["derived_from"])

    op.create_foreign_key(
        "fk_rules_superseded_by",
        "rules",
        "rules",
        ["superseded_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_rules_derived_from",
        "rules",
        "rules",
        ["derived_from"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── expert_domain_map ─────────────────────────────────────────────────────
    op.create_table(
        "expert_domain_map",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("expert_id", sa.Text(), nullable=False),
        sa.Column("domain_name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("expert_id", "domain_name", name="uq_expert_domain"),
    )
    op.create_index(
        "ix_expert_domain_expert_id", "expert_domain_map", ["expert_id"]
    )
    op.create_index(
        "ix_expert_domain_domain_name", "expert_domain_map", ["domain_name"]
    )

    # ── extraction_jobs ───────────────────────────────────────────────────────
    op.create_table(
        "extraction_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default="RUNNING", nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column(
            "source_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("total_docs", sa.Integer(), nullable=True),
        sa.Column("success_docs", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_docs", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "error_details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('RUNNING','COMPLETED','PARTIAL_SUCCESS','FAILED','RATE_LIMITED')",
            name="ck_extraction_jobs_status",
        ),
        sa.CheckConstraint(
            "source_type IN ('notion','file')",
            name="ck_extraction_jobs_source_type",
        ),
    )
    op.create_index(
        "ix_extraction_jobs_created_by", "extraction_jobs", ["created_by"]
    )
    op.create_index("ix_extraction_jobs_status", "extraction_jobs", ["status"])

    # ── audit_log ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("actor_email", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "entity_type IN ('object','link','action','rule')",
            name="ck_audit_log_entity_type",
        ),
    )
    op.create_index(
        "ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"]
    )
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order

    # users (no foreign keys from other tables; drop first)
    op.drop_table("users")

    # audit_log
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_table("audit_log")

    # extraction_jobs
    op.drop_index("ix_extraction_jobs_status", table_name="extraction_jobs")
    op.drop_index("ix_extraction_jobs_created_by", table_name="extraction_jobs")
    op.drop_table("extraction_jobs")

    # expert_domain_map
    op.drop_index("ix_expert_domain_domain_name", table_name="expert_domain_map")
    op.drop_index("ix_expert_domain_expert_id", table_name="expert_domain_map")
    op.drop_table("expert_domain_map")

    # rules (drop self-ref FKs first)
    op.drop_constraint("fk_rules_derived_from", "rules", type_="foreignkey")
    op.drop_constraint("fk_rules_superseded_by", "rules", type_="foreignkey")
    op.drop_index("ix_rules_derived_from", table_name="rules")
    op.drop_index("ix_rules_superseded_by", table_name="rules")
    op.drop_index("ix_rules_title", table_name="rules")
    op.drop_table("rules")

    # actions
    op.drop_constraint("fk_actions_derived_from", "actions", type_="foreignkey")
    op.drop_constraint("fk_actions_superseded_by", "actions", type_="foreignkey")
    op.drop_index("ix_actions_derived_from", table_name="actions")
    op.drop_index("ix_actions_superseded_by", table_name="actions")
    op.drop_index("ix_actions_actor_id", table_name="actions")
    op.drop_index("ix_actions_name", table_name="actions")
    op.drop_table("actions")

    # links
    op.drop_constraint("fk_links_derived_from", "links", type_="foreignkey")
    op.drop_constraint("fk_links_superseded_by", "links", type_="foreignkey")
    op.drop_index("ix_links_derived_from", table_name="links")
    op.drop_index("ix_links_superseded_by", table_name="links")
    op.drop_index("ix_links_from_to", table_name="links")
    op.drop_index("ix_links_to_id", table_name="links")
    op.drop_index("ix_links_from_id", table_name="links")
    op.drop_table("links")

    # objects (drop self-ref FKs first so the table can be dropped)
    op.drop_constraint("fk_objects_derived_from", "objects", type_="foreignkey")
    op.drop_constraint("fk_objects_superseded_by", "objects", type_="foreignkey")
    op.drop_index("ix_objects_derived_from", table_name="objects")
    op.drop_index("ix_objects_superseded_by", table_name="objects")
    op.drop_index("ix_objects_name", table_name="objects")
    op.drop_table("objects")
