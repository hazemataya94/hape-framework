from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = '0000_my_model'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'my_model',
        
    )

def downgrade():
    op.drop_table('my_model')