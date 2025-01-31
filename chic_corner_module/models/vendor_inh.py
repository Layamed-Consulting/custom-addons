from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
  _inherit = 'pos.order'

  cheque_date = fields.Date(string="Date du Chèque", help="Date of the cheque.")

  def _order_fields(self, ui_order):
    result = super()._order_fields(ui_order)
    _logger.debug("UI Order: %s", ui_order)
    result['cheque_date'] = ui_order.get('cheque_date')
    return result



