from odoo import api, fields, models,_

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    testfield = fields.Char(string="Test field")

    pricelist_price = fields.Float(
        string="Prix de vente",
        compute="_compute_pricelist_price",
        store=False
    )
    copied_category = fields.Many2one(
        'product.category',
        string="Catégorie de Produit",
        compute='_compute_copied_category',
        store=True
    )

    @api.depends('categ_id')
    def _compute_copied_category(self):
        for product in self:
            product.copied_category = product.categ_id

    def _compute_pricelist_price(self):
        for product in self:
            pricelist_item = self.env['product.pricelist.item'].search([
                ('product_tmpl_id', '=', product.id)
            ], limit=1)
            product.pricelist_price = pricelist_item.fixed_price if pricelist_item else 0.0