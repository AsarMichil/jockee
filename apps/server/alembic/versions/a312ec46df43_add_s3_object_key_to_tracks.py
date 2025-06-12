"""add_s3_object_key_to_tracks

Revision ID: a312ec46df43
Revises: d586b7432ebd
Create Date: 2025-06-11 22:33:52.460201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a312ec46df43'
down_revision = 'd586b7432ebd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add s3_object_key column to tracks table
    op.add_column('tracks', sa.Column('s3_object_key', sa.String(), nullable=True))
    
    # Update the file_source enum to include 'S3' (uppercase to match existing enum)
    # First create the new enum type
    file_source_enum = sa.Enum('local', 'youtube', 's3', 'unavailable', name='filesource')
    
    # For PostgreSQL, we need to use ALTER TYPE to add new enum values
    # This is a safe operation that adds the new value without affecting existing data
    op.execute("ALTER TYPE filesource ADD VALUE IF NOT EXISTS 'S3'")


def downgrade() -> None:
    # Remove s3_object_key column
    op.drop_column('tracks', 's3_object_key')
    
    # Note: PostgreSQL doesn't support removing enum values easily
    # The 's3' enum value will remain but won't be used 