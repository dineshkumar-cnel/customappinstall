/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component } from '@odoo/owl';


class DashBoard extends Component {
    static template = 'WooCommerceGraphs';

    constructor() {
        super(...arguments);
        this.dashboards_templates = ['WooCommerceDashboard', 'WooCommerceGraphs'];
        this.willStart();
    }

    async willStart() {
        console.log('Component is initializing...');
        await this.render_products(); // Render products on initialization
        await this.render_orders();
        await this.render_tile();
    }

    // Get Product Api
    async render_products() {
        console.log('Fetching product data...');
        try {
            const response = await fetch('/web/dataset/call_kw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),  // Adding CSRF Token if necessary
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        model: 'product.template',
                        method: 'get_product_graph_hwe',
                        args: [],
                        kwargs: {},
                    },
                    id: Math.floor(Math.random() * 1000)
                }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }

            const result = await response.json();
            console.log('Product data:', result);

            if (result && result.result) {
                const productData = result.result;
                this.populateProductTable_count(productData);
                this.populateProductTable(productData);
                this.updatePartnerCount(productData);
                this.mounted();
            } else {
                console.error('Invalid response structure:', result);
            }
        } catch (error) {
            console.error('Error fetching product data:', error);
        }
    }

     // Button click par notification show karna
     onImportDataClick = async () => {
        const response = await this._rpc({
            model: 'woo.wizard',
            method: 'get_woo_import',
        });

        if (response.status === 'success') {
            // Show success notification
            this.showNotification('Success', response.message, 'success');
        } else {
            // Show error notification
            this.showNotification('Error', response.message, 'danger');
        }
    };

     // Notification show karna
     showNotification(title, message, type) {
        const notificationManager = new NotificationManager(this.env);
        notificationManager.add(notificationManager.create({
            title,
            message,
            type, // 'success', 'danger', 'info'
        }));
    }

    updatePartnerCount(productData) {
        // Ensure productData and partners are properly initialized
        const partnerCount = productData && typeof productData.partners !== 'undefined' ? productData.partners : 0;

        // Update the DOM element with the partner count
        const partnerRightElement = document.getElementById('partner_right');
        if (partnerRightElement) {
            partnerRightElement.innerHTML = `<div class="count-container">${partnerCount}</div>`;
        } else {
            console.error('Element with ID partner_right not found.');
        }
    }

      // StartButton click handler for dynamic redirection
      redirectToMenu() {
        // Extract menu_id from the URL hash (after '#')
        const hashParams = new URLSearchParams(window.location.hash.slice(1));  // Remove the '#' symbol from the start
        let menuId = hashParams.get('menu_id');  // Get the menu_id from hash fragment
        let action = hashParams.get('action');  // Get the menu_id from hash fragment
    
        if (menuId && action) {
            // Convert menuId to a number, add 1, and use the new value
            menuId = parseInt(menuId, 10) + 1;  // Convert to integer and add 1
            
            action = parseInt(action, 10) - 2;
            // Construct the URL with the updated menuId and view_type=form
            const redirectUrl = `http://localhost:8069/web#menu_id=${menuId}&action=${action}&model=woo.commerce&view_type=form`;
    
            // Log the constructed URL in the console
            console.log('Redirecting to URL:', redirectUrl);
    
            // Redirect the browser to the new URL
            window.location.href = redirectUrl;
        } else {
            console.error('menu_id not found in the URL');
            console.log('Current URL:', window.location.href);
        }
    }
    
        // Start Sync Button click handler for dynamic redirection
        onViewProducts() {
            // Extract menu_id from the URL hash (after '#')
            const hashParams = new URLSearchParams(window.location.hash.slice(1));  // Remove the '#' symbol from the start
            let menuId = hashParams.get('menu_id');  // Get the menu_id from hash fragment
            let action = hashParams.get('action');
        
            if (menuId && action) {
                // Convert menuId to a number, add 1, and use the new value
                action = parseInt(action, 10) - 1;  // Convert to integer and add 1
                menuId = parseInt(menuId, 10) + 2;

                // Construct the URL with the updated menuId and view_type=form
                const redirectUrl = `http://localhost:8069/web#menu_id=${menuId}&action=${action}`;
                console.log('Redirecting to URL:', redirectUrl);
                // Redirect the browser to the new URL
                window.location.href = redirectUrl;
            } else {
                console.error('menu_id not found in the URL');
                console.log('Current URL:', window.location.href);
            }
        }
        
        

    populateProductTable_count(productData) {

        const product_right = document.getElementById('product_right');
        if (product_right) {
            // Clear existing content

            let counter = 0;
            console.log('Product data count:', productData);
            // Add rows for each product
            productData.forEach((item) => {
                counter++;
            });
            $('#product_right').html('<span>' + counter + '</span>');

        } else {
            console.warn('Product table element not found.');
        }
    }

    populateProductTable(productData) {

        const productTable = document.getElementById('product_body');
        if (productTable) {
            // Clear existing content

            let counter = 1;
            console.log('Product data2:', productData);
            // Add rows for each product
            productData.forEach((item) => {

                $('#product_table').append('<tr class="pr_tb_row" id="' + item.id + '"><td>' + item.id + '</td><td>' + item.name + '</td><td>' + item.quantity + '</td><td>' + item.price + '</td></tr>');
            });
        } else {
            console.warn('Product table element not found.');
        }
    }

    // Get Customer Count api 
    async render_tile() {
        console.log('Fetching tile details...');
    
        try {
            const response = await fetch('/web/dataset/call_kw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        model: 'sale.order',
                        method: 'get_tile_details',
                        args: [],
                        kwargs: {}
                    }
                })
            });
    
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
    
            const result = await response.json();
            console.log('Tile data:', result);
    
            // Check if the result object contains the data
            if (result.result) {
                // Extract data from the result object
                const data = result.result;
                const instanceCount = data.instance || 0;
                const productsCount = data.products || 0;
                const ordersCount = data.orders || 0;
                const customersCount = data.partners || 0;
    
                console.log('Extracted counts:', {
                    instanceCount,
                    productsCount,
                    ordersCount,
                    customersCount
                });
    
                // Update the DOM
                const updateElement = (selector, count) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.innerHTML = `<div class="count-container">${count}</div>`;
                        console.log(`Updated ${selector} with value: ${count}`);
                    } else {
                        console.warn(`Element with selector ${selector} not found.`);
                    }
                };
    
                updateElement('#partner_right', customersCount);
                updateElement('#product_right', productsCount);
                updateElement('#order_right', ordersCount);
                updateElement('#instance_right', instanceCount);
    
                // Function to show or hide an element
                function toggleElementVisibility(selector, isVisible) {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.style.display = isVisible ? 'block' : 'none';
                    } else {
                        console.warn(`Element with selector ${selector} not found.`);
                    }
                }
    
                // Toggle visibility of the "Start Sync" button based on product, Order And Customer count
                const startSyncButton = document.querySelector('#product_button');
                if (productsCount === 0 && ordersCount === 0 && customersCount=== 0) {
                    toggleElementVisibility('#product_button', true);  // Show button if productsCount is 0
                } else {
                    toggleElementVisibility('#product_button', false); // Hide button if productsCount > 0
                }
    
                // Example usage of other elements (based on instance count)
                if (instanceCount > 0) {
                    toggleElementVisibility('#instanceifnotzerocount', true); // Show instance data
                    toggleElementVisibility('#instanceifzerocount', false); // Hide instance zero count section
                } else {
                    toggleElementVisibility('#instanceifnotzerocount', false);
                    toggleElementVisibility('#instanceifzerocount', true);
                }
    
            } else {
                console.error('Result object does not contain the expected data:', result);
            }
    
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }
    

    /// Get Order Api 
    async render_orders() {
        console.log('Fetching Order data...');
        try {
            const response = await fetch('/web/dataset/call_kw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),  // Adding CSRF Token if necessary
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        model: 'sale.order',
                        method: 'get_orders',
                        args: [],
                        kwargs: {},
                    },
                    id: Math.floor(Math.random() * 1000)
                }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }

            const result = await response.json();
            console.log('Orders data:', result);

            // Check if the result is structured correctly
            if (result && result.result) {
                const orderData = result.result;
                this.populateOrderTable_count_hwe(orderData);
                this.populateOrderTable_hwe(orderData);

            } else {
                console.error('Invalid response structure:', result);
            }
        } catch (error) {
            console.error('Error fetching product data:', error);
        }
    }

    populateOrderTable_count_hwe(orderData) {
        const ordersTable = document.getElementById('order_right');
        if (ordersTable) {

            // Initialize counter for ID starting from 1
            let counter = 0;

            // Add rows for each product
            orderData.forEach((item) => {
                counter++;
            });
            $('#order_right').html('<span>' + counter + '</span>');
        } else {
            console.warn('Orders table element not found.');
        }
    }

    populateOrderTable_hwe(orderData) {
        const ordersTable = document.getElementById('orders_body');
        if (ordersTable) {

            // Initialize counter for ID starting from 1
            let counter = 1;

            // Add rows for each product
            orderData.forEach((item) => {

                $('#orders_body').append('<tr class="pr_tb_row" id="' + item.name + '"><td>' + item.name + '</td><td>' + item.date_order + '</td><td>' + item.customer + '</td><td>' + item.total + '</td><td>' + item.status + '</td></tr>');
            });
        } else {
            console.warn('Orders table element not found.');
        }
    }

    getCsrfToken() {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        } else {
            console.warn('CSRF token meta tag not found.');
            return '';
        }
    }

    tile_graphs() {
        const dataBar = {
            labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
            datasets: [{
                label: 'Customers',
                data: [5, 10, 15, 12, 10, 8, 6, 4],
                backgroundColor: ['#dee5ef', '#dee5ef', '#dee5ef', '#dee5ef', '#fc381d', '#dee5ef', '#dee5ef', '#dee5ef'],
                borderColor: ['#dee5ef', '#dee5ef', '#dee5ef', '#dee5ef', '#fc381d', '#dee5ef', '#dee5ef', '#dee5ef'],
                borderWidth: 1,
                fill: false
            }]
        };

        const optionsBar = {
            scales: {
                y: {
                    beginAtZero: true,
                    display: false,
                },
                x: {
                    beginAtZero: true,
                    display: false,
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            elements: {
                point: {
                    radius: 0
                }
            }
        };

        const ctxBar = document.getElementById("barChart");
        if (ctxBar) {
            new Chart(ctxBar, {
                type: 'bar',
                data: dataBar,
                options: optionsBar
            });
        }
    }

    // Orders and Products Search work Start

        mounted() {
            console.log('Component mounted.');
            this.setupEventListeners();
            this.tile_graphs(); // Initialize chart after component is mounted
        }
    
        setupEventListeners() {
            console.log('Setting up event listeners.');
    
            const productSearchInput = document.getElementById('product_search');
            const orderSearchInput = document.getElementById('order_search');
    
            if (productSearchInput) {
                console.log('Product search input found.');
                productSearchInput.addEventListener('keyup', (event) => {
                    this.onProductSearch(event);
                });
            } else {
                console.warn('Product search input not found.');
            }
    
            if (orderSearchInput) {
                console.log('Order search input found.');
                orderSearchInput.addEventListener('keyup', (event) => {
                    this.onOrderSearch(event);
                });
            } else {
                console.warn('Order search input not found.');
            }
        }
    
        ///// Serch Products
            onProductSearch(event) {
                if (event) event.preventDefault(); // Prevent form submission if necessary
                console.log('Product search initiated.');
    
                const inputElement = document.getElementById('product_search');
                if (!inputElement) {
                    console.error('Product search input element not found.');
                    return;
                }
    
                const input = inputElement.value.toLowerCase();
                console.log('Search input:', input);
    
                const rows = document.querySelectorAll('#product_table tbody tr');
                let hasVisibleRow = false; // Track if there's at least one visible row
                rows.forEach(row => {
                    const cells = row.getElementsByTagName('td');
                    const found = Array.from(cells).some(cell => cell.textContent.toLowerCase().includes(input));
                    row.style.display = found ? '' : 'none';
                    if (found) hasVisibleRow = true; // Mark as found if any row matches
                });
    
                // If no rows are found, show a blank row or message
                if (!hasVisibleRow) {
                    const noResultsRow = document.createElement('tr');
                    noResultsRow.innerHTML = '<td colspan="4" class="text-center">No results found</td>';
                    document.getElementById('product_body').appendChild(noResultsRow);
                } else {
                    // Clear any previous "No results found" message
                    const existingNoResultsRow = document.querySelector('#product_body tr.no-results');
                    if (existingNoResultsRow) {
                        existingNoResultsRow.remove();
                    }
                }
            }
    
        // Search orders
        onOrderSearch(event) {
            if (event) event.preventDefault(); // Prevent form submission if necessary
            console.log('Order search initiated.');
    
            const inputElement = document.getElementById('order_search');
            if (!inputElement) {
                console.error('Order search input element not found.');
                return;
            }
    
            const input = inputElement.value.toLowerCase();
            console.log('Search input:', input);
    
            const rows = document.querySelectorAll('#orders_table tbody tr');
            let hasVisibleRow = false; // Track if there's at least one visible row
            rows.forEach(row => {
                const cells = row.getElementsByTagName('td');
                const found = Array.from(cells).some(cell => cell.textContent.toLowerCase().includes(input));
                row.style.display = found ? '' : 'none';
                if (found) hasVisibleRow = true; // Mark as found if any row matches
            });
    
            // If no rows are found, show a blank row or message
            if (!hasVisibleRow) {
                const noResultsRow = document.createElement('tr');
                noResultsRow.innerHTML = '<td colspan="5" class="text-center">No results found</td>';
                document.getElementById('orders_body').appendChild(noResultsRow);
            } else {
                // Clear any previous "No results found" message
                const existingNoResultsRow = document.querySelector('#orders_body tr.no-results');
                if (existingNoResultsRow) {
                    existingNoResultsRow.remove();
                }
            }
        }
     // Orders and Products Search work End
     

// // JavaScript code for managing popup visibility and carousel
// document.addEventListener("DOMContentLoaded", function () {
//     var popupContainer = document.getElementById('popup');
//     var closeButton = document.getElementById('popup-close');
//     var carousel = document.querySelector('.owl-carousel'); // Owl carousel container

//     // Function to show popup
//     function showPopup() {
//         popupContainer.style.display = 'block'; // Show popup
//         carousel.style.display = 'none'; // Hide the carousel
//     }

//     // Function to hide popup
//     closeButton.addEventListener('click', function() {
//         popupContainer.style.display = 'none'; // Hide popup
//         carousel.style.display = 'block'; // Show carousel again
//     });

//     // Optionally, you can automatically show the popup when the page loads
//     // showPopup(); // Uncomment to show the popup by default when page loads
// });
}

registry.category('actions').add('woocommerce_dashboard_tag', DashBoard);
