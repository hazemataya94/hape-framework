from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = '001_create_deployment_cost'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'deployment_costs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.BigInteger, nullable=False),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('pod_cpu', sa.String(50), nullable=False),
        sa.Column('pod_ram', sa.String(50), nullable=False),
        sa.Column('autoscaling', sa.Boolean, nullable=False),
        sa.Column('min_replicas', sa.Integer, nullable=True),
        sa.Column('max_replicas', sa.Integer, nullable=True),
        sa.Column('current_replicas', sa.Integer, nullable=False),
        sa.Column('pod_cost', sa.Float, nullable=False),
        sa.Column('number_of_pods', sa.Integer, nullable=False),
        sa.Column('total_cost', sa.Float, nullable=False),
        sa.Column('cost_unit', sa.String(50), nullable=False),
    )

def downgrade():
    op.drop_table('deployment_costs')
