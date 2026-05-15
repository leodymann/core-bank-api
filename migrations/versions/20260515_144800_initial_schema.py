"""initial schema

Revision ID: 20260515_144800
Revises:
Create Date: 2026-05-15 14:48:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260515_144800"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_name", sa.String(length=160), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_account_id", sa.String(length=36), nullable=False),
        sa.Column("destination_account_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.Enum("QUEUED", "PROCESSING", "SUCCEEDED", "FAILED", name="transactionstatus"),
            nullable=False,
        ),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_destination_account_id", "transactions", ["destination_account_id"], unique=False)
    op.create_index("ix_transactions_idempotency_key", "transactions", ["idempotency_key"], unique=True)
    op.create_index("ix_transactions_source_account_id", "transactions", ["source_account_id"], unique=False)
    op.create_index("ix_transactions_status_created_at", "transactions", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_status_created_at", table_name="transactions")
    op.drop_index("ix_transactions_source_account_id", table_name="transactions")
    op.drop_index("ix_transactions_idempotency_key", table_name="transactions")
    op.drop_index("ix_transactions_destination_account_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("accounts")
