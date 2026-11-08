"""Catálogo y horario del cliente: SPEC-009."""
from alembic import op
import sqlalchemy as sa

revision = "a915c009e003"
down_revision = "f814b008d002"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("services") as batch:
        batch.add_column(sa.Column("duration_minutes", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))
        batch.create_check_constraint("ck_service_duration", "duration_minutes IS NULL OR (duration_minutes >= 5 AND duration_minutes <= 480)")
    op.create_table("business_hours",
        sa.Column("business_id", sa.String(50), sa.ForeignKey("businesses.id"), primary_key=True),
        sa.Column("weekday", sa.Integer(), primary_key=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False),
        sa.Column("opens_at", sa.Integer(), nullable=True),
        sa.Column("closes_at", sa.Integer(), nullable=True),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_hours_weekday"),
        sa.CheckConstraint("(is_closed AND opens_at IS NULL AND closes_at IS NULL) OR "
                           "(NOT is_closed AND opens_at IS NOT NULL AND closes_at IS NOT NULL "
                           "AND opens_at >= 0 AND closes_at <= 1439 AND opens_at < closes_at)", name="ck_hours_interval"),
    )


def downgrade():
    op.drop_table("business_hours")
    with op.batch_alter_table("services") as batch:
        batch.drop_constraint("ck_service_duration", type_="check")
        batch.drop_column("is_active")
        batch.drop_column("duration_minutes")
