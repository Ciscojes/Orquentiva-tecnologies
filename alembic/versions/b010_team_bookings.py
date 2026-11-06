"""Agenda por profesional."""
from alembic import op
import sqlalchemy as sa

revision = "b010team"
down_revision = "a915c009e003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("businesses", sa.Column("booking_enabled", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.create_table("professionals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.String(50), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("service_ids", sa.JSON(), nullable=False),
        sa.Column("days", sa.JSON(), nullable=False))
    with op.batch_alter_table("appointments") as b:
        b.drop_constraint("uq_appointment_business_time", type_="unique")
        b.add_column(sa.Column("professional_id", sa.Integer()))
        b.add_column(sa.Column("service_id", sa.Integer()))
        b.add_column(sa.Column("ends_at", sa.DateTime(timezone=True)))
        b.add_column(sa.Column("request_key", sa.String(36)))
        b.create_foreign_key("fk_booking_prof", "professionals", ["professional_id"], ["id"])
        b.create_foreign_key("fk_booking_service", "services", ["service_id"], ["id"])
        b.create_unique_constraint("uq_booking_request", ["business_id", "request_key"])
        b.create_unique_constraint("uq_prof_time", ["professional_id", "starts_at"])
    op.create_index("uq_legacy_time", "appointments", ["business_id","starts_at"], unique=True,
                    postgresql_where=sa.text("professional_id IS NULL"), sqlite_where=sa.text("professional_id IS NULL"))


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM professionals LIMIT 1")).first():
        raise RuntimeError("Downgrade would discard professional schedules")
    op.drop_index("uq_legacy_time", table_name="appointments")
    with op.batch_alter_table("appointments") as b:
        for name in ("fk_booking_prof", "fk_booking_service"):
            b.drop_constraint(name,type_="foreignkey")
        for name in ("uq_booking_request","uq_prof_time"):
            b.drop_constraint(name,type_="unique")
        for name in ("request_key","ends_at","professional_id","service_id"):
            b.drop_column(name)
        b.create_unique_constraint("uq_appointment_business_time", ["business_id","starts_at"])
    op.drop_table("professionals")
    op.drop_column("businesses","booking_enabled")
