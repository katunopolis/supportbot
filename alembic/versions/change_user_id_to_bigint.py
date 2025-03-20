"""change user_id to bigint

Revision ID: change_user_id_to_bigint
Revises: 7bb1d3569b1b
Create Date: 2025-03-19 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'change_user_id_to_bigint'
down_revision: Union[str, None] = '7bb1d3569b1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter user_id and assigned_admin columns in requests table
    op.alter_column('requests', 'user_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)
    op.alter_column('requests', 'assigned_admin',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)
    
    # Alter sender_id column in messages table
    op.alter_column('messages', 'sender_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)


def downgrade() -> None:
    # Convert back to Integer (note: this may fail if values are too large)
    op.alter_column('messages', 'sender_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    
    op.alter_column('requests', 'assigned_admin',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    
    op.alter_column('requests', 'user_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True) 