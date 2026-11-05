"""Initial relational schema for SCENTIQ platform.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-04 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Brands
    op.create_table(
        'brands',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('origin_country', sa.String(2), nullable=True),
        sa.Column('brand_type', sa.String(50), nullable=False),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_brands_canonical_name', 'brands', ['canonical_name'])
    op.create_index('ix_brands_slug', 'brands', ['slug'], unique=True)
    op.create_index('ix_brands_status', 'brands', ['status'])

    # 2. Notes
    op.create_table(
        'notes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('canonical_name', sa.String(150), nullable=False),
        sa.Column('slug', sa.String(150), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('note_family', sa.String(100), nullable=True),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_notes_canonical_name', 'notes', ['canonical_name'])
    op.create_index('ix_notes_slug', 'notes', ['slug'], unique=True)

    # 3. Accords
    op.create_table(
        'accords',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('canonical_name', sa.String(150), nullable=False),
        sa.Column('slug', sa.String(150), nullable=False),
        sa.Column('family', sa.String(100), nullable=True),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_accords_canonical_name', 'accords', ['canonical_name'])
    op.create_index('ix_accords_slug', 'accords', ['slug'], unique=True)

    # 4. Evidence Sources
    op.create_table(
        'evidence_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('url', sa.String(1000), nullable=True),
        sa.Column('publisher', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('accessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('license_status', sa.String(50), nullable=False),
        sa.Column('rights_note', sa.Text(), nullable=True),
        sa.Column('attribution_text', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evidence_sources_publisher', 'evidence_sources', ['publisher'])
    op.create_index('ix_evidence_sources_source_type', 'evidence_sources', ['source_type'])

    # 5. Fragrances
    op.create_table(
        'fragrances',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('brand_id', sa.String(36), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('concentration', sa.String(50), nullable=False),
        sa.Column('release_year', sa.Integer(), nullable=True),
        sa.Column('perfumer_text', sa.String(255), nullable=True),
        sa.Column('marketed_gender', sa.String(50), nullable=True),
        sa.Column('family', sa.String(100), nullable=True),
        sa.Column('secondary_family', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('curation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('brand_id', 'slug', 'concentration', name='uq_brand_slug_concentration'),
    )
    op.create_index('ix_fragrances_canonical_name', 'fragrances', ['canonical_name'])
    op.create_index('ix_fragrances_slug', 'fragrances', ['slug'])
    op.create_index('ix_fragrances_brand_id', 'fragrances', ['brand_id'])
    op.create_index('ix_fragrances_status', 'fragrances', ['status'])

    # 6. Fragrance Notes
    op.create_table(
        'fragrance_notes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fragrance_id', sa.String(36), sa.ForeignKey('fragrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('note_id', sa.String(36), sa.ForeignKey('notes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('pyramid_position', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('evidence_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, default=1.0),
        sa.UniqueConstraint('fragrance_id', 'note_id', 'pyramid_position', name='uq_fragrance_note_position'),
    )
    op.create_index('ix_fragrance_notes_fragrance_id', 'fragrance_notes', ['fragrance_id'])
    op.create_index('ix_fragrance_notes_note_id', 'fragrance_notes', ['note_id'])

    # 7. Fragrance Accords
    op.create_table(
        'fragrance_accords',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fragrance_id', sa.String(36), sa.ForeignKey('fragrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('accord_id', sa.String(36), sa.ForeignKey('accords.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('intensity_rank', sa.Integer(), nullable=False, default=1),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('evidence_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, default=1.0),
        sa.UniqueConstraint('fragrance_id', 'accord_id', name='uq_fragrance_accord'),
    )
    op.create_index('ix_fragrance_accords_fragrance_id', 'fragrance_accords', ['fragrance_id'])
    op.create_index('ix_fragrance_accords_accord_id', 'fragrance_accords', ['accord_id'])

    # 8. Claim Evidences
    op.create_table(
        'claim_evidences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('evidence_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, default=1.0),
        sa.Column('reviewer_id', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_claim_evidences_entity', 'claim_evidences', ['entity_type', 'entity_id'])

    # 9. Alternative Relationships
    op.create_table(
        'alternative_relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_fragrance_id', sa.String(36), sa.ForeignKey('fragrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_fragrance_id', sa.String(36), sa.ForeignKey('fragrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('evidence_grade', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('known_differences', sa.Text(), nullable=True),
        sa.Column('curator_id', sa.String(100), nullable=True),
        sa.Column('reviewer_id', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('source_fragrance_id', 'candidate_fragrance_id', name='uq_source_candidate_alternative'),
    )
    op.create_index('ix_alt_rel_source', 'alternative_relationships', ['source_fragrance_id'])
    op.create_index('ix_alt_rel_candidate', 'alternative_relationships', ['candidate_fragrance_id'])
    op.create_index('ix_alt_rel_status', 'alternative_relationships', ['status'])

    # 10. Price Listings
    op.create_table(
        'price_listings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fragrance_id', sa.String(36), sa.ForeignKey('fragrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seller', sa.String(255), nullable=False),
        sa.Column('url', sa.String(1000), nullable=True),
        sa.Column('size_ml', sa.Float(), nullable=True),
        sa.Column('price_inr', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='INR'),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('seller_status', sa.String(50), nullable=False),
        sa.Column('listing_status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_price_listings_fragrance', 'price_listings', ['fragrance_id'])
    op.create_index('ix_price_listings_status', 'price_listings', ['listing_status'])

    # 11. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('auth_subject', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. User Profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('preference_vector_json', sa.JSON(), nullable=True),
        sa.Column('avoid_terms', sa.JSON(), nullable=True),
        sa.Column('budget_min', sa.Float(), nullable=True),
        sa.Column('budget_max', sa.Float(), nullable=True),
        sa.Column('occasions', sa.JSON(), nullable=True),
        sa.Column('climate_context', sa.JSON(), nullable=True),
        sa.Column('intensity_preference', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. User Feedbacks
    op.create_table(
        'user_feedbacks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fragrance_id', sa.String(36), sa.ForeignKey('fragrances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('context_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 14. Recommendation Runs
    op.create_table(
        'recommendation_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('query_snapshot', sa.JSON(), nullable=False),
        sa.Column('ruleset_version', sa.String(50), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('result_ids', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor_id', sa.String(100), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_events_entity', 'audit_events', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('recommendation_runs')
    op.drop_table('user_feedbacks')
    op.drop_table('user_profiles')
    op.drop_table('users')
    op.drop_table('price_listings')
    op.drop_table('alternative_relationships')
    op.drop_table('claim_evidences')
    op.drop_table('fragrance_accords')
    op.drop_table('fragrance_notes')
    op.drop_table('fragrances')
    op.drop_table('evidence_sources')
    op.drop_table('accords')
    op.drop_table('notes')
    op.drop_table('brands')

