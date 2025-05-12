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

# models/woo_order_coupons.py
from odoo import models, fields

class WooCommerceOrderCouponsHwe(models.Model):
    _name = 'woo.order.coupons'
    _description = 'Woo Order Coupons'

    name = fields.Char(string='Coupon Name')
    # other fields...

# models/woo_wizard.py
from odoo import models, fields

class WooComerceWizardHwe(models.TransientModel):
    _name = 'woo.wizard'
    _description = 'Woo Wizard'

    name = fields.Char(string='Wizard Name')
    # other fields...

# models/woocommerce_update_wizard.py
from odoo import models, fields

class WooCommerceUpdateWizardHwe(models.TransientModel):
    _name = 'woocommerce.update.wizard'
    _description = 'WooCommerce Update Wizard'

    name = fields.Char(string='Update Wizard Name')
    # other fields...
