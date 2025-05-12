######################################################################################
#
#    CnEL India
#
#    Copyright (C) 2024-TODAY CnEl India(<https://cnelindia.com/>).
#    Author: Gulshan Saini (odoo@cnelindia.com)
#######################################################################################
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
from odoo import models
from woocommerce import API
from odoo.exceptions import ValidationError
from odoo import models, api,_


class ResPartnerHwe(models.Model):
    _inherit = 'res.partner'
    _description = "Inheriting Res Partner"

    @api.constrains('email')
    def _check_unique_email(self):
        for record in self:
            if record.email:
                domain = [('type', '=', 'contact'), ('id', '!=', record.id),
                          ('email', '=', record.email.lower())]
                duplicate_records = self.search(domain, limit=1)
                if duplicate_records:
                    raise ValidationError(_('The email already exists!'))

    def image_upload(self, product):
        """
        Uploads image into wordpress media to get a public link.
        """
        attachment_id = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'res.partner'),
                    ('res_id', '=', product.id),
                    ('res_field', '=', 'image_1920')])
        product_image_url = False
        if attachment_id:
            attachment_id.public = True
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            product_image_url = f"{base_url}{attachment_id.image_src}.png"
        return product_image_url

    def sync_customers(self):
        return {
            'name': _('Sync Customers'),
            'view_mode': 'form',
            'res_model': 'woocommerce.update.wizard',
            'view_id': self.env.ref(
                'woocommerce_odoo_bridge.woocommerce_update_form_display').id,
            'type': 'ir.actions.act_window',
            'context': {'operation_type': 'customers',
                        'active_ids': self.ids},
            'target': 'current'
        }

    def unlink(self):
        for partner_id in self:
            if partner_id.type == 'contact':
                if partner_id.instance_id:
                    app = API(
                        url="" + partner_id.instance_id.store_url + "/index.php/",
                        # Your Website URL
                        consumer_key=partner_id.instance_id.consumer_key,
                        # Your consumer key
                        consumer_secret=partner_id.instance_id.consumer_secret,
                        # Your consumer secret
                        wp_api=True,  # Enable the WP REST API integration
                        version="wc/v3",  # WooCommerce WP REST API version
                        timeout=500,
                    )
                    app.delete(f"customers/{partner_id.woo_id}",
                                     params={"force": True}).json()

        super(ResPartnerHwe, self).unlink()

    # def woo_update(self,instance_id):
    #     for partner_id in self:
    #         if partner_id.type == 'contact':
    #             if instance_id:
    #                 if partner_id.email:
    #                     image_url = self.image_upload(partner_id)
    #                     name = partner_id.name.rsplit(' ', 1)
    #                     val_list = {
    #                         "first_name": name[0],
    #                         "last_name": name[1] if len(name) > 1 else "",
    #                         'email': partner_id.email if partner_id.email else "",
    #                         'role': 'customer',
    #                         'billing': {
    #                             "first_name": name[0],
    #                             "last_name": name[1] if len(name) > 1 else "",
    #                             "company": "",
    #                             "address_1": partner_id.street if partner_id.street else "",
    #                             "address_2": "",
    #                             "city": partner_id.city if partner_id.city else "",
    #                             "state": partner_id.state_id.code if partner_id.state_id else "",
    #                             "postcode": partner_id.zip if partner_id.zip else "",
    #                             "country": partner_id.country_id.code if partner_id.country_id else "",
    #                             "email": partner_id.email if partner_id.email else
    #                             partner_id.name.split()[0] + "@gmail.com",
    #                             "phone": partner_id.phone if partner_id.phone else ""
    #                         },
    #                         'shipping': {
    #                             "first_name": name[0],
    #                             "last_name": name[1] if len(name) > 1 else "",
    #                             "company": "",
    #                             "address_1": partner_id.street if partner_id.street else "",
    #                             "address_2": "",
    #                             "city": partner_id.city if partner_id.city else "",
    #                             "state": partner_id.state_id.code if partner_id.state_id else "",
    #                             "postcode": partner_id.zip if partner_id.zip else "",
    #                         },
    #                         "is_paying_customer": False,
    #                         "avatar_url": image_url,
    #                         "meta_data": [],
    #
    #                     }
    #                     if partner_id.instance_id:
    #                         app = API(
    #                             url="" + instance_id.store_url + "/index.php/",  # Your store URL
    #                             consumer_key=instance_id.consumer_key,  # Your consumer key
    #                             consumer_secret=instance_id.consumer_secret,  # Your consumer secret
    #                             wp_api=True,  # Enable the WP REST API integration
    #                             version="wc/v3",  # WooCommerce WP REST API version
    #                             timeout=500,
    #                         )
    #                         res = app.put(f"customers/{partner_id.woo_id}", val_list).json()
    #                         print(res)
    #                         if res.get('id'):
    #                             partner_id.write({
    #                                 'woo_id': res.get('id'),
    #                                 'instance_id': instance_id.id,
    #                                 'woo_user_name': res.get('username')
    #                             })
    #
    #                     else:
    #                         app = API(
    #                             url="" + instance_id.store_url + "/index.php/",
    #                             # Your store URL
    #                             consumer_key=instance_id.consumer_key,
    #                             # Your consumer key
    #                             consumer_secret=instance_id.consumer_secret,
    #                             # Your consumer secret
    #                             wp_api=True,  # Enable the WP REST API integration
    #                             version="wc/v3",  # WooCommerce WP REST API version
    #                             timeout=500,
    #                         )
    #                         res = app.post('customers', val_list).json()
    #                         if res.get('id'):
    #                             partner_id.write({
    #                                 'woo_id':res.get('id'),
    #                                 'instance_id':instance_id.id,
    #                                 'woo_user_name':res.get('username')
    #                             })

