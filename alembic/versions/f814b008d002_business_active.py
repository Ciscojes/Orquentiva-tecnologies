"""Estado de negocios para el panel administrativo SPEC-008."""
from alembic import op
import sqlalchemy as sa

revision = "f814b008d002"
down_revision = "e713a007c001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("businesses", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade():
    op.drop_column("businesses", "is_active")
