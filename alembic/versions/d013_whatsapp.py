"""Durable WhatsApp inbox and conversation drafts."""
from alembic import op
import sqlalchemy as sa

revision = "d013whatsapp"
down_revision = "c011knowledge"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("whatsapp_conversations",
        sa.Column("business_id", sa.String(50), sa.ForeignKey("businesses.id"), primary_key=True),
        sa.Column("sender", sa.String(128), primary_key=True),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("whatsapp_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.String(256), unique=True, nullable=False),
        sa.Column("business_id", sa.String(50), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("phone_id", sa.String(128), nullable=False),
        sa.Column("sender", sa.String(128), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_table("whatsapp_messages")
    op.drop_table("whatsapp_conversations")
