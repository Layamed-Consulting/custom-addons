from odoo import fields, models,api

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    cheque_date = fields.Date(
        string='Date du chèque',
        related='pos_order_id.cheque_date',
        readonly=True,
        help='The date associated with the cheque payment from the POS order.'
    )

    @api.depends('payment_method_id')
    def _compute_field_visibility(self):
        for record in self:
            method = record.payment_method_id.name
            record.show_stan = method == 'Carte Bancaire'
            record.show_cheque_fields = method in ['Chèque', 'Chèque MDC']
            record.show_date = method == 'Chèque MDC'
            record.show_identite = method in ['Chèque MDC', 'Chèque']

    show_stan = fields.Boolean(compute='_compute_field_visibility')
    show_cheque_fields = fields.Boolean(compute='_compute_field_visibility')
    show_date = fields.Boolean(compute='_compute_field_visibility')
    show_identite = fields.Boolean(compute='_compute_field_visibility')
