"""add upts table and handover recipient

Revision ID: zz6f7a8b9c0d
Revises: zz5e6f7a8b9c
Create Date: 2026-09-13 18:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'zz6f7a8b9c0d'
down_revision = 'zz5e6f7a8b9c'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Buat tabel upts
    op.create_table(
        'upts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False, comment='Nama UPT BMKG'),
        sa.Column('address', sa.Text(), nullable=True, comment='Alamat UPT (opsional)'),
        sa.Column('phone', sa.String(length=50), nullable=True, comment='Kontak UPT (opsional)'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='Timestamp saat UPT dihapus (soft delete)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Tambah kolom upt_id, recipient_name, recipient_nip ke tabel handovers
    op.add_column(
        'handovers',
        sa.Column('upt_id', sa.BigInteger(), nullable=True, comment='ID referensi UPT penerima')
    )
    op.add_column(
        'handovers',
        sa.Column('recipient_name', sa.String(length=100), nullable=True, comment='Nama pihak/petugas penerima di UPT')
    )
    op.add_column(
        'handovers',
        sa.Column('recipient_nip', sa.String(length=30), nullable=True, comment='NIP pihak/petugas penerima di UPT')
    )

    # 3. Foreign key upt_id ke tabel upts
    op.create_foreign_key(
        'fk_handovers_upt_id',
        'handovers', 'upts',
        ['upt_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_handovers_upt_id', 'handovers', type_='foreignkey')
    op.drop_column('handovers', 'recipient_nip')
    op.drop_column('handovers', 'recipient_name')
    op.drop_column('handovers', 'upt_id')
    op.drop_table('upts')
