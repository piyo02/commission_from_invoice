from odoo import api, fields, models
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    commission = fields.Many2one(
        comodel_name="sale.commission",
        ondelete="restrict",
        compute="change_commission",
        related="user_id.commission",
        required=True,
    )

    @api.depends('user_id')
    def change_commission(self):
        self.commission = self.user_id.commission