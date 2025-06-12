"""fix_s3_enum_case

Revision ID: c16dd5ffbdbd
Revises: a312ec46df43
Create Date: 2025-06-12 02:04:44.024006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c16dd5ffbdbd'
down_revision = 'a312ec46df43'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the correct uppercase S3 enum value
    op.execute("ALTER TYPE filesource ADD VALUE IF NOT EXISTS 'S3'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values easily
    # The 'S3' enum value will remain but won't be used
    pass 