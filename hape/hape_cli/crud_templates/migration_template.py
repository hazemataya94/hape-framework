MIGRATION_TEMPLATE = """
from alembic import op
import sqlalchemy as sa

revision = '{{migration_counter}}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    {{model_table_creation_statements}}
def downgrade():
    {{model_table_drop_statements}}
""".strip()

MIGRATION_MODEL_TABLE_CREATION_TEMPLATE = """
    op.create_table(
        '{{model_name_snake_case}}',
        {{migration_columns}}
    )
""".strip()

MIGRATION_MODEL_TABLE_DROP_TEMPLATE = """
    op.drop_table('{{model_name_snake_case}}')
""".strip()
