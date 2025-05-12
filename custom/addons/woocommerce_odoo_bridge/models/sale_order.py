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

from odoo import models,_
from woocommerce import API


class SalesOrderHwe(models.Model):
    _inherit = 'sale.order'
    _description = "Inheriting Sale Order"

    def write(self, vals):
        if self.instance_id:
            app = API(
                url="" + self.instance_id.store_url + "/index.php/",  # Your Website URL
                consumer_key=self.instance_id.consumer_key,  # Your consumer key
                consumer_secret=self.instance_id.consumer_secret,  # Your consumer secret
                wp_api=True,  # Enable the WP REST API integration
                version="wc/v3",  # WooCommerce WP REST API version
                timeout=500,
            )
            status = 'processing'
            if self.state == 'sent':
                status = 'processing'
            elif self.state == 'draft':
                status = 'draft'
            elif self.state == 'cancel':
                status = 'cancelled'
            elif self.state == 'sale':
                status = 'completed'
            val_list = {
                'status': status
            }
            app.put(f"orders/{self.woo_id}", val_list).json()

        return super(SalesOrderHwe, self).write(vals)

    def unlink(self):
        for order in self:
            if order.instance_id:
                app = API(
                    url="" + self.instance_id.store_url + "/index.php/",  # Your website URL
                    consumer_key=self.instance_id.consumer_key,  # Your consumer key
                    consumer_secret=self.instance_id.consumer_secret,  # Your consumer secret
                    wp_api=True,  # Enable the WP REST API integration
                    version="wc/v3",  # WooCommerce WP REST API version
                    timeout=500,
                )
                app.delete(f"orders/{order.woo_id}", params={"force": True}).json()
            super(SalesOrderHwe, self).unlink()

    def sync_orders(self):
        return {
            'name': _('Sync Orders'),
            'view_mode': 'form',
            'res_model': 'woocommerce.update.wizard',
            'view_id': self.env.ref(
                'woocommerce_odoo_bridge.woocommerce_update_form_display').id,
            'type': 'ir.actions.act_window',
            'context': {'operation_type': 'orders',
                        'active_ids': self.ids},
            'target': 'current'
        }
