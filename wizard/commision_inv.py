from odoo import api, exceptions, fields, models, _
import logging
from datetime import date, timedelta

_logger = logging.getLogger(__name__)
class CommissionInvoices(models.Model):
    _name = "sale.commission.invoice"

    agent_id = fields.Many2many(
        comodel_name="res.partner",
        ondelete="restrict",
        string="Sales",
        domain="[('agent', '=', True)]"
    )
    day_term = fields.Integer(
        string="Umur Piutang",
        required=True,
        default=63 
    )
    start_date = fields.Date('Tanggal Awal', required=True )
    end_date = fields.Date('Tanggal Akhir', required=True )
    
    @api.multi
    def create_commission(self):
        self.ensure_one()
        settlement_obj = self.env['sale.commission.settlement']
        settlement_line_obj = self.env['sale.commission.settlement.line']
        settlement_ids = []

        date_to = date.today()
        date_from = date_to - timedelta(days=self.day_term)

        if not self.agent_id:
            self.agent_id = self.env['res.partner'].search(
                [('agent', '=', True)])
        
        invoice_has_get = []
        for agent in self.agent_id:
            invoices = self.env['account.invoice'].search([
                ('date_invoice', '>=', date_from),
                ('date_invoice', '<=', date_to),
                ('user_id.name', '=', agent.name),
                ('settled', '=', False),
                ('type', '=', 'out_invoice'),
            ], order="date_invoice")

            list_invoice = []
            for invoice in invoices:
                if invoice.id in invoice_has_get:
                    continue
                
                detail = []
                detail.append(invoice)
                list_invoice.append(detail)

            if len(list_invoice):
                settlement = settlement_obj.create({
                    'agent': agent.id,
                    'date_from': self.start_date,
                    'date_to': self.end_date,
                })
                settlement_ids.append(settlement.id)

                for invoice in list_invoice:
                    settlement_line_obj.create({
                        'settlement': settlement.id,
                        'invoice': invoice[0].id,
                        'date': invoice[0].date_invoice,
                        'total_invoice': invoice[0].amount_total})
                    
        if len(settlement_ids):
            return {
                'name': _('Created Settlements'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'sale.commission.settlement',
                'domain': [['id', 'in', settlement_ids]],
            }

        else:
            return {'type': 'ir.actions.act_window_close'}