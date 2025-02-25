"""Auto-merge multiple Alembic heads

Revision ID: b8baabc0df98
Revises: 000001_k8s_deployment, 000002_k8s_deployment_cost
Create Date: 2025-02-21 21:39:20.885129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8baabc0df98'
down_revision: Union[str, None] = ('000001_k8s_deployment', '000002_k8s_deployment_cost')
branch_labels: Union[str, Sequence[str], None] = ('merge_heads',)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
