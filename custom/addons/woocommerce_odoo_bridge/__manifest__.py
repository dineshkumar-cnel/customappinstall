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
{
    'name': 'WooCommerce Odoo Bridge',
    'version': '17.0',
    'summary': 'WooCommerce Odoo Bridge V17',
    'sequence': 4,
    'description': 'WooCommerce Odoo Bridge for Odoo 17, integrating WooCommerce with Odoo for seamless data synchronization.',
    'category': 'Ecommerce',
    'author': 'CnEL India',
    'maintainer': 'CnEL India',
    'company': 'CnEL India',
    'website': 'https://cnelindia.com',
    'depends': [
        'base',
        'stock',
        'website_sale',
        'sale_management',
        'account',
        'sale_stock',
    ],
    'data': [
        'data/data.xml',
        'data/delivery_data.xml',
        'data/res_partner.xml',
        'data/product_template.xml',
        'data/sync_selected_records.xml',
        'data/schedule_action.xml',
        'security/ir.model.access.csv',
        'views/woo_commerce.xml',
        'views/product_product.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/account_tax.xml',
        'views/product_category.xml',
        'views/product_attribute.xml',
        'views/job_cron.xml',
        'wizard/update_records.xml',
        'wizard/woo_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'woocommerce_odoo_bridge/static/src/css/dashboard.css',
            'woocommerce_odoo_bridge/static/src/js/lib/Chart.bundle.js',
            'woocommerce_odoo_bridge/static/src/js/dashboard.js',
            'woocommerce_odoo_bridge/static/src/xml/dashboard.xml',
        ],
    },
    'images': ['static/description/banner.gif'],
    "external_dependencies": {"python": ["WooCommerce", "numpy"]},
    'license': 'OPL-1',
    'price': 143.41,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
}


