from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    commission = fields.Many2one(
        comodel_name="sale.commission",
        ondelete="restrict",
        compute="change_commission",
        related="user_id.commission",
        required=True,
    )

    settled = fields.Boolean(
        string="Settled", readonly=True, default=False
    )

    @api.depends('user_id')
    def change_commission(self):
        self.commission = self.user_id.commission