"""Información pública por negocio."""
from alembic import op
import sqlalchemy as sa

revision = "c011knowledge"
down_revision = "b010team"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.String(50), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_knowledge_documents_business_id", "knowledge_documents", ["business_id"])


def downgrade():
    op.drop_table("knowledge_documents")
