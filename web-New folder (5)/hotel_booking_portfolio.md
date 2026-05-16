# Project Name: Hotel Booking (AP-Hotel)

## 📌 Project Overview
**Hotel Booking** is a comprehensive, full-featured Hotel Booking and Management System built to handle real-time room reservations, user management, and dynamic hotel configurations. It provides a seamless user experience for guests to explore rooms, book stays, and manage their reservations, while offering administrators a powerful dashboard to control every aspect of the hotel's operations, from room inventory to user queries and site settings.

## 🚀 Tech Stack & Architecture
- **Backend Framework:** Laravel 12.0 (PHP 8.2+)
- **Frontend Technologies:** Blade Templating, Tailwind CSS, Bootstrap, jQuery, Vite
- **Database:** MySQL (Eloquent ORM)
- **Cloud Storage:** Cloudinary (for scalable and fast image hosting)
- **PDF Generation:** DOMPDF (for booking invoices and records)
- **Architecture:** MVC (Model-View-Controller) Architecture

## ✨ Key Features & Panels

### 1. Public Interface (Guest View)
- **Dynamic Home Page:** Features dynamic carousels, highlighted rooms, and hotel amenities.
- **Room Browsing & Details:** Detailed views of available rooms with their specific features, facilities, and image galleries.
- **Review System:** Guests can read authentic reviews left by previous users.
- **Contact & Queries:** A built-in contact form allowing guests to send direct inquiries to the administration.
- **Responsive Design:** Optimized for mobile, tablet, and desktop viewing.

### 2. User Panel (Authenticated Guests)
- **Secure Authentication:** Registration, Login, Password Recovery, and Reset functionality.
- **Profile Management:** Users can update their personal information and securely change their passwords.
- **Booking Management:** 
  - Real-time room booking with availability checks.
  - View current and past booking histories.
  - Option to cancel active bookings.
  - Downloadable PDF invoices for bookings.
- **Review Submission:** Users can leave reviews for rooms they have successfully booked and stayed in.

### 3. Admin Panel (Hotel Management)
- **Comprehensive Dashboard:** An overview of the hotel's performance, recent bookings, and active queries.
- **Booking Management:** 
  - View new bookings and assign rooms.
  - Cancel or manage booking statuses.
  - Access complete booking records and generate PDF reports.
- **User Management:** View all registered users, verify user accounts (individual or bulk), and toggle user access (block/unblock).
- **Room & Inventory Control:** CRUD operations for Rooms. Set pricing, capacity, descriptions, and upload multiple images (stored via Cloudinary).
- **Features & Facilities:** Dynamically manage hotel-wide facilities and room-specific features.
- **Query & Review Moderation:** Read, manage, and delete user messages and reviews. Mark items as read to keep track of pending tasks.
- **Website Configuration & Settings:**
  - **General Settings:** Update site title, about us text, and general information.
  - **Shutdown Mode:** Ability to temporarily shut down bookings or the public site for maintenance.
  - **Team & Carousel:** Manage frontend carousel images and team member profiles.
  - **Contact & Socials:** Dynamically update hotel contact details and social media links.
