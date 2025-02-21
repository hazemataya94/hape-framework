MIGRATION_TEMPLATE = """
from alembic import op
import sqlalchemy as sa

revision = '{{migration_counter}}_create_{{model_name_snake_case}}_table'
down_revision = '{{migration_down_counter}}_create_{{migration_down_model_name_snake_case}}_table'
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