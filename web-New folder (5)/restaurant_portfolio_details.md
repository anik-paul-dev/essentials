# Foodie-Spot (Restaurant Food Ordering Website)

**Project Type:** Full-Stack Web Application  
**Role:** Full-Stack Developer  

## Overview
Foodie-Spot is a comprehensive, full-featured restaurant food ordering and management platform. It provides a seamless customer experience for browsing menus, adding items to a cart, and placing orders. Simultaneously, it offers a robust Admin Panel for restaurant owners to manage categories, menu items, order statuses, and user interactions.

## Key Features

### Customer Panel
- **Landing & Menu Pages:** Engaging hero banner, featured categories, and a dynamic menu page to browse and search for food items.
- **Session-Based Cart System:** Real-time cart management allowing users to add, update, and remove items without losing their state.
- **Secure Checkout & Ordering:** A streamlined checkout form capturing delivery details and generating order summaries.
- **Order History & Tracking:** Dedicated dashboard for customers to view past orders, track current order status, and download order receipts as PDFs.
- **Authentication:** Complete user registration, login, logout, and password reset functionalities.
- **Real-Time Chat & Notifications:** Live chat support and notification system to keep users informed about their orders.
- **Profile Management:** Users can update their profile information, password, and profile image.

### Admin Panel (Role-Based Access Control)
- **Interactive Dashboard:** High-level overview of total orders, revenue, pending orders, and recent activities.
- **Menu & Category Management (CRUD):** Complete control over adding, editing, and deleting food categories and menu items with image uploads.
- **Order Management:** View all incoming orders, update their status (Pending, Confirmed, Preparing, Delivered, Cancelled), and download order PDFs.
- **User Management:** View registered users, toggle user status, and manage platform access.
- **Admin Chat Management:** Engage with customers via chat, with capabilities to manage chat histories.
- **Site Settings:** Update global configurations like delivery fees directly from the admin panel.

## Technology Stack
- **Backend:** PHP, Laravel 11, Eloquent ORM
- **Database:** MySQL
- **Frontend:** HTML, Vanilla CSS, Tailwind CSS, JavaScript (Vanilla/jQuery for AJAX), Blade Templating
- **Tools & Libraries:** Vite (asset bundling), Barryvdh DomPDF (invoice generation), concurrent tasks handling
- **Architecture:** MVC (Model-View-Controller) Architecture

## UI / UX Design Highlights
- **Aesthetics:** Dark/warm color scheme with food-themed gradients and glassmorphism cards.
- **Interactivity:** Smooth hover micro-animations and intuitive navigation transitions.
- **Responsiveness:** Fully responsive layout optimized for desktop, tablet, and mobile viewing.
