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
from odoo.exceptions import UserError




class ProductTemplateHwe(models.Model):
    _inherit = 'product.template'
    _description = "Inheriting Product Template"

    def image_upload(self, product):
        """
        Uploads image into wordpress media to get a public link.
        """
        attachment_id = self.env['ir.attachment'].sudo().search(
            domain=[('res_model', '=', 'product.template'),
                    ('res_id', '=', product.id),
                    ('res_field', '=', 'image_1920')])
        product_image_url = False
        if attachment_id:
            attachment_id.public = True
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            product_image_url = f"{base_url}{attachment_id.image_src}.png"
        return product_image_url

    def sync_products(self):
        return {
            'name': _('Sync Prodcuts'),
            'view_mode': 'form',
            'res_model': 'woocommerce.update.wizard',
            'view_id': self.env.ref('woocommerce_odoo_bridge.woocommerce_update_form_display').id,
            'type': 'ir.actions.act_window',
            'context':{'operation_type':'products','active_ids':self.ids},
            'target': 'current'
        }
        # for product_id in self:
        #     if product_id.instance_id:
        #         app = API(
        #             url="" + product_id.instance_id.store_url + "/index.php/",
        #             # Your store URL
        #             consumer_key=product_id.instance_id.consumer_key,
        #             # Your consumer key
        #             consumer_secret=product_id.instance_id.consumer_secret,
        #             # Your consumer secret
        #             wp_api=True,  # Enable the WP REST API integration
        #             version="wc/v3",  # WooCommerce WP REST API version
        #             timeout=500,
        #         )
        #         image_url = self.image_upload(product_id)
        #
        #         val_list = {
        #             "name": product_id.name,
        #             "regular_price": str(product_id.list_price),
        #             "description": product_id.description if product_id.description else "",
        #             "sku": product_id.default_code if product_id.default_code else "",
        #             'manage_stock': True if product_id.detailed_type == 'product' else False,
        #             'stock_quantity': str(product_id.qty_available),
        #             "images": [
        #                 {
        #                     "src": image_url,
        #                 }
        #             ],
        #         }
        #         categories = []
        #         category_id = product_id.categ_id
        #         categories.append({
        #             'id': category_id.woo_id,
        #             'name': category_id.name,
        #             'slug': category_id.name
        #         })
        #         val_list.update({
        #             "categories": categories
        #         })
        #         app.put(f"products/{product_id.woo_id}", val_list).json()

    def unlink(self):
        super(ProductTemplateHwe, self).unlink()
        for product_id in self:
            if product_id.instance_id:
                app = API(
                    url="" + product_id.instance_id.store_url + "/index.php/",
                    # Your store URL
                    consumer_key=product_id.instance_id.consumer_key,
                    # Your consumer key
                    consumer_secret=product_id.instance_id.consumer_secret,
                    # Your consumer secret
                    wp_api=True,  # Enable the WP REST API integration
                    version="wc/v3",  # WooCommerce WP REST API version
                    timeout=500,
                )
                app.delete(f"products/{product_id.woo_id}", params={"force": True}).json()

