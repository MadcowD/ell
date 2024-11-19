"""Initial ell sql schema

Revision ID: 4524fb60d23e
Revises: 
Create Date: 2024-11-14 10:51:49.545417
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, JSON, TIMESTAMP, Float, String, Integer, ForeignKey, Boolean
import enum

from ell.types.lmp import LMPType

# revision identifiers, used by Alembic.
revision = '4524fb60d23e'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create SerializedLMP table first (as it's referenced by others)
    op.create_table(
        'serializedlmp',
        sa.Column('lmp_id', String(), nullable=False),
        sa.Column('name', String(), nullable=False),
        sa.Column('source', String(), nullable=False),
        sa.Column('dependencies', String(), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('lmp_type', sa.Enum(LMPType, name='lmptype'), nullable=False),
        sa.Column('api_params', JSON, nullable=True),
        sa.Column('initial_free_vars', JSON, nullable=True),
        sa.Column('initial_global_vars', JSON, nullable=True),
        sa.Column('num_invocations', Integer(), nullable=True, default=None),
        sa.Column('commit_message', String(), nullable=True),
        sa.Column('version_number', Integer(), nullable=True),
        sa.PrimaryKeyConstraint('lmp_id')
    )
    op.create_index('ix_serializedlmp_name', 'serializedlmp', ['name'])
    op.create_index('ix_serializedlmp_created_at', 'serializedlmp', ['created_at'])

    # Create SerializedLMPUses table
    op.create_table(
        'serializedlmpuses',
        sa.Column('lmp_user_id', String(), nullable=False),
        sa.Column('lmp_using_id', String(), nullable=False),
        sa.ForeignKeyConstraint(['lmp_user_id'], ['serializedlmp.lmp_id']),
        sa.ForeignKeyConstraint(['lmp_using_id'], ['serializedlmp.lmp_id']),
        sa.PrimaryKeyConstraint('lmp_user_id', 'lmp_using_id')
    )
    op.create_index('ix_serializedlmpuses_lmp_user_id', 'serializedlmpuses', ['lmp_user_id'])
    op.create_index('ix_serializedlmpuses_lmp_using_id', 'serializedlmpuses', ['lmp_using_id'])

    # Create Invocation table
    op.create_table(
        'invocation',
        sa.Column('id', String(), nullable=False),
        sa.Column('lmp_id', String(), nullable=False),
        sa.Column('latency_ms', Float(), nullable=False),
        sa.Column('prompt_tokens', Integer(), nullable=True),
        sa.Column('completion_tokens', Integer(), nullable=True),
        sa.Column('state_cache_key', String(), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('used_by_id', String(), nullable=True),
        sa.ForeignKeyConstraint(['lmp_id'], ['serializedlmp.lmp_id']),
        sa.ForeignKeyConstraint(['used_by_id'], ['invocation.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invocation_lmp_id', 'invocation', ['lmp_id'])
    op.create_index('ix_invocation_used_by_id', 'invocation', ['used_by_id'])
    op.create_index('ix_invocation_created_at_latency_ms', 'invocation', ['created_at', 'latency_ms'])
    op.create_index('ix_invocation_created_at_tokens', 'invocation', ['created_at', 'prompt_tokens', 'completion_tokens'])
    op.create_index('ix_invocation_lmp_id_created_at', 'invocation', ['lmp_id', 'created_at'])

    # Create InvocationContents table
    op.create_table(
        'invocationcontents',
        sa.Column('invocation_id', String(), nullable=False),
        sa.Column('params', JSON, nullable=True),
        sa.Column('results', JSON, nullable=True),
        sa.Column('invocation_api_params', JSON, nullable=True),
        sa.Column('global_vars', JSON, nullable=True),
        sa.Column('free_vars', JSON, nullable=True),
        sa.Column('is_external', Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['invocation_id'], ['invocation.id']),
        sa.PrimaryKeyConstraint('invocation_id')
    )
    op.create_index('ix_invocationcontents_invocation_id', 'invocationcontents', ['invocation_id'])

    # Create InvocationTrace table
    op.create_table(
        'invocationtrace',
        sa.Column('invocation_consumer_id', String(), nullable=False),
        sa.Column('invocation_consuming_id', String(), nullable=False),
        sa.ForeignKeyConstraint(['invocation_consumer_id'], ['invocation.id']),
        sa.ForeignKeyConstraint(['invocation_consuming_id'], ['invocation.id']),
        sa.PrimaryKeyConstraint('invocation_consumer_id', 'invocation_consuming_id')
    )
    op.create_index('ix_invocationtrace_invocation_consumer_id', 'invocationtrace', ['invocation_consumer_id'])
    op.create_index('ix_invocationtrace_invocation_consuming_id', 'invocationtrace', ['invocation_consuming_id'])

def downgrade() -> None:
    # Drop tables in correct order (reverse of creation)
    op.drop_table('invocationtrace')
    op.drop_table('invocationcontents')
    op.drop_table('invocation')
    op.drop_table('serializedlmpuses')
    op.drop_table('serializedlmp')