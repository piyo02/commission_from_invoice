from odoo import api, exceptions, fields, models, _
import logging
from datetime import date, datetime, timedelta

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

        # date_to = date.today()
        date_to = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        date_from = date_to - timedelta(days=self.day_term)
        if not self.agent_id:
            self.agent_id = self.env['res.partner'].search(
                [('agent', '=', True)])
        invoice_has_get = []
        for agent in self.agent_id:
            payments = self.env['account.payment'].search([
                ('payment_date', '>=', self.start_date),
                ('payment_date', '<=', self.end_date),
                ('payment_type', '=', 'inbound'),
                ('state', '=', 'posted'),
            ])
            list_invoice = []
            for payment in payments:
                for invoice in payment.invoice_ids:
                    date_invoice = datetime.strptime(invoice.date_invoice, "%Y-%m-%d").date()
                    if invoice.settled or date_invoice < date_from or invoice.state != 'paid' or invoice.user_id.name != agent.name or invoice.id in invoice_has_get:
                        continue
                    
                    detail = []
                    detail.append(invoice)
                    list_invoice.append(detail)
                    invoice_has_get.append(invoice.id)
                
            giros = self.env['vit.giro'].search([
                ('clearing_date', '>=', self.start_date),
                ('clearing_date', '<=', self.end_date),
                ('state', '=', 'close'),
                ('type', '=', 'receipt'),
            ])
            for giro in giros:
                for giro_line in giro.giro_invoice_ids:
                    invoice = giro_line.invoice_id
                    date_invoice = datetime.strptime(invoice.date_invoice, "%Y-%m-%d").date()
                    if invoice.settled or date_invoice <  date_from or invoice.state != 'paid' or invoice.user_id.name != agent.name or invoice.id in invoice_has_get:
                        continue

                    detail = []
                    detail.append(invoice)
                    list_invoice.append(detail)
                    invoice_has_get.append(invoice)

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