"""add email notification logs table

Revision ID: zz4d5e6f7a8b
Revises: zz3c4d5e6f7a
Create Date: 2026-09-03 11:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'zz4d5e6f7a8b'
down_revision = 'zz3c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'email_notification_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.BigInteger(), nullable=True, comment='ID transaksi peminjaman terkait'),
        sa.Column('admin_user_id', sa.BigInteger(), nullable=True, comment='ID user admin penerima'),
        sa.Column('recipient_email', sa.String(length=100), nullable=False, comment='Alamat email penerima'),
        sa.Column('notification_type', sa.String(length=50), nullable=False, comment='Jenis notifikasi'),
        sa.Column('subject', sa.String(length=255), nullable=False, comment='Subjek email'),
        sa.Column('status', sa.String(length=20), server_default='success', nullable=False, comment='Status'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Pesan error jika gagal'),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Waktu pengiriman'),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['transaction_id'], ['borrow_transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('email_notification_logs')
