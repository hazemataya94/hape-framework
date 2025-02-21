from alembic import op
import sqlalchemy as sa

revision = '000002_k8s_deployment_cost'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'k8s_deployment_cost',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('k8s_deployment_id', sa.Integer, sa.ForeignKey('k8s_deployment.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pod_cost', sa.String(255), nullable=True),
        sa.Column('number_of_pods', sa.Integer, nullable=True),
        sa.Column('total_cost', sa.Float, nullable=True)
    )

def downgrade():
    op.drop_table('k8s_deployment_cost')