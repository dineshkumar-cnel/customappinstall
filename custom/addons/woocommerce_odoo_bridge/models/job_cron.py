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
from odoo import fields, models, api
import logging
from woocommerce import API
import ast
from odoo.addons.website.tools import text_from_html
import time
import json
from odoo.tools.safe_eval import const_eval



_logger = logging.getLogger(__name__)


class CronJobHwe(models.Model):
    """ Class for recording jobs to be done to sync woocommerce and odoo

        Methods:
            _do_job(self):cron function to perform job  created in specific
            interval
    """
    _name = 'job.cron'
    _description = 'Cron job '
    _rec_name = "function"

    instance_id = fields.Many2one('woo.commerce', string='Connection',
                                  help="Instance Id on which have to "
                                       "sync the record")
    function = fields.Char(string="Role", help="Role to be performed")
    data = fields.Json(string="Data", help="Data, arguments for the Role")
    state = fields.Selection([('pending', 'Pending'),('process', 'Processing'), ('done', 'Success'), ('fail', 'Failed')],
                             string='Status', default='pending', readonly=True,
                             help="Status of record")
    description = fields.Text(string="Message Log", readonly=True)


    function_type = fields.Selection(
        [('import', 'Import'), ('export', 'Export'), ('sync', 'Sync')],
        string='Type', default='import', readonly=True,
        help="Type of function")

    @api.model
    def _do_job(self):
        """method to do cron jobs for exporting and importing data."""
        job = self.env['job.cron'].sudo().search([('state', '=', 'pending')],
                                                 order='id asc', limit=1)
        if job:
            try:
                model = self.get_wizard(job.instance_id)
                if hasattr(model, '%s' % job.function):
                    try:
                        getattr(model, '%s' % job.function)(job.data)
                        job.state = "done"
                        job.description = "Task completed successfully!"
                    except Exception as e:
                        job.state = "fail"
                        job.description = 'Could not complete the task due to the error: %s'% e
                else:
                    job.state = "fail"
                    job.description = "Task failed due to the error: Given function is missing."

            except Exception as e:
                job.state = "fail"
                job.description = "Task failed due to the error: %s" % e
                _logger.error(
                    "Task failed due to the error: %s" % e)


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
        wizard = self.env['woo.wizard'].with_context({'default_name': instance_id.name,
                        'default_consumer_key': instance_id.consumer_key,
                        'default_consumer_secret': instance_id.consumer_secret,
                        'default_store_url': instance_id.store_url,
                        # 'default_api_key': instance_id.api_key,
                        'default_currency': instance_id.currency,
                        'default_company': instance_id.company_specific,
                        'active_id': instance_id.id
                        }).create({})
        return wizard

