from alembic import op
import sqlalchemy as sa

revision = '000001_k8s_deployment'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'k8s_deployment',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('service_name', sa.String(255), nullable=True),
        sa.Column('pod_cpu', sa.String(255), nullable=True),
        sa.Column('pod_ram', sa.String(255), nullable=True),
        sa.Column('autoscaling', sa.Boolean, nullable=True),
        sa.Column('min_replicas', sa.Integer, nullable=True),
        sa.Column('max_replicas', sa.Integer, nullable=True),
        sa.Column('current_replicas', sa.Integer, nullable=True)
    )

def downgrade():
    op.drop_table('k8s_deployment')