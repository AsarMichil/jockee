"""Add enhanced audio analysis fields

Revision ID: d586b7432ebd
Revises: f2ff23da73e9
Create Date: 2025-06-06 17:17:12.030213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd586b7432ebd'
down_revision = 'f2ff23da73e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add style analysis fields
    op.add_column('tracks', sa.Column('dominant_style', sa.String, nullable=True))
    op.add_column('tracks', sa.Column('style_scores', sa.JSON, nullable=True))
    op.add_column('tracks', sa.Column('style_confidence', sa.Float, nullable=True))
    
    # Add enhanced mix points fields
    op.add_column('tracks', sa.Column('mix_in_point', sa.Float, nullable=True))
    op.add_column('tracks', sa.Column('mix_out_point', sa.Float, nullable=True))
    op.add_column('tracks', sa.Column('mixable_sections', sa.JSON, nullable=True))
    
    # Add section analysis fields
    op.add_column('tracks', sa.Column('intro_end', sa.Float, nullable=True))
    op.add_column('tracks', sa.Column('outro_start', sa.Float, nullable=True))
    op.add_column('tracks', sa.Column('intro_energy', sa.Float, nullable=True))
    op.add_column('tracks', sa.Column('outro_energy', sa.Float, nullable=True))
    op.add_column('tracks', sa.Column('energy_profile', sa.JSON, nullable=True))
    
    # Add vocal analysis fields
    op.add_column('tracks', sa.Column('vocal_sections', sa.JSON, nullable=True))
    op.add_column('tracks', sa.Column('instrumental_sections', sa.JSON, nullable=True))


def downgrade() -> None:
    # Remove the added columns in reverse order
    op.drop_column('tracks', 'instrumental_sections')
    op.drop_column('tracks', 'vocal_sections')
    op.drop_column('tracks', 'energy_profile')
    op.drop_column('tracks', 'outro_energy')
    op.drop_column('tracks', 'intro_energy')
    op.drop_column('tracks', 'outro_start')
    op.drop_column('tracks', 'intro_end')
    op.drop_column('tracks', 'mixable_sections')
    op.drop_column('tracks', 'mix_out_point')
    op.drop_column('tracks', 'mix_in_point')
    op.drop_column('tracks', 'style_confidence')
    op.drop_column('tracks', 'style_scores')
    op.drop_column('tracks', 'dominant_style') 