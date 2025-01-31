from odoo import http
from odoo.http import request
import json
from odoo.exceptions import AccessDenied
import werkzeug.exceptions


def validate_api_key(api_key):
    """Validate the API key and return the associated user if valid"""
    if not api_key:
        return None
    api_key_record = request.env['api.key'].sudo().search([
        ('key', '=', api_key),
        ('active', '=', True)
    ], limit=1)
    return api_key_record.user_id if api_key_record else None

#product_list_api
class DimensionProduitAPI(http.Controller):

    @http.route("/api/dimension_produit", auth='none', type='http', methods=['GET'], csrf=False)
    def get_dimension_produit(self, **kwargs):
        try:
            api_key = request.httprequest.headers.get('Authorization')

            user = validate_api_key(api_key)
            if not user:
                return http.Response(
                    json.dumps({"error": "Invalid or missing API key"}),
                    status=401,
                    content_type="application/json"
                )

            if not user.has_group('base.group_system'):
                return http.Response(
                    json.dumps({"error": "Access Denied", "details": "This API requires admin access"}),
                    status=403,
                    content_type="application/json"
                )

            request.update_env(user=user)

            # Fetch all products
            products = request.env['product.template'].sudo().search([])

            produit_data = []
            for product in products:
                # Fetch POS categories
                pos_categories = [category.name for category in product.pos_categ_ids] if product.pos_categ_ids else None

                # Fetch taxes
                taxes = [tax.name for tax in product.taxes_id] if product.taxes_id else None

                # Fetch supplier information
                supplier_info = []
                for supplier in product.seller_ids:
                    supplier_info.append({
                        "Nom du fournisseur": supplier.display_name,
                        "Prix": supplier.price,
                        "Devise": supplier.currency_id.name if supplier.currency_id else None
                    })

                # Fetch price from pricelist item (if exists)
                pricelist_item = request.env['product.pricelist.item'].sudo().search([
                    ('product_tmpl_id', '=', product.id),
                    ('pricelist_id.active', '=', True)
                ], limit=1)

                product_price = pricelist_item.fixed_price if pricelist_item else None

                stock_quantities = {}
                stock_records = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', product.product_variant_id.id)  # Fetch for specific variant
                ])

                for stock in stock_records:
                    location_name = stock.location_id.complete_name
                    stock_quantities[location_name] = stock.quantity


                # Append product data
                produit_data.append({
                    #"produit_id": product.id,
                    "Nom du Produit": product.name,
                    "Code barre": product.barcode,
                    "default code": product.default_code,
                    "Item ID": product.x_studio_item_id,
                    "Coût": product.standard_price,
                    "Prix de vente": product_price,
                    "HS Code": product.x_studio_hs_code,
                    "Collection": product.x_studio_origine_pays,
                    "Composition": product.x_studio_composition,
                    "Type de produit": product.detailed_type,
                    #"product_type": product.type,
                    "Politique de fabrication": product.invoice_policy,
                    "stock selon l'emplacement": stock_quantities,
                    "Catégorie de produit": product.categ_id.name,
                    "Marque du produit": pos_categories,
                    "Disponible en POS": product.available_in_pos,
                    "Taxes": taxes,  # Added taxes
                    "Informations fournisseur": supplier_info,

                })

            return request.make_json_response(produit_data, status=200)

        except werkzeug.exceptions.Unauthorized as e:
            return http.Response(
                json.dumps({"error": "Authentication Required", "details": str(e)}),
                status=401,
                content_type="application/json"
            )
        except werkzeug.exceptions.Forbidden as e:
            return http.Response(
                json.dumps({"error": "Access Denied", "details": str(e)}),
                status=403,
                content_type="application/json"
            )
        except Exception as e:
            error_message = f"Error fetching Dimension_produit: {str(e)}"
            request.env.cr.rollback()
            return http.Response(
                json.dumps({"error": "Internal Server Error", "details": error_message}),
                status=500,
                content_type="application/json"
            )

#sales_api
class PosOrderAPI(http.Controller):

    @http.route("/api/pos_ventes", auth='none', type='http', methods=['GET'], csrf=False)
    def get_pos_orders(self, id_produit=None, id_magasin=None, id_client=None, date_debut=None, date_fin=None, **kwargs):
        try:
            api_key = request.httprequest.headers.get('Authorization')
            user = validate_api_key(api_key)
            if not user:
                return http.Response(
                    json.dumps({"error": "Invalid or missing API key"}),
                    status=401,
                    content_type="application/json"
                )

            request.update_env(user=user)

            # Construire le domaine de recherche
            domain = []

            if id_magasin:
                domain.append(('config_id', '=', int(id_magasin)))

            if id_client:
                domain.append(('partner_id', '=', int(id_client)))

            if date_debut and date_fin:
                domain.append(('date_order', '>=', date_debut))
                domain.append(('date_order', '<=', date_fin))

            pos_orders = request.env['pos.order'].sudo().search(domain)

            pos_data = []
            for order in pos_orders:
                order_lines = []
                for line in order.lines:
                    # Filtrer aussi par ID produit
                    if id_produit and line.product_id.id != int(id_produit):
                        continue

                    order_lines.append({
                        "id_produit": line.product_id.id,  # ID du produit
                        "Nom": line.product_id.display_name,
                        "Quantité": line.qty,
                        "Note du client": line.customer_note or "",
                        "discount": line.discount,
                        "Prix": line.price_subtotal_incl,
                    })

                if not order_lines:
                    continue  # Si aucun produit ne correspond au filtre, on ignore cette commande

                pos_data.append({
                    "Ref": order.name,
                    "Session": order.session_id.id if order.session_id else "None",
                    "Date de commande": order.date_order,
                    #"Magasin": order.config_id.id if order.config_id else None,
                    "Nom du Magasin": order.config_id.name if order.config_id else "None",# ID du magasin
                    "Ticket de caisse": order.pos_reference,
                    #"Client id": order.partner_id.id if order.partner_id else None,  # ID du client
                    "Nom du client": order.partner_id.name if order.partner_id else "",
                    "Caissier": order.employee_id.name if order.employee_id else "",
                    "Nom du vendeur": order.suggestion if order.suggestion else "",
                    #"amount_total": order.amount_total,
                    "Produits achetés": order_lines,
                })

            return request.make_json_response(pos_data, status=200)

        except Exception as e:
            error_message = f"Error fetching POS orders: {str(e)}"
            request.env.cr.rollback()
            return http.Response(
                json.dumps({"error": "Internal Server Error", "details": error_message}),
                status=500,
                content_type="application/json"
            )

#payment_methedo_api
class PosPaymentAPI(http.Controller):

    @http.route("/api/pos_payments", auth='none', type='http', methods=['GET'], csrf=False)
    def get_pos_payments(self, id_magasin=None, id_client=None, id_produit=None, date_debut=None, date_fin=None, **kwargs):
        try:
            api_key = request.httprequest.headers.get('Authorization')
            user = validate_api_key(api_key)
            if not user:
                return http.Response(
                    json.dumps({"error": "Invalid or missing API key"}),
                    status=401,
                    content_type="application/json"
                )

            request.update_env(user=user)

            # Construire le domaine de recherche
            domain = []

            if id_magasin:
                domain.append(('session_id.config_id', '=', int(id_magasin)))

            if id_client:
                domain.append(('partner_id', '=', int(id_client)))

            if date_debut and date_fin:
                domain.append(('date_order', '>=', date_debut))
                domain.append(('date_order', '<=', date_fin))

            if id_produit:
                domain.append(('lines.product_id', '=', int(id_produit)))

            pos_orders = request.env['pos.order'].sudo().search(domain)

            payment_data = []
            for order in pos_orders:
                payment_methods = {}

                for payment in order.payment_ids:
                    payment_methods[payment.payment_method_id.name] = payment.amount

                payment_data.append({
                    "Nom du Magasin": order.config_id.name if order.config_id else "None",
                    "Session": order.session_id.name if order.session_id else "None",
                    "Ticket de caisse": order.pos_reference,
                    "Caissier": order.employee_id.name if order.employee_id else "None",
                    "Date de commande": order.date_order,
                    "Vendeur": order.suggestion if order.suggestion else "",
                    #"id_client": order.partner_id.id if order.partner_id else None,
                    "Nom du Client": order.partner_id.name if order.partner_id else "None",
                    "Méthodes de paiement": payment_methods
                })

            return request.make_json_response(payment_data, status=200)

        except Exception as e:
            error_message = f"Error fetching POS payments: {str(e)}"
            request.env.cr.rollback()
            return http.Response(
                json.dumps({"error": "Internal Server Error", "details": error_message}),
                status=500,
                content_type="application/json"
            )

#achat
class PurchaseOrderAPI(http.Controller):
    @http.route("/api/purchase_orders", auth='none', type='http', methods=['GET'], csrf=False)
    def get_purchase_orders(self, id_fournisseur=None, id_user=None, date_debut=None, date_fin=None, **kwargs):
        try:
            api_key = request.httprequest.headers.get('Authorization')
            user = validate_api_key(api_key)
            if not user:
                return http.Response(
                    json.dumps({"error": "Invalid or missing API key"}),
                    status=401,
                    content_type="application/json"
                )

            request.update_env(user=user)

            # Construire le domaine de recherche
            domain = []

            if id_fournisseur:
                domain.append(('partner_id', '=', int(id_fournisseur)))

            if id_user:
                domain.append(('user_id', '=', int(id_user)))

            if date_debut and date_fin:
                domain.append(('date_approve', '>=', date_debut))
                domain.append(('date_approve', '<=', date_fin))

            purchase_orders = request.env['purchase.order'].sudo().search(domain)

            purchase_data = []
            for po in purchase_orders:
                total_qty = sum(po.order_line.mapped('product_qty'))
                total_received = sum(po.order_line.mapped('qty_received'))

                purchase_data.append({
                    "Bon De Commande": po.name,
                    "Date de confirmation": po.date_approve,
                    "Fournisseur": po.partner_id.name if po.partner_id else "",
                    "Livrer à" : po.picking_type_id.name if po.picking_type_id else "",
                    #"partner_name": po.partner_id.name if po.partner_id else None,
                    #"user_id": po.user_id.id if po.user_id else None,
                    #"Utilisateur": po.user_id.name if po.user_id else None,
                    "Document D'origine": po.origin if po.origin else "",
                    "DD Impot": po.x_studio_dd_impot if po.x_studio_dd_impot else "",
                    "Num Fact Fournisseur": po.x_studio_num_fact_frs if po.x_studio_num_fact_frs else "",
                    "Total": po.amount_total,
                    "Quantité commandée": total_qty,
                    "Quantité reçue": total_received
                })

            return request.make_json_response(purchase_data, status=200)

        except Exception as e:
            error_message = f"Error fetching purchase orders: {str(e)}"
            request.env.cr.rollback()
            return http.Response(
                json.dumps({"error": "Internal Server Error", "details": error_message}),
                status=500,
                content_type="application/json"
            )

# stock :
