""" updated policy_doc and company table

Revision ID: 6eb341536d1f
Revises: bb69ced30286
Create Date: 2026-06-27 01:18:57.762778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '6eb341536d1f'
down_revision: Union[str, Sequence[str], None] = 'bb69ced30286'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop the foreign key constraint that blocks column modification
    op.execute(
        "ALTER TABLE policy_docs DROP CONSTRAINT IF EXISTS policy_docs_company_id_fkey"
    )

    # 2. Alter companies.id to VARCHAR(36) casting values with USING
    op.execute("ALTER TABLE companies ALTER COLUMN id TYPE VARCHAR(36) USING id::text")

    # 3. Alter policy_docs.company_id to VARCHAR(36) casting values with USING
    op.execute(
        "ALTER TABLE policy_docs ALTER COLUMN company_id TYPE VARCHAR(36) USING company_id::text"
    )

    # 4. Re-create the foreign key constraint linking the text-based columns
    op.create_foreign_key(
        "policy_docs_company_id_fkey",
        "policy_docs",
        "companies",
        ["company_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop the constraint to allow moving back to integers
    op.execute(
        "ALTER TABLE policy_docs DROP CONSTRAINT IF EXISTS policy_docs_company_id_fkey"
    )

    # 2. Revert policy_docs.company_id back to INTEGER casting values
    op.execute(
        "ALTER TABLE policy_docs ALTER COLUMN company_id TYPE INTEGER USING company_id::integer"
    )

    # 3. Revert companies.id back to INTEGER casting values
    op.execute("ALTER TABLE companies ALTER COLUMN id TYPE INTEGER USING id::integer")

    # 4. Re-create the integer-based foreign key constraint
    op.create_foreign_key(
        "policy_docs_company_id_fkey",
        "policy_docs",
        "companies",
        ["company_id"],
        ["id"],
    )
