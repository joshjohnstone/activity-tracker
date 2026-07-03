"""Add activity category and exercise relationship

Revision ID: 97501465d46b
Revises: 08f2ee178c67
Create Date: 2026-07-03 14:56:50.476954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97501465d46b'
down_revision = '08f2ee178c67'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.add_column(
            sa.Column(
                "activity_category",
                sa.String(length=50),
                nullable=False,
                server_default="Strength"
            )
        )
        batch_op.add_column(
            sa.Column(
                "lift_category",
                sa.String(length=50),
                nullable=True
            )
        )
        batch_op.alter_column(
            "category",
            existing_type=sa.String(length=50),
            nullable=True
        )

    op.execute(
        "UPDATE exercises SET lift_category = category "
        "WHERE lift_category IS NULL"
    )

    with op.batch_alter_table("activities") as batch_op:
        batch_op.add_column(
            sa.Column(
                "exercise_id",
                sa.Integer(),
                nullable=True
            )
        )
        batch_op.create_foreign_key(
            "fk_activities_exercise_id_exercises",
            "exercises",
            ["exercise_id"],
            ["id"]
        )


def downgrade():
    with op.batch_alter_table("activities") as batch_op:
        batch_op.drop_constraint(
            "fk_activities_exercise_id_exercises",
            type_="foreignkey"
        )
        batch_op.drop_column("exercise_id")

    with op.batch_alter_table("exercises") as batch_op:
        batch_op.alter_column(
            "category",
            existing_type=sa.String(length=50),
            nullable=False
        )
        batch_op.drop_column("lift_category")
        batch_op.drop_column("activity_category")
