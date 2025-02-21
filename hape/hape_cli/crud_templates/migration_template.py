MIGRATION_TEMPLATE = """
from alembic import op
import sqlalchemy as sa

revision = '{{migration_counter}}_{{model_name_snake_case}}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        '{{model_name_snake_case}}',
        {{migration_columns}}
    )

def downgrade():
    op.drop_table('{{model_name_snake_case}}')
""".strip()