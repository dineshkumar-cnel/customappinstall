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

import requests
from woocommerce import API

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
import re

class WooCommerceInstanceHwe(models.Model):
    _name = 'woo.commerce'
    _description = "WooCommerce Connections"

    name = fields.Char(string="WooCommerce Store Connection Name", required=True)
    category_id = fields.Many2one('product.category', string="Category")
    color = fields.Integer('')
    consumer_key = fields.Char(string="Consumer Key", required=True)
    consumer_secret = fields.Char(string="Consumer Secret", required=True)
    store_url = fields.Char(string="Website URL", required=True)
    description = fields.Text(string="Description")
    connection_date = fields.Date(string='Connection Date', default=fields.Date.today)
    currency = fields.Char("Currency", readonly=True)
    company_specific = fields.Boolean("Company",
                                      help="If this field is empty then"
                                           " created records are available "
                                           "for all companies")
    state = fields.Selection(
        [('not_connected', 'Website Not Connected'),
         ('connected', '🎉 Congratulations! Your website has been successfully connected. 🎉')], default='not_connected')
    
    form_save_message = fields.Text(default="The submit button is located ▲ above to submit the form.", readonly=True)

    
    @api.model
    def create(self, vals):
        # Record create hone par, agar state connected ho toh notification dikhaye
        res = super(WooCommerceInstanceHwe, self).create(vals)
        if res.state == 'connected':
            # Show the message for successful connection
            self.show_connection_message()
        return res

    def write(self, vals):
        # Record update hone par agar state connected ho toh notification dikhaye
        res = super(WooCommerceInstanceHwe, self).write(vals)
        if 'state' in vals and vals['state'] == 'connected':
            # Show the message for successful connection
            self.show_connection_message()
        return res

    def show_connection_message(self):
        # Notification message for successful connection
        message = "🎉 Congratulations! Your website has been successfully connected. 🎉"
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Website Connection Success",  # Title of the notification
                'message': message,  # The main message
                'type': 'success',  # The type of notification (success, warning, info, etc.)
                'sticky': False,  # Whether the message should stay on screen or disappear after a few seconds
            }
        }

    pending_count_logs = fields.Integer(compute='_compute_logs_count')
    completed_count_logs = fields.Integer(compute='_compute_logs_count')
    failed_count_logs = fields.Integer(compute='_compute_logs_count')

    def action_name(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Completed Woo Logs'),
            'domain': [('instance_id', '=', self.id), ('state', '=', 'done')],
            'view_mode': 'list,form',
            'res_model': 'job.cron',
            'context': {'create': False, 'edit': False},
        }

    def get_pending_instance_woo_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pending Woo Logs'),
            'domain': [('instance_id', '=', self.id), ('state', '=', 'pending')],
            'view_mode': 'list,form',
            'res_model': 'job.cron',
            'context': {'create': False, 'edit': False},
        }

    def get_failed_instance_woo_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Failed Woo Logs'),
            'domain': [('instance_id', '=', self.id), ('state', '=', 'fail')],
            'view_mode': 'list,form',
            'res_model': 'job.cron',
            'context': {'create': False, 'edit': False},
        }

    def _compute_logs_count(self):
        for instance in self:
            instance.pending_count_logs = self.env['job.cron'].search_count(
                [('instance_id', '=', instance.id), ('state', '=', 'pending')]
            )
            instance.completed_count_logs = self.env['job.cron'].search_count(
                [('instance_id', '=', instance.id), ('state', '=', 'done')]
            )
            instance.failed_count_logs = self.env['job.cron'].search_count(
                [('instance_id', '=', instance.id), ('state', '=', 'fail')]
            )

    @api.model
    def get_instance_graph(self):
        instance_ob = self.env['woo.commerce'].search([])
        product_len = []
        customer_len = []
        order_len = []
        instance_name = []
        for rec in instance_ob:
            products = self.env['product.template'].search([
                ('instance_id', '=', rec.id)])
            customers = self.env['res.partner'].search([
                ('instance_id', '=', rec.id)])
            orders = self.env['sale.order'].search([
                ('instance_id', '=', rec.id)])
            product_len.append(len(products))
            customer_len.append(len(customers))
            order_len.append(len(orders))
            instance_name.append(rec.name)
        return {
            'instance_name': instance_name,
            'product_len': product_len,
            'customer_len': customer_len,
            'order_len': order_len
        }

    def get_api(self):
        """
        Returns API object.
        """
        wcapi = API(
            url=f"{self.store_url}/index.php/",
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            wp_api=True,
            version="wc/v3",
            timeout=500,
        )
        return wcapi

    def get_wizard(self):
        """
        Function used for returning wizard view for operations.
        """
        set_wcapi = API(
            url=f"{self.store_url}/index.php/wp-json/wc/v3/system_status?",
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            wp_api=True,
            version="wc/v3",
            timeout=500
        )
        set_res = set_wcapi.get("").json()
        currency = set_res['settings'].get('currency')
        self.currency = currency
        return {
            'name': _('Connection Sync'),
            'view_mode': 'form',
            'res_model': 'woo.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_name': self.name,
                'default_consumer_key': self.consumer_key,
                'default_consumer_secret': self.consumer_secret,
                'default_store_url': self.store_url,
                'default_currency': self.currency,
                'default_company': self.company_specific,
            }
        }

       
    def get_instance(self):
        """
        Function used for returning the current form view of the instance.
        """
        return {
            'name': _('Instance'),
            'view_mode': 'form',
            'res_model': 'woo.commerce',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
       
    @api.model_create_multi
    def create(self, vals_list):
        """
        Checks all the connection validations.
        """
        attachment_id = self.env['ir.attachment'].sudo().search(
            domain=[('res_model', '=', 'product.template'),
                    ('res_field', '=', 'image_1920')])
        if attachment_id:
            attachment_id.public = True
        for item in vals_list:
            site_url = item['store_url']
            set_wcapi = API(
                url=f"{site_url}/index.php/wp-json/wc/v3/system_status?",
                consumer_key=item['consumer_key'],
                consumer_secret=item['consumer_secret'],
                wp_api=True,
                version="wc/v3",
                timeout=500
            )

            regex = re.compile(
                r'^(?:http|ftp)s?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)

            url_status = re.match(regex, set_wcapi.url) is not None

            if not url_status:
                raise UserError(_("URL Doesn't Exist."))
            try:
                response = requests.get(set_wcapi.url)
            except requests.ConnectionError as exception:
                raise UserError(_("URL Doesn't Exist."))
            if set_wcapi.get("").status_code != 200:
                raise UserError(
                    _("URL Doesn't Exist or Authentication Issue."))
            set_res = set_wcapi.get("").json()
            if set_res['settings']:
                currency = set_res['settings'].get('currency')
                item['currency'] = currency

                if item['currency']:
                    item['state'] = 'connected'
        return super(WooCommerceInstanceHwe, self).create(vals_list)

    def write(self, vals):
        attachment_id = self.env['ir.attachment'].sudo().search(
            domain=[('res_model', '=', 'product.template'),
                    ('res_field', '=', 'image_1920')])
        if attachment_id:
            attachment_id.public = True
        keys = ['store_url', 'consumer_key', 'consumer_secret']
        for key in keys:
            if key in vals.keys():
                raise UserError(
                    _("You Can't Change Credential Details Once they are created."))
        return super(WooCommerceInstanceHwe, self).write(vals)

    def sync_cron(self):
        a = self.env['woo.wizard'].search([])
        for item in a:
            item.auto_import_orders()
            item.auto_import_products()
            item.auto_import_categories()
            item.auto_import_customers()

    @api.model
    def get_woo_commerce_instances(self):
        """
        This method is called through JavaScript code
        and returns a dictionary containing lists of WooCommerce instances.
        """
        instances = self.env['woo.commerce'].search([])
        res = []
        for instance in instances:
            res.append({
                'id': instance.id,
                'name': instance.name,
            })
        return res

