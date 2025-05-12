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
import base64
import logging
import random
import requests
import string
from datetime import datetime
from odoo.http import request
from woocommerce import API
_logger = logging.getLogger(__name__)
from odoo import models, fields, _, api
from odoo.exceptions import UserError

category_ids = False
attribute_ids = False
api_res = False


class WooComerceWizardHwe(models.TransientModel):
    _name = 'woo.wizard'
    _description = "Woo Operation Wizard"

    name = fields.Char(string="Connection Name", readonly=True)
    consumer_key = fields.Char(string="Consumer Key", readonly=True)
    consumer_secret = fields.Char(string="Consumer Secret", readonly=True)
    store_url = fields.Char(string="Store URL", readonly=True)
    product_check = fields.Boolean(string="Products")
    customer_check = fields.Boolean(string="Customers")
    order_check = fields.Boolean(string="Orders")
    category_check = fields.Boolean(string="Categories")
    variants_check = fields.Boolean(string="Product Variants")
    currency = fields.Char("Currency", readonly=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    sync_fun = fields.Boolean(help="Check sync state")
    company = fields.Boolean("Company", help="if this field empty then "
                                             " created records available "
                                             "for all company")

    order_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('all', 'All'),
    ], string='Status', default='all')

    def get_api(self):
        """
        It returns the API object for operations
        """
        app = API(
            url="" + self.store_url + "/index.php/",  # Your store URL
            consumer_key=self.consumer_key,  # Your consumer key
            consumer_secret=self.consumer_secret,  # Your consumer secret
            wp_api=True,  # Enable the WP REST API integration
            version="wc/v3",  # WooCommerce WP REST API version
            timeout=500,
        )
        return app

    
    # import functions
    def get_woo_import(self):
        """
        function for importing data from woocommerce
        database
        """
        if not (self.product_check or self.order_check or self.customer_check):
            raise UserError(
                _("Please enable at least one Method"))
        pending_task = self.env['job.cron'].search(
            [('state', '=', 'pending'),
             ('instance_id', '=', self._context.get('active_id'))])
        if pending_task:
            raise UserError(
                _("Please ensure that there are no pending tasks running currently"))

        if self.order_check:
            self.order_data_import()
        if self.customer_check:
            self.customer_data_import()
        if self.product_check:
            self.product_data_import()

    # 3 import functions:
    def product_data_import(self):
        """
        function for getting all products data through API
        """
        app = self.get_api()
        page = 1  # The first page number to loop is page 1
        while True:
            try:
                product_data = app.get('products', params={
                    'per_page': 50, 'page': page}).json()
                self.category_values()
                self.product_attribute_data_import()
                page += 1
                if not product_data:
                    break
                else:
                    job = self.env['job.cron'].create({
                        'function': "product_create",
                        'data': product_data,
                        'function_type': 'import',
                        'instance_id': self._context.get('active_id')
                    })
            except:
                break

        message = {
        'type': 'simple_notification',
        'title': "Product Import Processing",
        'message': "⏳ The WooCommerce Product Data import is currently in progress...",
        'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Product Logs Created ✅",
            'message': "WooCommerce product data import is complete. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

    def customer_data_import(self):
        """
        function for getting all customers data through API
        """
        app = self.get_api()

        page = 1  # The first page number to loop is page 1
        customers = []
        while True:
            customer_data = app.get('customers', params={
                'per_page': 100, 'page': page}).json()
            page += 1
            if not customer_data:
                break
            customers += customer_data
        if customers:
            customer_data = [customers[i:i + 500] for i in
                             range(0, len(customers), 500)]
            for chunk in customer_data:
                job = self.env['job.cron'].create({
                    'function': "customer_create",
                    'data': chunk,
                    'function_type': 'import',
                    'instance_id': self._context.get('active_id')
                })

        message = {
            'type': 'simple_notification',
            'title': "Customer Import Processing",
            'message': "⏳ The WooCommerce Customer data import is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Customer Logs Created ✅",
            'message': "WooCommerce Customer data import is complete. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

    def order_data_import(self):

        """
        function to import woo commerce orders,
        its also import all products, customers
        """
        app = self.get_api()

        page = 1  # The first page number to loop is page 1
        orders = []
        while True:
            order_data = app.get('orders', params={
                'per_page': 100, 'page': page}).json()
            page += 1
            if not order_data:
                break
            orders += order_data
        chunk_size = 50
        context = []
        chunk = []
        if self.order_status in ['draft', 'sent', 'sale', 'done', 'cancel']:
            if self.order_status in ['sale', 'done']:
                orders = [record for record in orders if
                          record["status"] in ['pending', 'processing',
                                               'on-hold', 'completed',
                                               'refunded']]
            elif self.order_status == 'cancel':
                orders = [record for record in orders if
                          record["status"] in ['cancelled']]
            elif self.order_status == 'sent':
                orders = [record for record in orders if
                          record["status"] in ['failed']]
            else:
                orders = [record for record in orders if
                          record["status"] not in ['failed', 'cancelled',
                                                   'pending', 'processing',
                                                   'on-hold', 'completed',
                                                   'refunded']]

        if self.start_date and self.end_date:
            for rec in orders:
                order_create_date = rec.get('date_created').split('T')[0]
                ord_date = datetime.strptime(order_create_date,
                                             '%Y-%m-%d').date()
                if self.start_date <= ord_date <= self.end_date:
                    chunk.append(rec)
                    if len(chunk) == chunk_size:
                        context.append(chunk)
                        chunk = []
        elif self.start_date:
            for rec in orders:
                order_create_date = rec.get('date_created').split('T')[0]
                ord_date = datetime.strptime(order_create_date,
                                             '%Y-%m-%d').date()
                if ord_date >= self.start_date:
                    chunk.append(rec)
                    if len(chunk) == chunk_size:
                        context.append(chunk)
                        chunk = []
        elif self.end_date:
            for rec in orders:
                order_create_date = rec.get('date_created').split('T')[0]
                ord_date = datetime.strptime(order_create_date,
                                             '%Y-%m-%d').date()
                if ord_date <= self.end_date:
                    chunk.append(rec)
                    if len(chunk) == chunk_size:
                        context.append(chunk)
                        chunk = []
        else:
            for i in range(0, len(orders), chunk_size):
                context.append(orders[i:i + chunk_size])
        if context:
            # creating new categories,attributes,products,customers
            self.category_values()
            self.product_attribute_data_import()
            self.tax_data_import()
            for rec in context:
                job = self.env['job.cron'].create({
                    'function': "create_order",
                    'data': rec,
                    'function_type': 'import',
                    'instance_id': self._context.get('active_id')
                })
        
        message = {
            'type': 'simple_notification',
            'title': "Order Import Processing",
            'message': "⏳ The WooCommerce Order data import is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Order Logs Created ✅",
            'message': "WooCommerce Order data import is complete. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

    # other functions associated with importing. order: product,customer,order
    def category_values(self):
        """
        function to set category values to product
        """
        page = 1  # The first page number to loop is page 1
        categories = []
        app = self.get_api()
        while True:
            category_data = app.get('products/categories',
                                    params={'per_page': 100,
                                            'page': page}).json()
            page += 1
            if not category_data:
                break
            categories += category_data
        if categories:
            for category_data in categories:
                woo_ids = self.env['product.category'].search([]).mapped(
                    'woo_id')
                if str(category_data.get('id')) not in woo_ids:
                    self.create_or_get_category(category_data, categories)

    def create_or_get_category(self, category_data, categories):
        """
        Function to fetch/create category.
        :returns: The object of category.
        :rtype: object
        """
        # Check if the category_data exists in Odoo
        category_ids = self.env['product.category'].search([])
        category = category_ids.filtered(
            lambda r: r.woo_id == str(category_data.get('id')))
        if not category:
            # The category does not exist, so create it
            active_id = self._context.get('active_id')
            category_name = category_data['name']
            parent_id = category_data['parent']
            woo_id = category_data['id']
            # If the category has a parent, create it recursively
            parent_category_id = None
            if category_name == 'Uncategorized':
                return None
            if parent_id:
                parent_category = next(
                    (c for c in categories if c["id"] == parent_id), None)
                if parent_category:
                    parent_category_id = self.create_or_get_category(
                        parent_category, categories)
            # Create the current category
            vals = {
                'name': category_name,
                'parent_id': parent_category_id.id if parent_category_id else False,
                'woo_id': woo_id,
                'instance_id': active_id if active_id else False
            }
            category = self.env['product.category'].create(vals)
        return category[0]

    def product_attribute_data_import(self):
        """
        function for getting all products attributes data through API
        """
        app = self.get_api()
        response = app.get("products/attributes", params={'per_page': 100})
        if response.status_code == 200:
            attributes = self.env['product.attribute'].search([])
            woo_ids = attributes.mapped('woo_id')
            for rec in response.json():
                if str(rec.get('id')) not in woo_ids:
                    # new attributes to be created!!
                    self.attribute_create(rec)
                else:
                    # need to check if there is a new value added for the given attribute and if yes: create
                    attribute = attributes.filtered(
                        lambda x: x.woo_id == str(rec.get('id')))
                    if attribute:
                        response = app.get(
                            "products/attributes/%s/terms" % int(
                                attribute.woo_id),
                            params={'per_page': 100})
                        if response.status_code == 200:
                            attribute_values = response.json()
                            if attribute_values:
                                filtered_data = [attr for attr in
                                                 attribute_values if attr[
                                                     'name'] not in attribute.value_ids.mapped(
                                        'name')]
                                if filtered_data:
                                    self.create_attribute_values(filtered_data,
                                                                 attribute)

    def attribute_create(self, attribute):
        """
        function to create attributes
        """
        app = self.get_api()
        vals = {'display_type': 'radio', 'create_variant': 'always',
                'name': attribute.get('name'), 'woo_id': attribute.get('id'),
                'instance_id': self._context.get(
                    'active_id') if self._context.get('active_id') else False}
        new_attribute_id = self.env['product.attribute'].create(vals)
        if new_attribute_id:
            response = app.get(
                "products/attributes/%s/terms" % attribute.get('id'),
                params={'per_page': 100})
            if response.status_code == 200:
                attribute_values = response.json()
                if attribute_values:
                    self.create_attribute_values(attribute_values,
                                                 new_attribute_id)

    def create_attribute_values(self, data, attribute_id):
        """
        Function to create attribute values.
        """
        attr_vals = []
        for rec in data:
            val = {'woo_id': rec.get('id'), 'name': rec.get('name'),
                   'attribute_id': attribute_id.id}
            attr_vals.append(val)
        if attr_vals:
            new_attribute_value_ids = self.env[
                'product.attribute.value'].create(attr_vals)

    def product_create(self, data):
        """
        Function to sync products with WooCommerce, and delete/archive products only for the current connection.
        """
        # Get the current connection's instance ID (WooCommerce store)
        active_instance_id = self._context.get('active_id')

        # Fetch all products linked to the current connection (instance_id)
        prod_ids = self.env['product.template'].search([('instance_id', '=', active_instance_id)])

        # Extract WooCommerce product IDs from the incoming data
        woo_product_ids = [str(rec['id']) for rec in data]

        # Archive/Delete products in Odoo that are not found in the current WooCommerce connection
        for prod in prod_ids:
            if str(prod.woo_id) not in woo_product_ids:
                # If the product is not found in the current WooCommerce connection, archive it
                prod.write({'active': False})  # Soft delete (archive the product)

        # Process the data for adding/updating products from WooCommerce
        for rec in data:
            prod_id = prod_ids.filtered(lambda r: r.woo_id == str(rec['id']))
            
            if prod_id:
                if rec.get('type') in ['simple', 'bundle']:
                    self.write_simple_product(rec, prod_id)
                if rec.get('type') == 'variable':
                    self.write_variant_product(rec, prod_id)
            else:
                if rec.get('type') in ['simple', 'bundle']:
                    self.simple_product_create(rec)
                if rec.get('type') == 'variable':
                    self.variant_product_tmpl_create(rec)

        message = {
            'type': 'simple_notification',
            'title': "Import Processing",
            'message': "⏳ The WooCommerce data Order import is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

    def simple_product_create(self, data):
        """
        Function to create a product without variants, considering the active WooCommerce instance.
        """
        val_list = self.prepare_product_vals(data)
        val_list['instance_id'] = self._context.get('active_id') if self._context.get('active_id') else False

        image = self.get_product_image(data)
        categories_value = data.get('categories')

        if categories_value:
            category_woo_id = categories_value[0].get('id')
            category_id = self.env['product.category'].search(
                [('woo_id', '=', category_woo_id)], limit=1)
            if category_id:
                val_list['categ_id'] = category_id.id

        if image.get('main_image'):
            val_list.update(image.get('main_image'))

        if image.get('product_template_image_ids'):
            val_list['product_template_image_ids'] = image.get('product_template_image_ids')

        if data.get('virtual'):
            val_list['detailed_type'] = 'service'

        # Creating the product with the connection-specific instance ID
        new_product_id = self.env['product.template'].create(val_list)

        if new_product_id and categories_value:
            category_woo_id = categories_value[0].get('id')
            category_id = self.env['product.category'].search(
                [('woo_id', '=', category_woo_id)], limit=1)
            if category_id:
                new_product_id.categ_id = category_id.id

        if not data.get('virtual'):
            if new_product_id and data.get('manage_stock') and data.get('stock_quantity') >= 1:
                if data.get('manage_stock') and data.get('stock_quantity') >= 1:
                    # add stock for the product(variant)
                    variant = new_product_id.product_variant_ids.id
                    if variant:
                        stock_vals = {
                            'location_id': self.env.ref('stock.stock_location_stock').id,
                            'inventory_quantity': data.get('stock_quantity'),
                            'quantity': data.get('stock_quantity'),
                            'product_id': variant,
                            'on_hand': True
                        }
                        self.env['stock.quant'].sudo().create(stock_vals)

        return new_product_id


    def variant_product_tmpl_create(self, data):
        """
        Function to create a product with variants.
        :returns: The id of created product template.
        :rtype: int
        """
        app = self.get_api()
        val_list = self.prepare_product_vals(data)
        val_list['instance_id'] = self._context.get(
            'active_id') if self._context.get('active_id') else False
        image = self.get_product_image(data)
        categories_value = data.get('categories')
        if categories_value:
            category_woo_id = categories_value[0].get('id')
            category_id = self.env['product.category'].search(
                [('woo_id', '=', category_woo_id)], limit=1)
            if category_id:
                val_list['categ_id'] = category_id.id
        if image.get('main_image'):
            val_list.update(image.get('main_image'))
        if image.get('product_template_image_ids'):
            val_list['product_template_image_ids'] = image.get(
                'product_template_image_ids')
        variants_response = []
        try:
            page = 1
            params = {"per_page": 100}
            while True:
                params['page'] = page
                response = app.get("products/%s/variations" % (data.get("id")),
                                   params=params).json()
                page += 1
                if response and isinstance(response, list):
                    variants_response += response
                else:
                    break
        except Exception as error:
            message = "Error While Importing Product Variants from WooCommerce. \n%s" % (
                error)
            return message
        if data.get('virtual'):
            val_list['detailed_type'] = 'service'
        variant_vals = {}
        variant_stock_vals = []
        # intialize to avoid error for products having no variant data.
        if variants_response:
            attribute_line_ids = self.get_attributes_line_vals(
                variants_response)
            if attribute_line_ids:
                val_list['attribute_line_ids'] = attribute_line_ids
            variant_vals = self.update_variants(variants_response)
            variant_stock_vals = self.update_variant_stock_vals(
                variants_response)
        val_list['woo_variant_check'] = True
        new_product_id = self.env['product.template'].sudo().create(val_list)
        if new_product_id:
            product = self.env['product.template'].browse(new_product_id.id)
            if product:
                for rec in variant_vals:
                    if rec['combination']:
                        attr_ids = [x for x in rec['combination'].keys()]
                        attr_value_ids = [x[0] for x in
                                          rec['combination'].values()]
                        domain = [('product_tmpl_id', '=', product.id),
                                  ('attribute_id', 'in', attr_ids), (
                                      'product_attribute_value_id', 'in',
                                      attr_value_ids)]
                        product_templ_attr_value = self.env[
                            'product.template.attribute.value'].search(domain)
                        product_variant = product.product_variant_ids.filtered(
                            lambda
                                x: x.product_template_variant_value_ids.ids == product_templ_attr_value.ids)
                        if product_variant:
                            del rec['combination']
                            product_variant[0].write(rec)
        if variant_stock_vals:
            self.create_stock_variants(variant_stock_vals, product)
        return new_product_id

    def prepare_product_vals(self, data):
        """
            Function to prepare product values to create a product.
            :returns: The merged key-value pairs.
            :rtype: dict
        """

        category_id = self.env['product.category'].search([], limit=1).id
        val_list = {
            'name': data.get('name'),
            'detailed_type': 'product',
            'description': data.get('description'),
            'list_price': self.calc_currency_rate(
                data.get('price'), 1),
            'sale_ok': True,
            'default_code': data.get('sku'),
            'purchase_ok': data.get('purchasable') or False,
            'weight': data.get('weight') or 0,
            'woo_id': data.get('id'),
            'company_id': self.env.company.id if self.company else False,
        }
        dimensions_single = self.get_dimenstion(data.get('dimensions'))
        upsell_ids = self.get_linked_product_ids(data.get('upsell_ids'))
        cross_sell_ids = self.get_linked_product_ids(
            data.get('cross_sell_ids'))
        tags = self.tags_create(data.get('tags'))
        val_list['volume'] = dimensions_single
        val_list['categ_id'] = category_id
        val_list['optional_product_ids'] = cross_sell_ids
        val_list['alternative_product_ids'] = upsell_ids
        val_list['product_tag_ids'] = tags
        return val_list

    def calc_currency_rate(self, price, action):
        """
        function to convert currency
        """
        api_res = requests.get(
            'https://api.exchangerate-api.com/v4/latest/' + self.currency + '').json()
        currency = self.env.company.currency_id.name
        currency_rate = api_res['rates']
        if action == 1:
            value = round(float(price) * currency_rate[currency],
                          4) if price else 0
        else:
            value = round(float(price) / currency_rate[currency],
                          4) if price else 0
        return value

    def get_dimenstion(self, data):
        """
        Function to return dimension for a product.
        :returns: The calculated dimension based on length * width * height.
        :rtype: Int
        """
        try:
            dimensions_single = int(data['length']) * int(data['width']) * int(
                data['height'])
        except ValueError:
            dimensions_single = 0
        return dimensions_single

    def get_linked_product_ids(self, upsell_ids, var=False):
        """
        function to set upsell, cross-sell products
        """
        # in woocommerce the upsell / cross-sell products are given as specific variants
        # here , its product template is selected and added
        product_ids = self.env['product.template'].search([])
        product_var_ids = self.env['product.product'].search([])
        val_list = []
        if upsell_ids:
            for item in upsell_ids:
                if not var:
                    product_id = product_ids.filtered(
                        lambda r: r.woo_id == str(item))
                    if product_id:
                        if not product_id[0].id in val_list:
                            val_list.append(product_id[0].id)
                    else:
                        product_id = product_var_ids.filtered(
                            lambda r: r.woo_var_id == str(item))
                        if product_id:
                            if not product_id[
                                       0].product_tmpl_id.id in val_list:
                                val_list.append(
                                    product_id[0].product_tmpl_id.id)
        return val_list

    def tags_create(self, data):
        """
        Function to create product tags.
        :returns: The list of tag ids.
        :rtype: list
        """
        product_tag = []
        if data:
            for item in data:
                tag_name = item['name']
                woo_id = item['id']
                domain = [['name', '=', tag_name]]
                tag_ids = self.env['product.tag'].search(domain)
                if tag_ids:
                    for tag_id in tag_ids:
                        if tag_id.id not in product_tag:
                            product_tag.append(tag_id.id)
                else:
                    new_tag_id = self.env['product.tag'].create(
                        {'name': tag_name, 'woo_id': woo_id})
                    product_tag.append(new_tag_id.id)
        return product_tag

    def get_product_image(self, data):
        """
        Function to get the main product image and also the other images in product.
        :returns: The dict of main image and other images if existed.
        :rtype: Dict
        """
        data_list = {}
        product_template_image_ids = []
        for index, value in enumerate(data.get('images')):
            if index == 0:
                data_list['main_image'] = {
                    'image_1920': base64.b64encode(
                        requests.get(data['images'][0]['src']).content)}
            else:
                product_template_image_ids.append((0, 0,
                                                   {'name': data.get('name'),
                                                    'image_1920': base64.b64encode(
                                                        requests.get(value[
                                                                         'src']).content)}))
        data_list['product_template_image_ids'] = product_template_image_ids
        return data_list

    def get_attributes_line_vals(self, data):
        """
        Function to fetch and return attributes and its values.
        :returns: The merged key-value pairs.
        :rtype: dict
        """
        attr_ids = self.env['product.attribute'].search([])
        vals = {}
        dynamic_vals = {}
        for item in data:
            for attribute in item['attributes']:
                if attribute.get('id'):
                    attr_id = attr_ids.filtered(
                        lambda x: x.woo_id == str(attribute.get('id')))
                    if attr_id:
                        attr_val = attr_id.value_ids.filtered(
                            lambda x: x.name.lower() == attribute.get(
                                'option').lower())
                        if attr_val:
                            vals.setdefault(attr_id.id, []).append(
                                attr_val.ids[0])
                else:
                    if attribute.get('name'):
                        new_attribute = self.env['product.attribute'].search(
                            [('name', '=', attribute.get('name'))])
                        if not new_attribute:
                            new_attribute = self.env[
                                'product.attribute'].create(
                                {'name': attribute.get('name')})
                        if attribute.get('option'):
                            if not len(new_attribute) > 1:
                                new_value = new_attribute.value_ids.filtered(
                                    lambda x: x.name.lower() == attribute.get(
                                        'option').lower())
                                if not new_value:
                                    new_value = self.env[
                                        'product.attribute.value'].create({
                                        'name': attribute.get('option'),
                                        'attribute_id': new_attribute.id,
                                    })
                                if new_value.id not in dynamic_vals.setdefault(
                                        new_attribute.id, []):
                                    dynamic_vals[new_attribute.id].append(
                                        new_value.id)
                            else:
                                new_attribute = new_attribute.filtered(
                                    lambda x: attribute.get(
                                        'option').lower() in x.value_ids.mapped(
                                        'name'))
                                if len(new_attribute) > 1:
                                    new_attribute = new_attribute[0]
                                new_value = new_attribute.value_ids.filtered(
                                    lambda x: x.name.lower() == attribute.get(
                                        'option').lower())
                                if not new_value:
                                    new_value = self.env[
                                        'product.attribute.value'].create({
                                        'name': attribute.get('option'),
                                        'attribute_id': new_attribute.id,
                                    })
                                if new_value[
                                    0].id not in dynamic_vals.setdefault(
                                    new_attribute.id, []):
                                    dynamic_vals[new_attribute.id].append(
                                        new_value[0].id)
        attribute_line_values = [
            (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, value_ids)]})
            for attr_id, value_ids in vals.items()
        ]
        if dynamic_vals:
            new_lines = [(0, 0, {'attribute_id': attr_id,
                                 'value_ids': [(6, 0, value_ids)]}) for
                         attr_id, value_ids in dynamic_vals.items()]
            attribute_line_values += new_lines
        return attribute_line_values

    def update_variants(self, val):
        """
        Function to return variant values.
        :returns: The merged key-value pairs.
        :rtype: dict
        """
        variants_list = []
        attr_obj = self.env['product.attribute']
        for data in val:
            vals = {}
            for attribute in data['attributes']:
                if attribute.get('id'):
                    attr_id = attr_obj.search([]).filtered(
                        lambda x: x.woo_id == str(attribute.get('id')))
                    if attr_id:
                        attr_val = attr_id.value_ids.filtered(
                            lambda x: x.name.lower() == attribute.get(
                                'option').lower())
                        if attr_val:
                            vals.setdefault(attr_id.id, []).append(
                                attr_val.ids[0])
                elif attribute.get('name'):
                    attr_id = attr_obj.search(
                        [('name', '=', attribute.get('name'))])
                    if attr_id and len(attr_id) == 1:
                        attr_val = attr_id.value_ids.filtered(
                            lambda x: x.name.lower() == attribute.get(
                                'option').lower())
                        if attr_val:
                            vals.setdefault(attr_id.id, []).append(
                                attr_val.ids[0])
                    if attr_id and len(attr_id) > 1:
                        new_attribute = attr_id.filtered(
                            lambda x: attribute.get(
                                'option').lower() in x.value_ids.mapped(
                                'name'))
                        if len(new_attribute) > 1:
                            new_attribute = new_attribute[0]
                        new_value = new_attribute.value_ids.filtered(
                            lambda x: x.name.lower() == attribute.get(
                                'option').lower())
                        if new_value:
                            vals.setdefault(new_attribute.id, []).append(
                                new_value.ids[0])
            new_dict = {'image_variant_1920': base64.b64encode(
                requests.get(data['image']['src']).content) if data[
                'image'] else False, 'woo_var_id': data['id'],
                        'description': data['description'],
                        'default_code': data['sku'],
                        'weight': data['weight'],
                        'combination': vals if vals else False,
                        'volume': self.get_dimenstion(data['dimensions'])}
            variants_list.append(new_dict)
        return variants_list

    def update_variant_stock_vals(self, val):
        """
        Function to return variant stock values.
        :returns: The merged key-value pairs.
        :rtype: dict
        """
        stock_vals = {}
        for rec in val:
            if rec.get('manage_stock') != 'parent' and rec.get('manage_stock'):
                if rec.get('stock_quantity') > 0:
                    stock_vals[rec.get('id')] = rec.get('stock_quantity')
        return stock_vals

    def create_stock_variants(self, val, product):
        """
        Function to create stock for variants.
        """
        for rec in val:
            variant_id = product.product_variant_ids.filtered(
                lambda x: x.woo_var_id == str(rec))
            if variant_id:
                stock_vals = {
                    'location_id': self.env.ref(
                        'stock.stock_location_stock').id,
                    'inventory_quantity': val.get(rec),
                    'quantity': val.get(rec),
                    'product_id': variant_id[0].id,
                    'on_hand': True
                }
                self.env['stock.quant'].sudo().create(stock_vals)

    def customer_create(self, data):
        """
        function for syncing customer data, it creates/writes customers from
        WooCommerce to Odoo.
        """
        
        existing_woo_ids = [str(rec['id']) for rec in data]
        instance_id = self._context.get('active_id')  # current connection's instance_id
        
        # Fetch all customers in Odoo with woo_id
        all_customers = self.env['res.partner'].search([
            ('woo_id', '!=', False), 
            ('type', '=', 'contact'),
            ('instance_id', '=', instance_id)  # Match the current connection's instance_id
        ])
    
    # Check customers in Odoo that don't exist in WooCommerce (to delete them)
        for customer in all_customers:
            if customer.woo_id not in existing_woo_ids:
                # Customer not found in WooCommerce, so delete from Odoo
                customer.unlink()

        partner_ids = self.env['res.partner'].search(
            [('woo_id', '!=', False), ('type', '=', 'contact')])
        for rec in data:
            partner_id = partner_ids.filtered(
                lambda r: r.woo_id == str(rec['id']))
            if partner_id:
                existing_values = partner_id.read(
                    ['name', 'email', 'phone', 'street', 'street2', 'city',
                     'zip', 'state_id', 'country_id', 'woo_id',
                     'woo_user_name', 'company_id', 'company_type'])
                if existing_values[0].get('state_id'):
                    existing_values[0]['state_id'] = \
                        existing_values[0]['state_id'][0]
                if existing_values[0].get('country_id'):
                    existing_values[0]['country_id'] = \
                        existing_values[0]['country_id'][0]
                if existing_values[0].get('company_id'):
                    existing_values[0]['company_id'] = \
                        existing_values[0]['company_id'][0]
                existing_values[0].pop("id", None)
                woocommerce_values = {
                    'company_type': "person",
                    'name': rec.get('first_name') + " " + rec.get(
                        'last_name'),
                    'email': rec.get('email'),
                    'phone': rec['billing']['phone'],
                    'street': rec['billing']['address_1'],
                    'street2': rec['billing']['address_2'],
                    'city': rec['billing']['city'],
                    'zip': rec['billing']['postcode'],
                    'state_id': self.env['res.country.state'].search(
                        [('code', '=', rec['billing']['state']),
                         ('country_id', '=',
                          rec['billing']['country'])]).id,
                    'country_id': self.env['res.country'].search(
                        [('code', '=', rec['billing']['country'])]).id,
                    'woo_id': str(rec.get('id')),
                    'woo_user_name': rec.get('username'),
                    'company_id': self.env.company.id if self.company else False
                }
                if not existing_values[0] == woocommerce_values:
                    partner_id.write(woocommerce_values)
                if rec.get('shipping'):
                    shipping_address = {}
                    first_name = rec['shipping'].get("first_name") or ''
                    last_name = rec['shipping'].get("last_name") or ''
                    name = first_name + " " + last_name if first_name or last_name else ''
                    if name:
                        shipping_address['name'] = name
                        shipping_address['zip'] = rec['shipping'].get(
                            "postcode") or ''
                        shipping_address['street'] = rec['shipping'].get(
                            "address_1") or ''
                        shipping_address['street2'] = rec['shipping'].get(
                            "address_2") or ''
                        shipping_address['city'] = rec.get('shipping').get(
                            "city") or ''
                        shipping_address['phone'] = rec['shipping'].get(
                            "phone") or ''
                        state = rec.get('shipping').get("state") or ''
                        country = rec.get('shipping').get("country") or ''
                        country_id = self.env['res.country'].sudo().search(
                            [('code', '=', country)], limit=1)
                        state_id = self.env['res.country.state'].sudo().search(
                            ['&', ('code', '=', state),
                             ('country_id', '=', country_id.id)], limit=1)
                        shipping_address[
                            'country_id'] = False if not country_id else country_id.id
                        shipping_address[
                            'state_id'] = False if not state_id else state_id.id
                        shipping_address['woo_id'] = str(rec.get('id'))
                        shipping_address['woo_user_name'] = rec.get('username')
                        if not partner_id.child_ids.filtered(
                                lambda x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id'])):
                            # no delivery address added so create
                            shipping_address['parent_id'] = partner_id.id
                            shipping_address['type'] = 'delivery'
                            shipping_address[
                                'instance_id'] = self._context.get(
                                'active_id') if self._context.get(
                                'active_id') else False
                            new_delivery_contact = self.env[
                                'res.partner'].create(shipping_address)
                        else:
                            # check and compare the details of the delivery address
                            child_id = partner_id.child_ids.filtered(
                                lambda
                                    x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id']))
                            if not len(child_id) > 1:
                                current_delivery_address = child_id.read(
                                    ['name', 'zip', 'street', 'street2',
                                     'city',
                                     'phone', 'country_id', 'state_id',
                                     'woo_id', 'woo_user_name'])
                                if current_delivery_address[0].get('state_id'):
                                    current_delivery_address[0]['state_id'] = \
                                        current_delivery_address[0][
                                            'state_id'][
                                            0]
                                if current_delivery_address[0].get(
                                        'country_id'):
                                    current_delivery_address[0]['country_id'] = \
                                        current_delivery_address[0][
                                            'country_id'][0]
                                current_delivery_address[0].pop("id", None)
                                if not current_delivery_address[
                                           0] == shipping_address:
                                    shipping_address[
                                        'instance_id'] = self._context.get(
                                        'active_id')
                                    update_delivery_address = child_id.write(
                                        shipping_address)
                    else:
                        # might need to delete the record after unlinking from parent
                        if partner_id.child_ids.filtered(
                                lambda x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id'])):
                            child_to_remove = partner_id.child_ids.filtered(
                                lambda
                                    x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id']))
                            child_to_remove.unlink()
            else:
                existing_id = self.env['res.partner'].search(
                    [('type', '=', 'contact'),
                     ('email', '=', rec.get('email'))])
                if existing_id:
                    if not len(existing_id) > 1:
                        vals = {
                            'woo_id': rec.get('id'),
                            'woo_user_name': rec.get('username'),
                            'instance_id': self._context.get(
                                'active_id') if self._context.get(
                                'active_id') else False,
                            'company_id': self.env.company.id if self.company else False,
                        }
                        if vals:
                            partner = self.env['res.partner'].write(vals)
                else:
                    partner_id = self.create_new_customer(rec)

    def has_at_least_one_value(self, dictionary):
        """Method to if the dictionary is empty or not.
            :param dictionary: Dictionary to check.
            :return: Returns False if dictionary is empty. Else return True."""
        for value in dictionary.values():
            if value:  # This checks if the value is non-empty.
                return True
            else:
                return False

    def create_new_customer(self, rec):
        """
        Function to create new customer.
        :returns: The customer id.
        :rtype: Int
        """
        mail_list = self.env['res.partner'].search(
            [('type', '=', 'contact')]).mapped('email')
        if rec.get('email') in mail_list:
            return False
        val = self.prepare_customer_vals(rec)
        if val:
            val['instance_id'] = self._context.get(
                'active_id') if self._context.get('active_id') else False
            partner_id = self.env['res.partner'].create(val)
            if partner_id:
                # need to check a separate delivery address is needed to add and here we are making the name field mandatory
                first_name = rec['shipping'].get("first_name") or ''
                last_name = rec['shipping'].get("last_name") or ''
                if first_name or last_name:
                    name = first_name + " " + last_name
                else:
                    name = ""
                if name:
                    state = rec.get('shipping').get("state") or ''
                    country = rec.get('shipping').get("country") or ''
                    country_id = self.env['res.country'].sudo().search(
                        [('code', '=', country)], limit=1)
                    state_id = self.env['res.country.state'].sudo().search(
                        ['&', ('code', '=', state),
                         ('country_id', '=', country_id.id)], limit=1)
                    shipping_address = {
                        'name': name,
                        'zip': rec['shipping'].get("postcode") or '',
                        'street': rec['shipping'].get("address_1") or '',
                        'street2': rec['shipping'].get("address_2") or '',
                        'city': rec.get('shipping').get("city") or '',
                        'phone': rec['shipping'].get("phone") or '',
                        'country_id': country_id.id if country_id else False,
                        'state_id': state_id.id if state_id else False,
                        'parent_id': partner_id.id,
                        'type': 'delivery',
                        'woo_id': rec.get('id'),
                        'woo_user_name': rec.get('username'),
                        'instance_id': self._context.get(
                            'active_id') if self._context.get(
                            'active_id') else False,
                        'company_id': self.env.company.id if self.company else False
                    }
                    delivery_contact = self.env['res.partner'].create(
                        shipping_address)
                if partner_id and self.has_at_least_one_value(
                        rec['billing']):
                    if rec['billing'].get("first_name") and not rec[
                        'billing'].get("last_name"):
                        name = rec['billing'].get("first_name")
                    elif rec['billing'].get("last_name") and not rec[
                        'billing'].get("first_name"):
                        name = rec.get("first_name")
                    elif rec['billing'].get("first_name") and rec[
                        'billing'].get("last_name"):
                        dict = rec['billing']
                        name_with = f'{dict.get("first_name")} {dict.get("last_name")}',
                        name = str(name_with).strip("'(',)")
                    elif not (rec['billing'].get("first_name") and rec[
                        'billing'].get("last_name")):
                        name = ''
                    billing_address = {
                        'name': name if name else False,
                        'company_id': self.env.company.id if self.env.company else False,
                        'phone': rec['billing']['phone'] if rec['billing'][
                            'phone'] else False,
                        'street': rec['billing']['address_1'] if
                        rec['billing'][
                            'address_1'] else False,
                        'street2': rec['billing']['address_2'] if
                        rec['billing'][
                            'address_2'] else False,
                        'city': rec['billing']['city'] if rec['billing'][
                            'city'] else False,
                        'zip': rec['billing']['postcode'] if
                        rec['billing'][
                            'postcode'] else False,
                        'state_id': self.env['res.country.state'].search(
                            [('code', '=', rec['billing']['state']),
                             ('country_id', '=',
                              rec['billing']['country'])]).id if
                        rec['billing']['country'] else False,
                        'country_id': self.env['res.country'].search(
                            [('code', '=',
                              rec['billing']['country'])]).id if
                        rec['billing']['country'] else False,
                        'type': 'invoice',
                        'parent_id': partner_id.id,
                    }
                    self.env['res.partner'].sudo().create(billing_address)
                return partner_id

    def prepare_customer_vals(self, rec):
        """
        Function to return basic customer values that for creation.
        :returns: The merged key-value pairs.
        :rtype: dict
        """
        vals = {}
        first_name = rec.get("first_name") or ''
        b_first_name = rec['billing'].get("first_name") or ''
        last_name = rec.get("last_name") or ''
        b_last_name = rec['billing'].get("last_name") or ''
        username = rec.get("username") or ''
        if first_name or last_name:
            name = first_name + " " + last_name
        elif b_first_name or b_last_name:
            name = b_first_name + " " + b_last_name
        elif username:
            name = username
        else:
            name = ""
        if name:
            vals = {
                'company_type': "person",
                'name': name,
                'email': rec.get('email') if rec.get('email') else False,
                'phone': rec['billing']['phone'] if rec['billing'][
                    'phone'] else False,
                'street': rec['billing']['address_1'] if rec['billing'][
                    'address_1'] else False,
                'street2': rec['billing']['address_2'] if rec['billing'][
                    'address_2'] else False,
                'city': rec['billing']['city'] if rec['billing'][
                    'city'] else False,
                'zip': rec['billing']['postcode'] if rec['billing'][
                    'postcode'] else False,
                'state_id': self.env['res.country.state'].search(
                    [('code', '=', rec['billing']['state']),
                     ('country_id', '=',
                      rec['billing']['country'])]).id if rec['billing'][
                    'country'] else False,
                'country_id': self.env['res.country'].search(
                    [('code', '=', rec['billing']['country'])]).id if
                rec['billing']['country'] else False,
                'woo_id': rec.get('id'),
                'woo_user_name': rec.get('username') if rec.get(
                    'username') else False,
                'company_id': self.env.company.id if self.company else False,
            }
        return vals

    def tax_data_import(self):
        """
        function to import woo commerce taxes into odoo
        """
        app = self.get_api()
        res = app.get("taxes", params={"per_page": 100}).json()
        tax_obj_ids = self.env['account.tax'].search([])
        woo_ids = tax_obj_ids.mapped('woo_id')
        tax_ids = []
        existing_tax_ids = []
        instance_id = self._context.get('active_id')
        for recd in res:
            if str(recd.get('id')) not in woo_ids:
                vals_tax = {
                    'name': recd.get('name'),
                    'amount': recd.get('rate'),
                    'woo_id': recd.get('id'),
                    'instance_id': instance_id if instance_id else False,
                    'tax_class': recd.get('class'),
                    'description': recd.get('rate').split('.')[0] + ".00%",
                }
                tax_ids.append(vals_tax)
            else:
                tax_id = tax_obj_ids.filtered(
                    lambda x: x.woo_id == str(recd.get('id')))
                if tax_id:
                    vals_tax = {
                        'id': tax_id.id,
                        'name': recd.get('name'),
                        'amount': recd.get('rate'),
                        'woo_id': recd.get('id'),
                        'instance_id': instance_id if instance_id else False,
                        'tax_class': recd.get('class'),
                        'description': recd.get('rate').split('.')[0] + ".00%",
                    }
                    existing_tax_ids.append(vals_tax)
        if tax_ids:
            self.env['account.tax'].create(tax_ids)
        if existing_tax_ids:
            query = """ UPDATE account_tax SET woo_id = %(woo_id)s,instance_id = %(instance_id)s, name = %(name)s, tax_class = %(tax_class)s, description = %(description)s,amount= %(amount)s WHERE id = %(id)s"""

            self.env.cr.executemany(query, existing_tax_ids)

    def create_order(self, orders):
        """
        function to create woo commerce order in odoo
        """
        app = self.get_api()
        partner_obj = self.env['res.partner']
        prod_obj = self.env['product.template']
        prod_var_obj = self.env['product.product']
        tax_ids = self.env['account.tax'].search([])
        order_ids = self.env['sale.order'].search([
            ('woo_id', '!=', False)
        ])
        woo_ids = order_ids.mapped('woo_id')

        # Step 1: Identify orders to delete (those not in WooCommerce anymore)
        existing_order_woo_ids = [str(order['id']) for order in orders]
        
        # Find orders in Odoo that are no longer in WooCommerce
        orders_to_delete = order_ids.filtered(lambda o: str(o.woo_id) not in existing_order_woo_ids)

        # Delete those orders in Odoo
        for order in orders_to_delete:
            order.sudo().with_context({'disable_cancel_warning': True}).action_cancel()
            order.unlink()

        for item in orders:
            if str(item.get('id')) not in woo_ids:
                partner_ids = partner_obj.search([('type', '=', 'contact')])
                partner_id = self.get_partner_from_order(item, partner_ids)
                if partner_id:
                    order_create_date = item.get('date_created').split('T')[0]
                    date_time_obj = datetime.strptime(order_create_date,
                                                      '%Y-%m-%d').date()
                    state = 'draft'
                    if item.get('status') == 'failed':
                        state = 'sent'
                    val_list = {
                        'partner_id': partner_id,
                        'date_order': date_time_obj,
                        'woo_id': item.get('id'),
                        'instance_id': self._context.get(
                            'active_id') if self._context.get(
                            'active_id') else False,
                        'woo_order_key': item.get('order_key'),
                        'state': state,
                    }
                    orderline = []
                    for line_item in item.get('line_items'):
                        woo_tax = []
                        for tax in line_item['taxes']:
                            woo_tax.append(str(tax['id']))
                        tax_id = tax_ids.filtered(
                            lambda r: r.woo_id in woo_tax)
                        main_product = prod_obj.search([]).filtered(
                            lambda r: r.woo_id == str(line_item['product_id']))
                        if main_product:
                            main_product = main_product[0]
                            product = False
                            if len(main_product.product_variant_ids) > 1:
                                product = prod_var_obj.search([]).filtered(
                                    lambda r: r.woo_var_id == str(
                                        line_item['variation_id']))
                                if product:
                                    product = product[0]
                            else:
                                product = main_product.product_variant_ids[0]
                            if product:
                                val = {
                                    'name': product.name,
                                    'product_id': product.id,
                                    'price_unit': float(line_item['price']),
                                    'product_uom_qty': line_item[
                                        'quantity'],
                                    'tax_id': tax_id.ids,
                                    'customer_lead': 1,
                                }
                                orderline.append((0, 0, val))
                        else:
                            # here we might need to create a new product instead of calling import product function
                            products_data = app.get(
                                'products/%s' % line_item['product_id'],
                                params={
                                    'per_page': 100, 'page': 1}).json()
                            product = False
                            if products_data.get('type') in ['simple',
                                                             'variable',
                                                             'bundle',
                                                             'grouped',
                                                             'external']:
                                # currently including these woocommerce product types only
                                if products_data.get('type') in ['simple',
                                                                 'bundle']:
                                    # no need to create variants for these products so we can use a separate function
                                    simple_product = self.simple_product_create(
                                        products_data)
                                    if simple_product:
                                        if product:
                                            product = \
                                                simple_product.product_variant_ids[
                                                    0]

                                if products_data.get('type') == 'variable':
                                    # need to create variants for these products
                                    variant_product = self.variant_product_tmpl_create(
                                        products_data)
                                    if variant_product:
                                        product = variant_product.product_variant_ids.filtered(
                                            lambda r: r.woo_var_id == str(
                                                line_item['variation_id']))
                                if product:
                                    val = {
                                        'name': product.name,
                                        'product_id': product.id,
                                        'product_uom_qty': line_item[
                                            'quantity'],
                                        'price_unit': float(
                                            line_item['price']),
                                        'tax_id': tax_id.ids,
                                        'customer_lead': 1
                                    }
                                    orderline.append((0, 0, val))

                    for line_item in item.get('shipping_lines'):
                        if not line_item.get('method_id') or line_item.get(
                                'method_id') == 'other':
                            product = self.env.ref(
                                'woocommerce_odoo_bridge.product_product_woocommerce_other_hwe')
                        if line_item.get('method_id') == 'flat_rate':
                            product = self.env.ref(
                                'woocommerce_odoo_bridge.product_product_flat_delivery')
                        if line_item.get('method_id') == 'local_rate':
                            product = self.env.ref(
                                'woocommerce_odoo_bridge.product_product_local_delivery')
                        if line_item.get('method_id') == 'free_shipping':
                            product = self.env.ref(
                                'woocommerce_odoo_bridge.product_product_woocommerce_free_delivery')
                        val = {
                            'name': product.name,
                            'product_id': product.product_variant_ids[0].id,
                            'tax_id': False,
                            'price_unit': float(line_item['total']),
                            'product_uom_qty': 1,
                            'customer_lead': 1,
                        }
                        orderline.append((0, 0, val))
                    for line_item in item.get('fee_lines'):
                        product = self.env.ref(
                            'woocommerce_odoo_bridge.woocommerce_fee_lines')
                        val = {
                            'name': product.name,
                            'product_id': product.product_variant_ids[0].id,
                            'tax_id': False,
                            'price_unit': float(line_item['total']),
                            'product_uom_qty': 1,
                            'customer_lead': 1,
                        }
                        orderline.append((0, 0, val))
                    # for line_item in item.get('coupon_lines'):
                    #     if line_item.get('discount', None):
                    #         product = self.env.ref(
                    #             'woocommerce_odoo_bridge.woocommerce_coupons')
                    #         val = {
                    #             'name': product.name,
                    #             'product_id': product.product_variant_ids[0].id,
                    #             'tax_id': False,
                    #             'price_unit': -1 * float(line_item['discount']),
                    #             'product_uom_qty': 1,
                    #             'customer_lead': 1,
                    #         }
                    #         orderline.append((0, 0, val))
                    if orderline:
                        val_list['order_line'] = orderline

                    so = self.env['sale.order'].sudo().create(val_list)
                    if item.get('status') in ['pending', 'processing',
                                              'on-hold', 'completed',
                                              'refunded']:
                        so.action_confirm()
                    if item.get('status') in ['cancelled']:
                        so.with_context(
                            {'disable_cancel_warning': True}).action_cancel()

    def get_partner_from_order(self, data, partners):
        """
        Function to fetch/create partner from order.
        :returns: The id of partner.
        :rtype: int
        """
        app = self.get_api()
        if data.get('customer_id'):
            partner = partners.filtered(
                lambda x: x.woo_id == str(data.get('customer_id')))
            if partner:
                return partner.id
            else:
                customer_data = app.get(
                    'customers/%s' % data.get('customer_id'), params={
                        'per_page': 100, 'page': 1}).json()
                if customer_data:
                    # creating a new partner
                    partner_id = self.create_new_customer(customer_data)
                    if partner_id:
                        return partner_id.id
        else:
            partner = self.env.ref('woocommerce_odoo_bridge.woocommerce_guest').id
            return partner

    # import functions

    # export functions
    
    def get_woo_export(self):
        """
        function to export data to woocommerce from odoo
        """
        if not (self.product_check or self.order_check or self.customer_check):
            raise UserError(
                _("Please enable at least one Method"))
        pending_task = self.env['job.cron'].search(
            [('state', '=', 'pending'),
             ('instance_id', '=', self._context.get('active_id'))])
        if pending_task:
            raise UserError(
                _("Please ensure that there are no pending tasks running currently"))

        if self.order_check:
            self.product_data_export()
            self.customer_data_export()
            self.order_data_export()
        else:
            if self.product_check:
                self.product_data_export()
            if self.customer_check:
                self.customer_data_export()

    def product_data_export(self):
        """
        function to export products to woo commerce
        """
        model = self.env['product.template']
        domain = []
        product_ids = self.list_records_in_chunks(model, domain, 100)
        if product_ids:
            self.create_categories_woo()
            self.create_attributes_woo()
            self.create_product_tag_woo()

            for chunk in product_ids:
                    job = self.env['job.cron'].create({
                        'function': "product_data_post",
                        'data': chunk,
                        'function_type': 'export',
                        'instance_id': self._context.get('active_id')
                    })
            message = {
            'type': 'simple_notification',
            'title': "Product Export Processing",
            'message': "⏳ The WooCommerce data Export Product is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Product Export Logs Created ✅",
            'message': "WooCommerce product data Export is completed. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)
                    
    def customer_data_export(self):
        """
        function to export products to woo commerce
        """

        model = self.env['res.partner']
        domain = [('type', '=', 'contact')]
        customer_ids = self.list_records_in_chunks(model, domain, 250)
        if customer_ids:
            for chunk in customer_ids:
                job = self.env['job.cron'].create({
                    'function': "customer_data_post",
                    'data': chunk,
                    'function_type': 'export',
                    'instance_id': self._context.get('active_id')
                })
        message = {
            'type': 'simple_notification',
            'title': "Customer Export Processing",
            'message': "⏳ The WooCommerce data Export Customer is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Customer Export LOgs Created ✅",
            'message': "WooCommerce Customer data Export is completed. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

    def order_data_export(self):
        """
        function for exporting order datas, it posts products, customers, orders
        from odoo to woocommerce.
        """

        message = {
            'type': 'simple_notification',
            'title': "Order Export Processing",
            'message': "⏳ The WooCommerce data Export Order is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Order Export Logs Created ✅",
            'message': "WooCommerce Order data Export is completed. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        model = self.env['sale.order']
        domain = [('woo_id', '=', False)]
        if self.start_date and self.end_date:
            domain += ('date_order', '>=', self.start_date), \
                ('date_order', '<=', self.end_date)
        elif self.start_date:
            domain += [('date_order', '>=', self.start_date)]
        elif self.end_date:
            domain += [('date_order', '<=', self.end_date)]
        if self.order_status in ['draft', 'sent', 'sale', 'done', 'cancel']:
            domain += [('state', '=', self.order_status)]
        order_ids = self.list_records_in_chunks(model, domain)
        if order_ids:
            self.product_data_export()
            self.customer_data_export()
            for chunk in order_ids:
                job = self.env['job.cron'].create({
                    'function': "order_data_post",
                    'data': chunk,
                    'function_type': 'export',
                    'instance_id': self._context.get('active_id')
                })

    def list_records_in_chunks(self, model, domain=[], chunk_size=50):
        """
        function for fetching and returning the required records as chunks.
        """
        records = model.search(domain).ids
        chunks = [records[i:i + chunk_size] for i in
                  range(0, len(records), chunk_size)]
        return chunks

    def create_categories_woo(self):
        """
        function for posting categories from odoo to woocommerce
        """
        app = self.get_api()
        category_ids = self.env['product.category'].search(
            [('woo_id', '=', False)])
        for category_id in category_ids:
            if category_id.parent_id:
                val = {
                    "name": category_id.name,
                    "parent": category_id.parent_id.woo_id
                }
            else:
                val = {
                    "name": category_id.name,
                }
            res = app.post("products/categories", val).json()
            if res.get('code') and res.get('code') != 'term_exists':
                continue
            if res.get('code') == 'term_exists':
                category_id.woo_id = res['data']['resource_id']
            else:
                category_id.woo_id = res.get('id')
            category_id.instance_id = self._context.get('active_id')

    def create_attributes_woo(self):
        """
                function to create/post attribute and its values from odoo to woocommerce.
        """
        app = self.get_api()
        attribute_ids = self.env['product.attribute'].search([
            ('woo_id', '=', False)
        ])
        attributes_list = []
        for attribute_id in attribute_ids:
            data = {
                "name": attribute_id.name,
                "slug": f'oe_{attribute_id.name}_{attribute_id.id}',
                "type": "select",
                "order_by": "menu_order",
                "has_archives": True,
            }
            att_res = app.post("products/attributes", data).json()
            if att_res.get('code'):
                continue
            if att_res.get('id'):
                val = {'id': attribute_id.id, 'woo_id': att_res.get('id'),
                       'instance_id': self._context.get('active_id')}
                attributes_list.append(val)
                if attribute_id.value_ids:
                    value_list = []
                    for attribute_value in attribute_id.value_ids:
                        val = {'name': attribute_value.name,
                               "slug": f'oe_{attribute_value.name}_{attribute_value.id}'}
                        value_list.append(val)
                    if value_list:
                        data = {}
                        data['create'] = value_list
                        # res = app.post("products", value_list).json()
                        response = app.post(
                            "products/attributes/%s/terms/batch" % att_res.get(
                                'id'),
                            data)
                        if response.json().get('create'):
                            ids = attribute_id.value_ids.mapped('id')
                            attr_odoo_vals = []
                            for index, record in enumerate(
                                    response.json().get('create')):
                                if not record.get('error'):
                                    val = {'id': ids[index],
                                           'woo_id': record.get('id'),
                                           'instance_id': self._context.get(
                                               'active_id')}
                                    attr_odoo_vals.append(val)
                            if attr_odoo_vals:
                                query = """UPDATE product_attribute_value 
                                SET woo_id = %(woo_id)s,instance_id = %(instance_id)s                                
                                            WHERE id = %(id)s"""
                                self.env.cr.executemany(query, attr_odoo_vals)

        if attributes_list:
            query = """ UPDATE product_attribute
                        SET woo_id = %(woo_id)s,instance_id = 
                             %(instance_id)s
                        WHERE id = %(id)s"""
            self.env.cr.executemany(query, attributes_list)

    def create_product_tag_woo(self):
        """
        function for creating woocommerce tags from odoo.
        """
        app = self.get_api()
        tag_ids = self.env['product.tag'].search([('woo_id', '=', False)])
        tag_list = []
        for tag_id in tag_ids:
            data = {
                "name": tag_id.name
            }
            tag_list.append(data)
        if tag_list:
            data = {}
            data['create'] = tag_list
            response = app.post("products/tags/batch", data)
            if response.json().get('create'):
                tag_ids = tag_ids.mapped('id')
                tag_vals = []
                for index, record in enumerate(response.json().get('create')):
                    if not record.get('error'):
                        val = {'id': tag_ids[index],
                               'woo_id': record.get('id')}
                        tag_vals.append(val)
                if tag_vals:
                    query = """ UPDATE product_tag SET woo_id = %(woo_id)s WHERE id = %(id)s """
                    self.env.cr.executemany(query, tag_vals)


    def product_data_post(self, data):
        """
        Function for posting product data from Odoo to WooCommerce.
        """
        app = self.get_api()
        product_ids = self.env['product.template'].browse(data)

        # Pagination Setup
        page = 1
        per_page = 100  # Adjust per_page if necessary, but 100 is usually a reasonable limit
        woo_product_list = []

        while True:
            # Fetch products from WooCommerce with pagination
            response = app.get("products", params={'page': page, 'per_page': per_page}).json()

            if not response:
                break  # No more products to fetch

            woo_product_list.extend(response)  # Add current page of products to the list
            page += 1  # Move to the next page

        woo_ids_in_woo = [str(product['id']) for product in woo_product_list]
        _logger.info(f"All WooCommerce Product IDs: {woo_ids_in_woo}")
        
        # Get Odoo product IDs
        odoo_woo_ids = product_ids.mapped('woo_id')
        _logger.info(f"All Odoo Product IDs: {odoo_woo_ids}")

        # Find products in WooCommerce that do not exist in Odoo
        ids_to_delete = set(woo_ids_in_woo) - set(odoo_woo_ids)
        _logger.info(f"IDs to delete (present in WooCommerce but not in Odoo): {ids_to_delete}")

        # Deleting products in WooCommerce that are not in Odoo
        for woo_id in ids_to_delete:
            try:
                _logger.info(f"Deleting product from WooCommerce: Woo ID {woo_id}")    
                response = app.delete(f"products/{woo_id}").json()
                if response.get('id'):
                    _logger.info(f"Deleted product from WooCommerce: Woo ID {woo_id}")
                else:
                    _logger.warning(f"Failed to delete product from WooCommerce: Woo ID {woo_id}, Response: {response}")
            except Exception as e:
                _logger.error(f"Error while deleting product from WooCommerce: Woo ID {woo_id}, Error: {e}")

        for product_id in product_ids:
            product_type = 'variable' if product_id.attribute_line_ids else 'simple'
            description = product_id.description
            val_list = {
                "name": product_id.name,
                "type": product_type,
                "regular_price": str(self.calc_currency_rate(
                    product_id.list_price, 2)),
                "sku": product_id.default_code if product_id.default_code else "",
                "description": description if description else "",
            }
            stock_check = True if product_id.detailed_type == 'product' else False
            if stock_check:
                stock_qty = product_id.qty_available
                val_list.update({
                    'manage_stock': stock_check,
                    'stock_quantity': str(stock_qty),
                })
            else:
                val_list['manage_stock'] = stock_check
            categories = []
            parent = True
            category_id = product_id.categ_id
            while parent:
                categories.append({
                    'id': category_id.woo_id,
                    'name': category_id.name
                })
                parent = category_id.parent_id
                category_id = parent
            val_list.update({
                "categories": categories
            })
            if product_id.image_1920:
                image_url = self.image_upload(product_id)
                if image_url:
                    val_list.update({
                        "images": [
                            {
                                "src": image_url
                            },
                        ],
                    })
            if product_id.attribute_line_ids:
                attribute_val = []
                for item in product_id.attribute_line_ids:
                    if item.attribute_id.woo_id:
                        attribute_val.append({
                            'id': item.attribute_id.woo_id,
                            'name': item.attribute_id.name,
                            "position": 0,
                            "visible": True,
                            "variation": True,
                            "options": item.value_ids.mapped(
                                'name')
                        })
                val_list.update({
                    'attributes': attribute_val
                })
            if product_id.optional_product_ids:
                cross_sell_ids = [int(item) for item in
                                  product_id.optional_product_ids.mapped(
                                      'woo_id') if
                                  item != False and item.isdigit()]
                val_list['cross_sell_ids'] = cross_sell_ids

            if product_id.alternative_product_ids:
                upsell_ids = [int(item) for item in
                              product_id.alternative_product_ids.mapped(
                                  'woo_id') if
                              item != False and item.isdigit()]
                val_list['upsell_ids'] = upsell_ids

            if product_id.woo_id:
                _logger.info(f"All value list{val_list}")
                res = app.put(f"products/{product_id.woo_id}", val_list).json()
            else:
                res = app.post("products", val_list).json()
                if res.get('code') and res.get(
                        'code') != 'woocommerce_product_image_upload_error':
                    continue
                if res.get('code') == 'woocommerce_product_image_upload_error':
                    val_list['images'] = False
                    res = app.post("products", val_list).json()
                if res.get('id'):
                    product_id.woo_id = res.get('id')
                    product_id.instance_id = self._context.get('active_id')

    def image_upload(self, product):
        """
        Uploads image into WordPress media to get a public link.
        """
        attachment_id = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'product.template'),
             ('res_id', '=', product.id),
             ('res_field', '=', 'image_1920')])
        product_image_url = False
        if attachment_id:
            try:
                attachment_id.public = True
                base_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                product_image_url = f"{base_url}{attachment_id.image_src}.png"
            except Exception as e:
                error = e
        return product_image_url


    def customer_data_post(self, data):
        """function to export and sync customer data with WooCommerce"""
        app = self.get_api()
        value_list = []
        customer_ids = self.env['res.partner'].browse(data)
        
        # Step 1: Process customers from Odoo to WooCommerce (Create/Update)
        for rec in customer_ids:
            if rec.email:
                name = rec.name.rsplit(' ', 1)
                if rec.woo_id:
                    # If WooCommerce ID exists, update the customer data
                    data = {
                        "email": rec.email,
                        "first_name": name[0],
                        "last_name": name[1] if len(name) > 1 else "",
                    }
                else:
                    # Create a new WooCommerce customer if no WooCommerce ID exists
                    username_random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
                    data = {
                        "email": rec.email,
                        "first_name": name[0],
                        "last_name": name[1] if len(name) > 1 else "",
                        "username": f"{name[0]} {name[1]}{username_random_string}" if len(name) > 1 else f"{name[0]}{username_random_string}"
                    }

                billing_addr = self.fetch_address(rec)
                shipping = self.env['res.partner'].sudo().search(
                    [('parent_id', '=', rec.id), ('type', '=', 'delivery')],
                    limit=1
                )
                if shipping:
                    shipping_addr = self.fetch_address(shipping)
                else:
                    shipping_addr = billing_addr
                data['billing'] = billing_addr
                data['shipping'] = shipping_addr

                if rec.woo_id:
                    res = app.put(f'customers/{rec.woo_id}', data).json()
                else:
                    res = app.post('customers', data).json()
                    if res.get('code'):
                        continue
                    else:
                        val = {'id': rec.id, 'woo_id': res.get('id'),
                            'instance_id': self._context.get('active_id'),
                            'woo_user_name': res.get('username')}
                        value_list.append(val)

        # Update Odoo with WooCommerce IDs
        if value_list:
            query = """ UPDATE res_partner
                        SET woo_id = %(woo_id)s, instance_id = %(instance_id)s,
                            woo_user_name = %(woo_user_name)s
                        WHERE id = %(id)s
                    """
            self.env.cr.executemany(query, value_list)

        # Initialize the page and per_page for pagination
        page = 1
        per_page = 100  # You can adjust this value depending on the API limit
        woo_customer_ids = []

        # Step 1: Fetch all WooCommerce customers with pagination
        while True:
            response = app.get(f'customers', params={'page': page, 'per_page': per_page}).json()

            if not response:
                break  # No more customers to fetch

            # Extend the woo_customer_ids list with customer ids from the response
            woo_customer_ids.extend([rec['id'] for rec in response])
            
            page += 1  # Move to the next page
        # Step 2: Get all Odoo customer IDs
        odoo_customer_ids = [rec.woo_id for rec in customer_ids]

        # Ensure both lists are of the same data type (e.g., all integers)
        woo_customer_ids = list(map(int, woo_customer_ids))
        odoo_customer_ids = list(map(int, odoo_customer_ids))

        # Step 3: Find WooCommerce customers who don't exist in Odoo
        missing_woo_customers = set(woo_customer_ids) - set(odoo_customer_ids)

        # Step 4: Delete customers in WooCommerce who are not present in Odoo
        for woo_customer in missing_woo_customers:

            # Search for the Odoo customer using the WooCommerce ID
            odoo_customer = self.env['res.partner'].search([('woo_id', '=', woo_customer)], limit=1)

            if not odoo_customer or odoo_customer.active is False:  # Customer is deleted or not found in Odoo
                # Delete the WooCommerce customer
                app.delete(f'customers/{woo_customer}', params={"force": True}).json()





    def fetch_address(self, obj):
        """
        function for returning basic customer data.
        :returns: The merged key-value pairs.
        :rtype: dict
        """
        val = {}
        name = obj.name if obj.name else obj.parent_id.name
        name = name.rsplit(' ', 1)
        val['first_name'] = name[0]
        val['last_name'] = name[1] if len(name) > 1 else ""
        val['company'] = ""
        if obj.type == 'delivery':
            val[
                'address_1'] = obj.street if obj.street else obj.parent_id.street if obj.parent_id.street else ""
            val[
                'city'] = obj.city if obj.city else obj.parent_id.city if obj.parent_id.city else ""
            val[
                'state'] = obj.state_id.code if obj.state_id.code else obj.parent_id.state_id.code if obj.parent_id.state_id.code else ""
            val[
                'postcode'] = obj.zip if obj.zip else obj.parent_id.zip if obj.parent_id.zip else ""
            val[
                'country'] = obj.country_id.code if obj.country_id.code else obj.parent_id.country_id.code if obj.parent_id.country_id.code else ""
        else:
            val['address_1'] = obj.street if obj.street else ''
            val['city'] = obj.city if obj.city else ''
            val['state'] = obj.state_id.code if obj.state_id.code else ''
            val['postcode'] = obj.zip if obj.zip else ''
            val['country'] = obj.country_id.code if obj.country_id.code else ''
            val['email'] = obj.email if obj.email else ""
            val['phone'] = obj.phone if obj.phone else ""

        val['address_2'] = ''

    def order_data_post(self, data):
        """
        function for post order datas from odoo to woocommerce.
        """
        app = self.get_api()
        order_ids = self.env['sale.order'].browse(data)
        for order_id in order_ids:
            state = 'processing'
            if order_id.state == 'sent':
                state = 'processing'
            elif order_id.state == 'draft':
                state = 'draft'
            elif order_id.state == 'cancel':
                state = 'cancelled'
            elif order_id.state in ['sale', 'done']:
                state = 'processing'
            val_list = {
                'name': order_id.name,
                'customer_id': int(order_id.partner_id.woo_id),
                'date_created': order_id.date_order.isoformat(),
                'state': state,
                'line_items': [],
            }
            for line in order_id.order_line:
                product_id = line.product_id
                taxes = []
                if line.tax_id:
                    for tax in line.tax_id:
                        if tax.woo_id:
                            taxes.append({
                                "id": tax.woo_id,
                                "total": "",
                                "subtotal": "",
                            })
                        else:
                            tax_name = tax.name
                            if tax.amount_type == 'percent':
                                tax_rate = tax.amount
                            else:
                                tax_rate = tax.amount / 100
                            data = {
                                "rate": str(tax_rate),
                                "name": tax_name,
                                "shipping": False
                            }
                            a = app.post("taxes", data).json()
                            if a.get('id'):
                                tax.woo_id = a.get('id')
                                tax.instance_id = self._context.get(
                                    'active_id')
                                taxes.append({
                                    "id": tax.woo_id,
                                    "total": "",
                                    "subtotal": "",
                                })
                if product_id.woo_id:
                    val_list['line_items'].append({
                        'product_id': product_id.woo_id,
                        'name': product_id.name,
                        'quantity': line.product_uom_qty,
                        'taxes': taxes
                    })
            res = app.post('orders', val_list).json()
            if res.get('code'):
                continue
            if res.get('id'):
                order_id.woo_id = res.get('id')
                order_id.instance_id = self._context.get('active_id')


    # export functions
    # Export Sync Function

    def export_sync_details(self):
        """
        function for syncing datas, it creates products, customers, orders
        also updated field in woo commerce on odoo based
        """
        message = {
            'type': 'simple_notification',
            'title': "Product, Order And Customer Export Processing",
            'message': "⏳ The WooCommerce Product, Order And Customer Data Export is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Product, Order And Customer Export Logs Created ✅",
            'message': "The WooCommerce Product, Order And Customer Data Export is complete. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        pending_task = self.env['job.cron'].search(
            [('state', '=', 'pending'),
             ('instance_id', '=', self._context.get('active_id'))])
        if pending_task:
            raise UserError(
                _("Please ensure that there are no pending tasks running currently"))

        self.product_data_export()
        self.customer_data_export()
        self.order_data_export()


    # Import sync functions
    def sync_details(self):
        """
        function for syncing datas, it creates products, customers, orders
        also updated field in odoo based on woo commerce
        """
        message = {
            'type': 'simple_notification',
            'title': "Product, Order And Customer Import Processing",
            'message': "⏳ The WooCommerce Product, Order And Customer Data Import is currently in progress...",
            'sticky': False,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        message = {
            'type': 'simple_notification',
            'title': "Product, Order And Customer Import Logs Created ✅",
            'message': "The WooCommerce Product, Order And Customer Data Import is complete. Now you can view the logs by visiting the Woo Logs page. 🚀",
            'sticky': True,  # Keep the message displayed until it's replaced
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', message)

        pending_task = self.env['job.cron'].search(
            [('state', '=', 'pending'),
             ('instance_id', '=', self._context.get('active_id'))])
        if pending_task:
            raise UserError(
                _("Please ensure that there are no pending tasks running currently"))

        self.customer_data_sync()
        self.product_data_sync()
        self.order_data_sync()

    def customer_data_sync(self):
        """
        function for syncing customer data from woocommerce to odoo.
        """
        page = 1
        customers_list = []
        app = self.get_api()
        while True:
            customer_data = app.get('customers', params={
                'per_page': 50, 'page': page}).json()
            page += 1
            if not customer_data:
                break
            else:
                customers_list += customer_data
        if customers_list:
            for i in range(0, len(customers_list), 50):
                data = customers_list[i:i + 50]
                job = self.env['job.cron'].create({
                    'function': "write_customer",
                    'data': data,
                    'instance_id': self._context.get('active_id'),
                    'function_type': 'import'
                })

    def product_data_sync(self):
        """
        function for syncing product data from woocommerce to odoo.
        """
        page = 1
        app = self.get_api()
        self.category_values()  # creating new categories and attributes
        self.product_attribute_data_import()
        while True:
            product_data = app.get('products', params={
                'per_page': 50, 'page': page}).json()
            page += 1
            if not product_data:
                break
            else:
                job = self.env['job.cron'].create({
                    'function': "write_product_data",
                    'data': product_data,
                    'instance_id': self._context.get('active_id'),
                    'function_type': 'import'
                })

    def order_data_sync(self):
        """
        function to import woo commerce orders,
        its also import all products, customers
        """
        app = self.get_api()

        page = 1  # The first page number to loop is page 1
        orders = []
        while True:
            order_data = app.get('orders', params={
                'per_page': 100, 'page': page}).json()
            page += 1
            if not order_data:
                break
            orders += order_data
        chunk_size = 50
        context = []
        chunk = []
        if self.order_status in ['draft', 'sent', 'sale', 'done', 'cancel']:
            if self.order_status in ['sale', 'done']:
                orders = [record for record in orders if
                          record["status"] in ['pending', 'processing',
                                               'on-hold', 'completed',
                                               'refunded']]
            elif self.order_status == 'cancel':
                orders = [record for record in orders if
                          record["status"] in ['cancelled']]
            elif self.order_status == 'sent':
                orders = [record for record in orders if
                          record["status"] in ['failed']]
            else:
                orders = [record for record in orders if
                          record["status"] not in ['failed', 'cancelled',
                                                   'pending', 'processing',
                                                   'on-hold', 'completed',
                                                   'refunded']]

        if self.start_date and self.end_date:
            for rec in orders:
                order_create_date = rec.get('date_created').split('T')[0]
                ord_date = datetime.strptime(order_create_date,
                                             '%Y-%m-%d').date()
                if self.start_date <= ord_date <= self.end_date:
                    chunk.append(rec)
                    if len(chunk) == chunk_size:
                        context.append(chunk)
                        chunk = []
        elif self.start_date:
            for rec in orders:
                order_create_date = rec.get('date_created').split('T')[0]
                ord_date = datetime.strptime(order_create_date,
                                             '%Y-%m-%d').date()
                if ord_date >= self.start_date:
                    chunk.append(rec)
                    if len(chunk) == chunk_size:
                        context.append(chunk)
                        chunk = []
        elif self.end_date:
            for rec in orders:
                order_create_date = rec.get('date_created').split('T')[0]
                ord_date = datetime.strptime(order_create_date,
                                             '%Y-%m-%d').date()
                if ord_date <= self.end_date:
                    chunk.append(rec)
                    if len(chunk) == chunk_size:
                        context.append(chunk)
                        chunk = []
        else:
            for i in range(0, len(orders), chunk_size):
                context.append(orders[i:i + chunk_size])
        if context:
            # creating new categories,attributes,products,customers
            self.category_values()
            self.product_attribute_data_import()
            self.tax_data_import()
            for rec in context:
                job = self.env['job.cron'].create({
                    'function': "create_order",
                    'data': rec,
                    'function_type': 'import',
                    'instance_id': self._context.get('active_id')
                })

    def write_customer(self, data):
        """
        function for syncing customer data, it creates/writes customers from
        WooCommerce to Odoo.
        """
        
        existing_woo_ids = [str(rec['id']) for rec in data]
        instance_id = self._context.get('active_id')  # current connection's instance_id
        
        # Fetch all customers in Odoo with woo_id
        all_customers = self.env['res.partner'].search([
            ('woo_id', '!=', False), 
            ('type', '=', 'contact'),
            ('instance_id', '=', instance_id)  # Match the current connection's instance_id
        ])
    
    # Check customers in Odoo that don't exist in WooCommerce (to delete them)
        for customer in all_customers:
            if customer.woo_id not in existing_woo_ids:
                # Customer not found in WooCommerce, so delete from Odoo
                customer.unlink()

        partner_ids = self.env['res.partner'].search(
            [('woo_id', '!=', False), ('type', '=', 'contact')])
        for rec in data:
            partner_id = partner_ids.filtered(
                lambda r: r.woo_id == str(rec['id']))
            if partner_id:
                existing_values = partner_id.read(
                    ['name', 'email', 'phone', 'street', 'street2', 'city',
                     'zip', 'state_id', 'country_id', 'woo_id',
                     'woo_user_name', 'company_id', 'company_type'])
                if existing_values[0].get('state_id'):
                    existing_values[0]['state_id'] = \
                        existing_values[0]['state_id'][0]
                if existing_values[0].get('country_id'):
                    existing_values[0]['country_id'] = \
                        existing_values[0]['country_id'][0]
                if existing_values[0].get('company_id'):
                    existing_values[0]['company_id'] = \
                        existing_values[0]['company_id'][0]
                existing_values[0].pop("id", None)
                woocommerce_values = {
                    'company_type': "person",
                    'name': rec.get('first_name') + " " + rec.get(
                        'last_name'),
                    'email': rec.get('email'),
                    'phone': rec['billing']['phone'],
                    'street': rec['billing']['address_1'],
                    'street2': rec['billing']['address_2'],
                    'city': rec['billing']['city'],
                    'zip': rec['billing']['postcode'],
                    'state_id': self.env['res.country.state'].search(
                        [('code', '=', rec['billing']['state']),
                         ('country_id', '=',
                          rec['billing']['country'])]).id,
                    'country_id': self.env['res.country'].search(
                        [('code', '=', rec['billing']['country'])]).id,
                    'woo_id': str(rec.get('id')),
                    'woo_user_name': rec.get('username'),
                    'company_id': self.env.company.id if self.company else False
                }
                if not existing_values[0] == woocommerce_values:
                    partner_id.write(woocommerce_values)
                if rec.get('shipping'):
                    shipping_address = {}
                    first_name = rec['shipping'].get("first_name") or ''
                    last_name = rec['shipping'].get("last_name") or ''
                    name = first_name + " " + last_name if first_name or last_name else ''
                    if name:
                        shipping_address['name'] = name
                        shipping_address['zip'] = rec['shipping'].get(
                            "postcode") or ''
                        shipping_address['street'] = rec['shipping'].get(
                            "address_1") or ''
                        shipping_address['street2'] = rec['shipping'].get(
                            "address_2") or ''
                        shipping_address['city'] = rec.get('shipping').get(
                            "city") or ''
                        shipping_address['phone'] = rec['shipping'].get(
                            "phone") or ''
                        state = rec.get('shipping').get("state") or ''
                        country = rec.get('shipping').get("country") or ''
                        country_id = self.env['res.country'].sudo().search(
                            [('code', '=', country)], limit=1)
                        state_id = self.env['res.country.state'].sudo().search(
                            ['&', ('code', '=', state),
                             ('country_id', '=', country_id.id)], limit=1)
                        shipping_address[
                            'country_id'] = False if not country_id else country_id.id
                        shipping_address[
                            'state_id'] = False if not state_id else state_id.id
                        shipping_address['woo_id'] = str(rec.get('id'))
                        shipping_address['woo_user_name'] = rec.get('username')
                        if not partner_id.child_ids.filtered(
                                lambda x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id'])):
                            # no delivery address added so create
                            shipping_address['parent_id'] = partner_id.id
                            shipping_address['type'] = 'delivery'
                            shipping_address[
                                'instance_id'] = self._context.get(
                                'active_id') if self._context.get(
                                'active_id') else False
                            new_delivery_contact = self.env[
                                'res.partner'].create(shipping_address)
                        else:
                            # check and compare the details of the delivery address
                            child_id = partner_id.child_ids.filtered(
                                lambda
                                    x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id']))
                            if not len(child_id) > 1:
                                current_delivery_address = child_id.read(
                                    ['name', 'zip', 'street', 'street2',
                                     'city',
                                     'phone', 'country_id', 'state_id',
                                     'woo_id', 'woo_user_name'])
                                if current_delivery_address[0].get('state_id'):
                                    current_delivery_address[0]['state_id'] = \
                                        current_delivery_address[0][
                                            'state_id'][
                                            0]
                                if current_delivery_address[0].get(
                                        'country_id'):
                                    current_delivery_address[0]['country_id'] = \
                                        current_delivery_address[0][
                                            'country_id'][0]
                                current_delivery_address[0].pop("id", None)
                                if not current_delivery_address[
                                           0] == shipping_address:
                                    shipping_address[
                                        'instance_id'] = self._context.get(
                                        'active_id')
                                    update_delivery_address = child_id.write(
                                        shipping_address)
                    else:
                        # might need to delete the record after unlinking from parent
                        if partner_id.child_ids.filtered(
                                lambda x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id'])):
                            child_to_remove = partner_id.child_ids.filtered(
                                lambda
                                    x: x.type == 'delivery' and x.woo_id == str(
                                    rec['id']))
                            child_to_remove.unlink()
            else:
                existing_id = self.env['res.partner'].search(
                    [('type', '=', 'contact'),
                     ('email', '=', rec.get('email'))])
                if existing_id:
                    if not len(existing_id) > 1:
                        vals = {
                            'woo_id': rec.get('id'),
                            'woo_user_name': rec.get('username'),
                            'instance_id': self._context.get(
                                'active_id') if self._context.get(
                                'active_id') else False,
                            'company_id': self.env.company.id if self.company else False,
                        }
                        if vals:
                            partner = self.env['res.partner'].write(vals)
                else:
                    partner_id = self.create_new_customer(rec)

    def write_product_data(self, data):
        """
        Function to sync products with WooCommerce, and delete/archive products only for the current connection.
        """
        # Get the current connection's instance ID (WooCommerce store)
        active_instance_id = self._context.get('active_id')

        # Fetch all products linked to the current connection (instance_id)
        prod_ids = self.env['product.template'].search([('instance_id', '=', active_instance_id)])

        # Extract WooCommerce product IDs from the incoming data
        woo_product_ids = [str(rec['id']) for rec in data]

        # Archive/Delete products in Odoo that are not found in the current WooCommerce connection
        for prod in prod_ids:
            if str(prod.woo_id) not in woo_product_ids:
                # If the product is not found in the current WooCommerce connection, archive it
                prod.write({'active': False})  # Soft delete (archive the product)

        # Process the data for adding/updating products from WooCommerce
        for rec in data:
            prod_id = prod_ids.filtered(lambda r: r.woo_id == str(rec['id']))
            
            if prod_id:
                if rec.get('type') in ['simple', 'bundle']:
                    self.write_simple_product(rec, prod_id)
                if rec.get('type') == 'variable':
                    self.write_variant_product(rec, prod_id)
            else:
                if rec.get('type') in ['simple', 'bundle']:
                    self.simple_product_create(rec)
                if rec.get('type') == 'variable':
                    self.variant_product_tmpl_create(rec)


    def write_simple_product(self, data, product):
        """
        Function to write data to a simple WooCommerce product without variants
        and update stock quantity in Odoo if it has changed.
        """
        
        # Prepare the product data
        val_list = self.prepare_product_vals(data)
        del val_list['detailed_type']  # Remove the detailed_type field for updates
        
        # Set the instance ID from the active context
        val_list['instance_id'] = self._context.get('active_id') if self._context.get('active_id') else False
        
        # Process the product image and categories
        image = self.get_product_image(data)
        categories_value = data.get('categories')
        
        # Retrieve category details and update the category ID
        if categories_value:
            category_woo_id = categories_value[0].get('id')
            category_id = self.env['product.category'].search([('woo_id', '=', category_woo_id)], limit=1)
            if category_id:
                val_list['categ_id'] = category_id.id
        
        # Process and update images
        if image.get('main_image'):
            val_list.update(image.get('main_image'))
        if image.get('product_template_image_ids'):
            val_list['product_template_image_ids'] = image.get('product_template_image_ids')
        
        # Set the product as a service if it is virtual
        if data.get('virtual'):
            val_list['detailed_type'] = 'service'

        # Optional and alternative product IDs (if applicable)
        val_list['optional_product_ids'] = [(6, 0, val_list.get('optional_product_ids', []))]
        val_list['alternative_product_ids'] = [(6, 0, val_list.get('alternative_product_ids', []))]
        
        # Update the product with the new values
        updated_product_id = product.write(val_list)

        # Check if the product type is consumable or service before updating stock
        if data.get('stock_quantity') is not None and product.detailed_type not in ['service', 'consu']:
            new_stock_quantity = data.get('stock_quantity')
            
            # Find the product variant (if exists)
            product_variant = product.product_variant_ids
            if product_variant:
                # Locate the stock quant record for the product
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', product_variant.id),
                    ('location_id', '=', self.env.ref('stock.stock_location_stock').id)
                ], limit=1)
                
                # If stock quant exists, update it
                if stock_quant:
                    stock_quant.write({
                        'quantity': new_stock_quantity,
                        'inventory_quantity': new_stock_quantity
                    })
                else:
                    # If no stock quant found, create a new one
                    stock_vals = {
                        'product_id': product_variant.id,
                        'location_id': self.env.ref('stock.stock_location_stock').id,
                        'quantity': new_stock_quantity,
                        'inventory_quantity': new_stock_quantity,
                        'on_hand': True,
                    }
                    self.env['stock.quant'].sudo().create(stock_vals)

        return updated_product_id



    def write_variant_product(self, data, product):
        """
        Function to write a given product with variants.
        """
        app = self.get_api()
        val_list = self.prepare_product_vals(data)
        del val_list['detailed_type']
        val_list['instance_id'] = self._context.get(
            'active_id') if self._context.get('active_id') else False
        image = self.get_product_image(data)
        categories_value = data.get('categories')
        category_woo_id = categories_value[0].get('id')
        category_id = self.env['product.category'].search(
            [('woo_id', '=', category_woo_id)], limit=1)
        if category_id:
            val_list['categ_id'] = category_id.id
        if image.get('main_image'):
            val_list.update(image.get('main_image'))
        if image.get('product_template_image_ids'):
            val_list['product_template_image_ids'] = image.get(
                'product_template_image_ids')
        variants = False
        # try:
        #     params = {"per_page": 100}
        #     response = app.get("products/%s/variations" % (data.get("id")),
        #                        params=params)
        #     variants = response.json()
        #
        # except Exception as error:
        #     message = "Error While Importing Product Variants from WooCommerce. \n%s" % (
        #         error)
        #     return message
        variants_response = []
        try:
            page = 1
            params = {"per_page": 100}
            while True:
                params['page'] = page
                response = app.get("products/%s/variations" % (data.get("id")),
                                   params=params).json()
                page += 1
                if response and isinstance(response, list):
                    variants_response += response
                else:
                    break
        except Exception as error:
            message = "Error While Importing Product Variants from WooCommerce. \n%s" % (
                error)
            return message
        # if data.get('virtual'):
        #     val_list['detailed_type'] = 'service'
        variant_vals = {}
        # intialise to avoid error for products having no variant data.
        if variants_response:
            # attribute_line_ids = self.get_attributes_line_vals(variants)
            variant_vals = self.update_variants(variants_response)
        val_list['optional_product_ids'] = [
            (6, 0, val_list['optional_product_ids'])]
        val_list['alternative_product_ids'] = [
            (6, 0, val_list['alternative_product_ids'])]
        updated_product_id = product.write(val_list)

        for rec in variant_vals:
            var_id = rec.pop('woo_var_id')
            product_var = self.env['product.product'].search(
                [('woo_var_id', '=', str(var_id))])
            if product_var:
                rec.pop('combination')
                updated_product_var = product_var.write(rec)

    # def write_order_data(self, data):
    #     """function for syncing order datas, it creates/write products,
    #      customers, orders also updated field in odoo based on woo commerce
    #             """
    #     app = self.get_api()
    #     partner_obj = self.env['res.partner']
    #     tax_ids = self.env['account.tax'].search([])
    #     prod_obj = self.env['product.template']
    #     prod_var_obj = self.env['product.product']
    #     order_ids = self.env['sale.order'].search([
    #         ('woo_id', '!=', False)
    #     ])
    #     for item in data:
    #         order_id = order_ids.filtered(
    #             lambda r: r.woo_id == str(item['id']))
    #         if order_id:
    #             if order_id[0].state in ['draft', 'sent', 'cancel']:
    #                 state = 'draft'
    #                 if item.get('status') == 'failed':
    #                     state = 'sent'
    #                 order_val = {}
    #                 order_val['state'] = state
    #                 partner_id = False
    #                 if item.get('customer_id'):
    #                     partner = partner_obj.search(
    #                         [('woo_id', '!=', False), (
    #                             'type', '=', 'contact')]).filtered(
    #                         lambda x: x.woo_id == str(item.get('customer_id')))
    #                     if partner:
    #                         partner_id = partner
    #                 else:
    #                     partner_id = self.env.ref(
    #                         'woocommerce_odoo_bridge.woocommerce_guest')
    #                 if partner_id:
    #                     order_val.update({
    #                         'partner_id': partner_id,
    #                         'woo_coupon_ids': False
    #                     })
    #                 order_id[0].order_line.unlink()
    #                 orderline = []
    #                 for line_item in item.get('line_items'):
    #                     woo_tax = []
    #                     for tax in line_item['taxes']:
    #                         woo_tax.append(str(tax['id']))
    #                     tax_id = tax_ids.filtered(
    #                         lambda r: r.woo_id in woo_tax)
    #                     main_product = prod_obj.search([]).filtered(
    #                         lambda r: r.woo_id == str(
    #                             line_item['product_id']))
    #                     if main_product:
    #                         main_product = main_product[0]
    #                         product = False
    #                         if len(main_product.product_variant_ids) > 1:
    #                             product = prod_var_obj.search([]).filtered(
    #                                 lambda r: r.woo_var_id == str(
    #                                     line_item['id']))
    #                             if not product:
    #                                 product = main_product.product_variant_ids[
    #                                     0]
    #                         else:
    #                             product = main_product.product_variant_ids[
    #                                 0]
    #                         if product:
    #                             val = {
    #                                 'name': product.name,
    #                                 'product_id': product.id,
    #                                 'price_unit': float(line_item['price']),
    #                                 'product_uom_qty': line_item[
    #                                     'quantity'],
    #                                 'tax_id': tax_id.ids,
    #                                 'customer_lead': 1,
    #                             }
    #                             orderline.append((0, 0, val))
    #                     else:
    #                         # here we might need to create a new product instead of calling import product function
    #                         products_data = app.get(
    #                             'products/%s' % line_item['product_id'],
    #                             params={
    #                                 'per_page': 100, 'page': 1}).json()
    #                         if products_data.get('type') in ['simple',
    #                                                          'variable',
    #                                                          'bundle',
    #                                                          'grouped',
    #                                                          'external']:
    #                             # currently including these woocommerce product types only
    #                             product = False
    #                             if products_data.get('type') in ['simple',
    #                                                              'bundle']:
    #                                 # no need to create variants for these products so we can use a separate function
    #                                 simple_product = self.simple_product_create(
    #                                     products_data)
    #                                 if simple_product:
    #                                     product = prod_obj.search([]).filtered(
    #                                         lambda r: r.woo_id == str(
    #                                             simple_product))
    #                                     if product[0]:
    #                                         product = \
    #                                             product[0].product_variant_ids[
    #                                                 0]

    #                             if products_data.get('type') == 'variable':
    #                                 # need to create variants for these products
    #                                 variant_product = self.variant_product_tmpl_create(
    #                                     products_data)
    #                                 product = prod_var_obj.search([]).filtered(
    #                                     lambda r: r.woo_var_id == str(
    #                                         line_item['id']))
    #                             if product:
    #                                 val = {
    #                                     'name': product.name,
    #                                     'product_id': product.id,
    #                                     'product_uom_qty': line_item[
    #                                         'quantity'],
    #                                     'price_unit': float(
    #                                         line_item['price']),
    #                                     'tax_id': tax_id.ids,
    #                                     'customer_lead': 1
    #                                 }
    #                                 orderline.append((0, 0, val))
    #                 for line_item in item.get('shipping_lines'):
    #                     if not line_item.get('method_id') or line_item.get(
    #                             'method_id') == 'other':
    #                         product = self.env.ref(
    #                             'woocommerce_odoo_bridge.product_product_woocommerce_other_hwe')
    #                     if line_item.get('method_id') == 'flat_rate':
    #                         product = self.env.ref(
    #                             'woocommerce_odoo_bridge.product_product_flat_delivery')
    #                     if line_item.get('method_id') == 'local_rate':
    #                         product = self.env.ref(
    #                             'woocommerce_odoo_bridge.product_product_local_delivery')
    #                     if line_item.get('method_id') == 'free_shipping':
    #                         product = self.env.ref(
    #                             'woocommerce_odoo_bridge.product_product_woocommerce_free_delivery_hwe')
    #                     val = {
    #                         'name': product.name,
    #                         'product_id': product.product_variant_ids[0].id,
    #                         'tax_id': False,
    #                         'price_unit': float(line_item['total']),
    #                         'product_uom_qty': 1,
    #                         'customer_lead': 1,
    #                     }
    #                     orderline.append((0, 0, val))
    #                 for line_item in item.get('fee_lines'):
    #                     product = self.env.ref(
    #                         'woocommerce_odoo_bridge.woocommerce_fee_lines')
    #                     val = {
    #                         'name': product.name,
    #                         'product_id': product.product_variant_ids[0].id,
    #                         'tax_id': False,
    #                         'price_unit': float(line_item['total']),
    #                         'product_uom_qty': 1,
    #                         'customer_lead': 1,
    #                     }
    #                     orderline.append((0, 0, val))
    #                 # for line_item in item.get('coupon_lines'):
    #                 #     if line_item.get('discount', None):
    #                 #         product = self.env.ref(
    #                 #             'woocommerce_odoo_bridge.woocommerce_coupons')
    #                 #         val = {
    #                 #             'name': product.name,
    #                 #             'product_id': product.product_variant_ids[
    #                 #                 0].id,
    #                 #             'tax_id': False,
    #                 #             'price_unit': -1 * float(
    #                 #                 line_item['discount']),
    #                 #             'product_uom_qty': 1,
    #                 #             'customer_lead': 1,
    #                 #         }
    #                 #         orderline.append((0, 0, val))
    #                 if orderline:
    #                     order_val['order_line'] = orderline
    #                 if order_val:
    #                     order_id[0].write(order_val)
    #                 if item.get('status') in ['cancelled'] and order_id[
    #                     0].state != 'cancel':
    #                     order_id[0].with_context(
    #                         {'disable_cancel_warning': True}).action_cancel()
    #         else:
    #             self.create_order([item])

    # syncing functions end

    # export/update records to woocommerce

    def update_to_woo_commerce(self, data, type):
        """
        function to update/export customer,product,orders data to woo commerce
        """
        if data:
            if type == 'customers':
                records = data.ids
                customer_list = [records[i:i + 100] for i in
                                 range(0, len(records), 100)]
                for chunk in customer_list:
                    job = self.env['job.cron'].create({
                        'function': "customer_data_woo_update",
                        'data': chunk,
                        'function_type': 'export',
                        'instance_id': self._context.get('active_id')
                    })
                    # self.customer_data_woo_update(chunk)
            if type == 'products':
                self.create_categories_woo()
                self.create_attributes_woo()
                self.create_product_tag_woo()
                records = data.ids
                product_list = [records[i:i + 50] for i in
                                range(0, len(records), 50)]
                for chunk in product_list:
                    job = self.env['job.cron'].create({
                        'function': "product_data_woo_update",
                        'data': chunk,
                        'function_type': 'export',
                        'instance_id': self._context.get('active_id')
                    })
            if type == 'orders':
                self.product_data_export()
                self.customer_data_export()
                records = data.ids
                order_list = [records[i:i + 50] for i in
                              range(0, len(records), 50)]
                for chunk in order_list:
                    job = self.env['job.cron'].create({
                        'function': "order_data_woo_update",
                        'data': chunk,
                        'function_type': 'export',
                        'instance_id': self._context.get('active_id')
                    })

    def customer_data_woo_update(self, data):
        """
        function to update/export customer data to woo commerce
        """
        app = self.get_api()
        instance_id = self._context.get('active_id')
        value_list = []
        customer_ids = self.env['res.partner'].browse(data)
        for rec in customer_ids:
            if rec.email:
                # updating the condition as email a mandatory field or skip the current record
                name = rec.name.rsplit(' ', 1)
                data = {
                    "email": rec.email,
                    "first_name": name[0],
                    "last_name": name[1] if len(name) > 1 else "",
                    "username": rec.email,
                }
                billing_addr = self.fetch_address(rec)
                shipping = self.env['res.partner'].sudo().search(
                    [('parent_id', '=', rec.id), ('type', '=', 'delivery')],
                    limit=1)
                if shipping:
                    shipping_addr = self.fetch_address(shipping)
                else:
                    shipping_addr = billing_addr
                data['billing'] = billing_addr
                data['shipping'] = shipping_addr
                if not rec.woo_id:
                    res = app.post('customers', data).json()
                    if res.get('code'):
                        message = res.get('message')
                    else:
                        val = {'id': rec.id, 'woo_id': res.get('id'),
                               'instance_id': instance_id,
                               'woo_user_name': res.get('username')}
                        value_list.append(val)
                else:
                    data.pop('username')
                    res = app.put(f"customers/{rec.woo_id}",
                                  data).json()
                    if res.get('code'):
                        message = res.get('message')
                    else:
                        val = {'id': rec.id, 'woo_id': res.get('id'),
                               'instance_id': instance_id,
                               'woo_user_name': res.get('username')}
                        value_list.append(val)

        if value_list:
            query = """ UPDATE res_partner
                                SET woo_id = %(woo_id)s,
                                    instance_id = %(instance_id)s,
                                    woo_user_name = %(woo_user_name)s
                                WHERE id = %(id)s
                            """

            self.env.cr.executemany(query, value_list)

    def product_data_woo_update(self, data):
        """
        function to update/export product data to woo commerce
        """
        app = self.get_api()
        instance_id = self._context.get('active_id')
        if data:
            product_data = self.env['product.template'].browse(data)
            for product_id in product_data:
                product_type = 'variable' if product_id.attribute_line_ids else 'simple'
                description = product_id.description
                val_list = {
                    "name": product_id.name,
                    "type": product_type,
                    "regular_price": str(self.calc_currency_rate(
                        product_id.list_price, 2)),
                    "sku": product_id.default_code if product_id.default_code else "",
                    "description": description if description else "",
                }
                stock_check = True if product_id.detailed_type == 'product' else False
                if stock_check:
                    stock_qty = product_id.qty_available
                    val_list.update({
                        'manage_stock': stock_check,
                        'stock_quantity': str(stock_qty),
                    })
                else:
                    val_list['manage_stock'] = stock_check
                categories = []
                parent = True
                category_id = product_id.categ_id
                while parent:
                    categories.append({
                        'id': category_id.woo_id,
                        'name': category_id.name,
                        'slug': category_id.name
                    })
                    parent = category_id.parent_id
                    category_id = parent
                val_list.update({
                    "categories": categories
                })
                if product_id.image_1920:
                    image_url = self.image_upload(product_id)
                    val_list.update({
                        "images": [
                            {
                                "src": image_url
                            },
                        ],
                    })
                if product_id.attribute_line_ids:
                    attribute_val = []
                    for item in product_id.attribute_line_ids:
                        if item.attribute_id.woo_id:
                            attribute_val.append({
                                'id': item.attribute_id.woo_id,
                                'name': item.attribute_id.name,
                                "position": 0,
                                "visible": True,
                                "variation": True,
                                "options": item.value_ids.mapped(
                                    'name')
                            })
                    val_list.update({
                        'attributes': attribute_val
                    })
                if product_id.optional_product_ids:
                    cross_sell_ids = [int(item) for item in
                                      product_id.optional_product_ids.mapped(
                                          'woo_id') if
                                      item != False and item.isdigit()]
                    val_list['cross_sell_ids'] = cross_sell_ids
                if product_id.alternative_product_ids:
                    upsell_ids = [int(item) for item in
                                  product_id.alternative_product_ids.mapped(
                                      'woo_id') if
                                  item != False and item.isdigit()]
                    val_list['upsell_ids'] = upsell_ids
                if not product_id.woo_id:
                    res = app.post("products", val_list).json()
                    if res.get(
                            'code') == 'woocommerce_product_image_upload_error':
                        val_list['images'] = False
                        res = app.post("products", val_list).json()

                    if res.get('id'):
                        product_id.woo_id = res.get('id')
                        product_id.instance_id = instance_id
                        product_id.woo_variant_check = True
                        # if product_id.attribute_line_ids:
                        #     post_variants_list = []
                        #     for variant in product_id.product_variant_ids:
                        #         post_variants_attrs_list = []
                        #         values = variant.product_template_variant_value_ids.product_attribute_value_id.mapped('name')
                        #         for index, value in enumerate(variant.product_template_variant_value_ids.attribute_id.mapped('woo_id')):
                        #             post_variants_attrs_list.append({'id':int(value),'option':values[index]})
                        #         post_variants_list.append({"regular_price":"10.00",
                        #          "attributes":post_variants_attrs_list
                        #          })
                        #     data = {"create": post_variants_list}
                        #     res = app.post("products/"+str(res.get('id'))+"/variations/batch",
                        #                      data).json()

                else:
                    res = app.put(f"products/{product_id.woo_id}",
                                  val_list).json()
                    if res.get(
                            'code') == 'woocommerce_product_image_upload_error':
                        val_list['images'] = False
                        res = app.post("products", val_list).json()
                    if res.get('id'):
                        product_id.woo_id = res.get('id')
                        product_id.instance_id = instance_id
                        product_id.woo_variant_check = True

    def order_data_woo_update(self, data):
        """
            function to update/export orders data to woo commerce
        """
        app = self.get_api()
        instance_id = self._context.get('active_id')
        if data:
            order_data = self.env['sale.order'].browse(data)
            for order_id in order_data:
                state = 'processing'
                if order_id.state == 'sent':
                    state = 'processing'
                elif order_id.state == 'draft':
                    state = 'draft'
                elif order_id.state == 'cancel':
                    state = 'cancelled'
                elif order_id.state == 'sale':
                    state = 'completed'
                val_list = {
                    'name': order_id.name,
                    'customer_id': int(order_id.partner_id.woo_id),
                    'date_created': order_id.date_order.isoformat(),
                    'state': state,
                    'line_items': [],
                }
                # currently it is not updating the existing lines so adding new lines will only create duplicate lines
                # for line in order_id.order_line:
                #     product_id = line.product_id
                #     taxes = []
                #     if line.tax_id:
                #         for tax in line.tax_id:
                #             if tax.woo_id:
                #                 taxes.append({
                #                     "id": tax.woo_id,
                #                     "total": "",
                #                     "subtotal": "",
                #                 })
                #             else:
                #                 tax_name = tax.name
                #                 if tax.amount_type == 'percent':
                #                     tax_rate = tax.amount
                #                 else:
                #                     tax_rate = tax.amount / 100
                #                 data = {
                #                     "rate": str(tax_rate),
                #                     "name": tax_name,
                #                     "shipping": False
                #                 }
                #                 a = app.post("taxes", data).json()
                #                 if a.get('id'):
                #                     tax.woo_id = a.get('id')
                #                     tax.instance_id = instance_id.id
                #                     taxes.append({
                #                         "id": tax.woo_id,
                #                         "total": "",
                #                         "subtotal": "",
                #                     })
                #     val_list['line_items'].append({
                #         'product_id': product_id.woo_id,
                #         'name': product_id.name,
                #         'quantity': line.product_uom_qty,
                #         'taxes': taxes
                #     })
                if not order_id.woo_id:
                    res = app.post('orders', val_list).json()
                    if res.get('code'):
                        continue
                        # self.env['woo.logs'].sudo().create({
                        #     'status': 'failed',
                        #     'trigger': 'order_data_export_failed',
                        #     'description': res.get('code')
                        # })
                    if res.get('id'):
                        order_id.woo_id = res.get('id')
                        order_id.instance_id = instance_id
                if order_id.woo_id:
                    res = app.put(f"orders/{order_id.woo_id}", val_list).json()
                    if res.get('id'):
                        order_id.woo_id = res.get('id')
                        order_id.instance_id = instance_id
