# BD-Bazar: Full-Featured E-Commerce Platform

**BD-Bazar** is a comprehensive, multi-vendor e-commerce platform built to handle complex user journeys, scalable product management, and secure order processing. Developed with performance, security, and user experience in mind, this application serves as a robust foundation for modern digital marketplaces.

## 🛠️ Technology Stack
* **Backend:** Laravel 10 (PHP 8.1+), MySQL
* **Frontend:** Laravel Blade, Tailwind CSS, Vite
* **Integrations:** Stripe (Payments), Cloudinary (Media Storage), DomPDF (Invoice Generation)
* **Architecture:** MVC (Model-View-Controller) with Service-oriented patterns.

## 🚀 Key Features

* **Multi-Role Access Control (RBAC):** Distinct access levels and dashboards for Guests, Registered Users, Vendors (Admins), and System Owners (Superadmins).
* **Guest Checkout & Session Migration:** Allows guests to add items to cart, wishlist, and even checkout seamlessly. Upon registration or login, all guest session data (cart, wishlist, orders) automatically migrates to their permanent account.
* **ID Obfuscation:** Implements a security layer that encodes sequential database IDs into secure public IDs (e.g., `base_convert` logic), preventing scraping and enumeration attacks.
* **Intelligent Caching:** Utilizes a custom `CacheService` to handle aggressive caching of product catalogs, automatically invalidating when products are updated or deleted.
* **Multi-Gateway Payment System:** Supports Cash on Delivery (COD), Stripe (Credit/Debit), bKash, and Nagad.
* **Dynamic Invoicing:** Automated PDF invoice generation upon order confirmation and delivery.

## 🎛️ System Panels

### 1. User/Guest Panel (Storefront)
* **Dynamic Storefront:** Browse products by categories, search, and filter.
* **Shopping Cart & Wishlist:** Real-time updates, completely functional for non-logged-in users.
* **Checkout & Order Tracking:** Secure checkout process with multiple payment options and real-time status tracking (Pending, Confirmed, Processing, Shipped, Delivered).
* **User Profile:** Manage shipping addresses, view past orders, and download invoices.

### 2. Vendor (Admin) Panel
* **Product Management:** Full CRUD capabilities for products including multiple image uploads (via Cloudinary), stock tracking, and discount configurations.
* **Order Fulfillment:** Vendors can track orders, update order statuses, and process shipping.
* **Analytics Dashboard:** Real-time statistics on total orders, revenue, and low-stock alerts.

### 3. Superadmin Panel
* **Complete System Oversight:** Global dashboard with aggregate analytics across all vendors and users.
* **Admin & User Management:** Ability to create/suspend vendors and manage customer accounts.
* **Global Settings:** Manage dynamic site settings, delivery fees, and contact queries.
* **Category Management:** Build and manage the multi-level category hierarchy.
