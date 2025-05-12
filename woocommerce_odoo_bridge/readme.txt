===============================
Module Name: WooCommerce Odoo Bridge
===============================

Overview
--------
The WooCommerce Odoo Bridge module provides seamless integration between WooCommerce and Odoo. 
It enables manual synchronization of products, customers, and orders between WooCommerce and Odoo through user-friendly "Export Data To WooCommerce" and "Import Data From WooCommerce" buttons, ensuring data consistency.

Features
--------
- **Manual Sync**: Sync data on-demand using "Export Data To WooCommerce" and "Import Data From WooCommerce" buttons.
- **Product Sync**: Import/export products between WooCommerce and Odoo with details such as name, price, inventory, and images.
- **Customer Sync**: Sync customer data manually with WooCommerce and Odoo.
- **Order Management**: Import WooCommerce orders into Odoo or update order statuses in WooCommerce via manual actions.
- **Error Reporting**: Provides logs and notifications for sync errors or conflicts.

Installation
------------
1. Download the `WooCommerce Odoo Bridge` module and place it in your Odoo addons directory.
2. Restart the Odoo server.
3. Go to the Apps menu in the Odoo backend and update the apps list.
4. Search for "WooCommerce Odoo Bridge" and install it.
5. Install the WooCommerce connector plugin in your WooCommerce store (if required).

Configuration
-------------
1. Go to **WooCommerce Odoo Bridge > Settings** in Odoo.
2. Enter your WooCommerce API credentials (Consumer Key and Secret) and the WooCommerce store URL.
3. Configure the default settings for:
   - Product category mapping
   - Customer group mapping
   - Tax and payment method mapping
4. Test the connection to ensure the integration is properly set up.

Usage
-----
1. **Manual Sync via Buttons**:
   - Navigate to **WooCommerce Odoo Bridge > Sync**.
   - Use the "Import Data From WooCommerce" button to pull data (products, customers, or orders) from WooCommerce into Odoo.
   - Use the "Export Data To WooCommerce" button to push data from Odoo to WooCommerce.

2. **Product Sync**:
   - Go to **WooCommerce Odoo Bridge > Products**.
   - Use the "Export Data To WooCommerce" button to send products to WooCommerce or "Import Data From WooCommerce" to fetch products from WooCommerce.

3. **Customer Sync**:
   - Navigate to **WooCommerce Odoo Bridge > Customers**.
   - Perform synchronization by clicking "Export Data To WooCommerce" or "Import Data From WooCommerce."

4. **Order Management**:
   - Access **WooCommerce Odoo Bridge > Orders**.
   - Use the buttons to import WooCommerce orders or export updated order statuses to WooCommerce.

5. **Logs and Reports**:
   - View synchronization logs under **WooCommerce Odoo Bridge > Logs** for details on successful actions or errors.

Screenshots
-----------
| WooCommerce Odoo Bridge Sync Page:
.. image:: static/description/sync_page.png
   :width: 80%
   :align: center

| Product Sync Example:
.. image:: static/description/product_sync.png
   :width: 80%
   :align: center

| Customer Sync Example:
.. image:: static/description/customer_sync.png
   :width: 80%
   :align: center

Support
-------
If you encounter any issues or have questions about the module, please contact us:
- Email: info@cnelindia.com
- Website: https://cnelindia.com/
- Phone: +91 9983345001

License
-------
This module is licensed under the LGPL-3 license.

FAQs
----
**1. How does manual synchronization work?**  
Manual synchronization requires the user to navigate to the sync page and click the "Export Data To WooCommerce" or "Import Data From WooCommerce" button to trigger data transfer.

**2. Can I still schedule automatic synchronization?**  
This version of the module currently supports manual synchronization only. For automated syncing, contact our support team.

**3. What data can be synchronized?**  
The module supports syncing of products, customers, and orders.

**4. How do I handle sync errors?**  
Sync errors are logged in the module. Navigate to **WooCommerce Odoo Bridge > Logs** to review error details and take necessary actions.