"""fix bigint columns

Revision ID: fix_bigint_columns
Revises: change_user_id_to_bigint
Create Date: 2025-03-19 17:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_bigint_columns'
down_revision: Union[str, None] = 'change_user_id_to_bigint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL for direct column type changes
    op.execute('ALTER TABLE requests ALTER COLUMN user_id TYPE bigint')
    op.execute('ALTER TABLE requests ALTER COLUMN assigned_admin TYPE bigint')
    op.execute('ALTER TABLE messages ALTER COLUMN sender_id TYPE bigint')


def downgrade() -> None:
    # Note: This might fail if any values are too large for INTEGER
    op.execute('ALTER TABLE messages ALTER COLUMN sender_id TYPE integer')
    op.execute('ALTER TABLE requests ALTER COLUMN assigned_admin TYPE integer')
    op.execute('ALTER TABLE requests ALTER COLUMN user_id TYPE integer') 