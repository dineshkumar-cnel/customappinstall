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
import xmlrpc.client
import odoo
from odoo.tests import common
import requests
import base64
from datetime import datetime
from odoo.http import request
from woocommerce import API
from odoo import models, fields, api, _
from odoo.exceptions import UserError

category_ids = False
attribute_ids = False
api_res = False
auth_vals = False


class WoocommerceUpdateHwe(models.TransientModel):
    _name = 'woocommerce.update.wizard'
    _description = 'Woocommerce Update'

    instance_id = fields.Many2one('woo.commerce', string="Instance",copy=False)

    @api.model
    def default_get(self, fields):
        """
                function to set default instance value.

        """
        defaults = super().default_get(fields)
        current_instance = self.env['woo.commerce'].search([('state','=','connected')])
        if len(current_instance) == 1:
            defaults['instance_id'] = current_instance.id
        return defaults

    def update_records(self):
        """
                function to update/export product,customer,order from odoo to woocommerce.

                """
        if not self.instance_id:
            raise UserError(
                _("Instance field is mandatory for updating records."))
        records = self._context.get('active_ids')
        if self._context.get('operation_type') == 'products':
            objs = self.env['product.template'].browse(records)
            wizard = self.get_wizard(self.instance_id)
            wizard.update_to_woo_commerce(objs, 'products')
        if self._context.get('operation_type') == 'customers':
            objs = self.env['res.partner'].browse(records).filtered(lambda x: x.type == 'contact')
            wizard = self.get_wizard(self.instance_id)
            wizard.update_to_woo_commerce(objs,'customers')
        if self._context.get('operation_type') == 'orders':
            objs = self.env['sale.order'].browse(records)
            wizard = self.get_wizard(self.instance_id)
            wizard.update_to_woo_commerce(objs, 'orders')

    def get_wizard(self,instance_id):
        """
        function used for returning new wizard
        for operations

        """

        set_wcapi = API(
            url=instance_id.store_url + "/index.php/wp-json/wc/v3/system_status?",
            consumer_key=instance_id.consumer_key,  # Your consumer key
            consumer_secret=instance_id.consumer_secret,  # Your consumer secret
            wp_api=True,  # Enable the WP REST API integration
            version="wc/v3",  # WooCommerce WP REST API version
            timeout=500

        )
        set_res = set_wcapi.get("").json()
        currency = set_res['settings'].get('currency')
        instance_id.currency = currency
        wizard = self.env['woo.wizard'].with_context(
            {'default_name': instance_id.name,
             'default_consumer_key': instance_id.consumer_key,
             'default_consumer_secret': instance_id.consumer_secret,
             'default_store_url': instance_id.store_url,
             'default_currency': instance_id.currency,
             'default_company': instance_id.company_specific,
             'active_id': instance_id.id
             }).create({})
        return wizard
