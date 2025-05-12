# -*- coding: utf-8 -*-
######################################################################################
#
#    CnEL India
#
#    Copyright (C) 2021-TODAY Cnel India(<https://cnelindia.com>).
#    Author: Gulshan Saini (odoo@cnelindia.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import models, fields, api


class ProductLabelsHwe(models.Model):
    _inherit = 'product.tag'

    woo_id = fields.Char(string="WooCommerce ID", readonly=True, copy=False)

class InheritedProductTemplateHwe(models.Model):
    _inherit = 'product.template'

    woo_id = fields.Char(string="WooCommerce ID",copy=False)
    instance_id = fields.Many2one('woo.commerce', string="Connection",
                                  readonly=True, copy=False)
    woo_variant_check = fields.Boolean(readonly=True, copy=False)


    def unlink(self):
        """
        For deleting on both Connection
        .
        """
        for recd in self:
            if recd.woo_id and recd.instance_id:
                wcapi = recd.instance_id.get_api()
                wcapi.delete("products/" + recd.woo_id + "", params={"force": True}).json()
        return super(InheritedProductTemplateHwe, self).unlink()

    @api.model
    def get_product_graph_hwe(self):
        """
        For getting product graph.
        """
        woo_products = self.env['product.template'].search([('woo_id', '!=', False)])
        products_details = []
        for product in woo_products:
            products_details.append({
                'id': product.id,
                'name': product.name,
                'quantity': product.qty_available,
                'price': product.list_price,
            })
        return products_details


class InheritedProductHwe(models.Model):
    _inherit = 'product.product'

    woo_price = fields.Float(string="woo price", copy=False)
    woo_var_id = fields.Char(string="Woo Variant ID", readonly=True,
                             copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        context_val = self._context
        if self._context.get('woocommerce_variant') and self._context.get('variant_vals'):
            for i in range(len(vals_list)):
                vals_list[i].update(context_val['variant_vals'][i])
        val = super(InheritedProductHwe,self).create(vals_list)
        return val


    def unlink(self):
        """
        For deleting on both instances.
        """
        for recd in self:
            if recd.woo_var_id:
                wcapi = recd.product_tmpl_id.instance_id.get_api()
                wcapi.delete("products/" + recd.product_tmpl_id.woo_id + "/variations/" + recd.woo_var_id + "",
                             params={"force": True}).json()
        return super(InheritedProductHwe, self).unlink()

    @api.depends('list_price', 'price_extra')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        """
        function is override for Changing Variant Price
        based on the woo price.

        """
        for recd in self:
            product_id = self.env['product.template'].search([('product_variant_ids', 'in', recd.id)])
            if not product_id.woo_variant_check:
                to_uom = None
                if 'uom' in self._context:
                    to_uom = self.env['uom.uom'].browse(self._context['uom'])

                for product in self:
                    if to_uom:
                        list_price = product.uom_id._compute_price(product.list_price, to_uom)
                    else:
                        list_price = product.list_price
                    product.lst_price = list_price + product.price_extra
            else:
                if recd.woo_price == 0:
                    recd.lst_price = recd.product_tmpl_id.list_price
                else:
                    recd.lst_price = recd.woo_price


class InheritedResPartnerHwe(models.Model):
    _inherit = 'res.partner'

    woo_id = fields.Char(string="WooCommerce ID", readonly=True, copy=False)
    woo_user_name = fields.Char(string="User Name", readonly=True, copy=False)
    instance_id = fields.Many2one('woo.commerce', string="Connection",
                                  readonly=True, copy=False)

class InheritSaleOrderHwe(models.Model):
    _inherit = 'sale.order'

    woo_id = fields.Char(string="WooCommerce ID", copy=False)
    woo_order_key = fields.Char(string="Order Key", readonly=True, copy=False)
    instance_id = fields.Many2one('woo.commerce', string="Connecton",
                                  readonly=True, copy=False)
    woo_order_status = fields.Char('WooCommerce Order Status', readonly=True,
                                   copy=False)
    state_check = fields.Boolean(compute='state_change')
    woo_coupon_ids = fields.One2many('woo.order.coupons', 'woo_order_id',
                                     string="Woo Coupon Details",
                                     readonly=True, copy=False)

    def state_change(self):
        """
        For computing invoiced quantity based on the woo status.
        """
        if self.woo_order_status != 'completed':
            for order in self.order_line:
                order.qty_invoiced = 0
        self.state_check = True

    @api.model
    def get_tile_details(self):
        instance = self.env['woo.commerce'].search([])
        products = self.env['product.template'].search([('woo_id', '!=', False)])
        partners = self.env['res.partner'].search([('woo_id', '!=', False)])
        orders = self.env['sale.order'].search([('woo_id', '!=', False)])
        tile_details = {
            'instance': len(instance.ids),
            'products': len(products.ids),
            'partners': len(partners.ids),
            'orders': len(orders.ids),
        }
        return tile_details

    @api.model
    def get_orders(self):
        orders = self.env['sale.order'].search([('woo_id', '!=', False)])
        orders_list = []
        for order in orders:
            if order.invoice_status == 'no':
                status = 'Nothing to Invoice'
            elif order.invoice_status == 'to invoice':
                status = 'To Invoice'
            elif order.invoice_status == 'invoiced':
                status = 'Fully Invoiced'
            else:
                status = 'Upselling Opportunity'
            orders_list.append({
                'name': order.name,
                'date_order': order.date_order,
                'customer': order.partner_id.name,
                'total': order.amount_total,
                'status': status,})
        return orders_list


class WooCommerceOrderCouponsHwe(models.Model):
    _name = 'woo.order.coupons'
    _description = "Woo Order Coupons"

    woo_coupon_id = fields.Char('Woo ID', readonly=True, copy=False)
    coupon_code = fields.Char("Coupon Code", readonly=True, copy=False)
    discount_amount = fields.Float("Discount Amount", readonly=True,
                                   copy=False)
    tax_discount = fields.Float("Tax Discount", readonly=True, copy=False)
    woo_order_id = fields.Many2one('sale.order', copy=False)


class InheritedAccountTaxHwe(models.Model):
    _inherit = 'account.tax'

    woo_id = fields.Char(string="WooCommerce ID", readonly=True, copy=False)
    instance_id = fields.Many2one('woo.commerce', string="Connection",
                                  readonly=True, copy=False)
    tax_class = fields.Char(string="Tax Class", readonly=True, copy=False)


class InheritedProductCategoryHwe(models.Model):
    _inherit = 'product.category'

    woo_id = fields.Char(string="WooCommerce ID", readonly=True, copy=False)
    instance_id = fields.Many2one('woo.commerce', string="Connection",
                                  readonly=True, copy=False)

    @api.model
    def get_product_category_graph(self):
        categrories = self.env['product.category'].search([
            ('woo_id', '!=', False)])
        categories_name = []
        products_count = []
        for category in categrories:
            products = self.env['product.template'].search([
                ('categ_id', '=', category.id)])
            categories_name.append(category.name)
            products_count.append(len(products.ids))
        return {
            'categories_name': categories_name,
            'products_count': products_count
        }


class InheritedProductAttributeHwe(models.Model):
    _inherit = 'product.attribute'

    woo_id = fields.Char(string="", readonly=True, copy=False)
    instance_id = fields.Many2one('woo.commerce', string="Instance",
                                  readonly=True, copy=False)
