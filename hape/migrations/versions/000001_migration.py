from alembic import op
import sqlalchemy as sa

revision = '000001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'k8s_deployment',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('pod_cpu', sa.String(255), nullable=False),
        sa.Column('pod_ram', sa.String(255), nullable=False),
        sa.Column('autoscaling', sa.Boolean, nullable=False),
        sa.Column('min_replicas', sa.Integer, nullable=True),
        sa.Column('max_replicas', sa.Integer, nullable=True),
        sa.Column('current_replicas', sa.Integer, nullable=False)
    )
    op.create_table(
        'k8s_deployment_cost',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('k8s_deployment_id', sa.Integer, sa.ForeignKey('k8s_deployment.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pod_cost', sa.String(255), nullable=False),
        sa.Column('number_of_pods', sa.Integer, nullable=False),
        sa.Column('total_cost', sa.Float, nullable=False)
    )
    
def downgrade():
    op.drop_table('k8s_deployment')
    op.drop_table('k8s_deployment_cost')
    