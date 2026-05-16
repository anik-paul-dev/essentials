# BD-MarketPlace — Portfolio Project Overview

## Project Summary

**BD-MarketPlace** is a full-stack, city-based local e-commerce marketplace built for Bangladesh. It connects local buyers with sellers and shops across multiple cities, allowing users to browse, buy, sell, chat, and manage orders — all from a single platform. The platform features a **4-role RBAC (Role-Based Access Control)** system with 5 distinct panels: Public Storefront, User Panel, Shop Panel, Admin Panel (city-scoped), and SuperAdmin Panel (global control).

> **Type:** Client Project (Paid)  
> **Role:** Solo Full-Stack Developer — designed, developed, and deployed independently  
> **Stack:** MERN (MongoDB, Express.js, React, Node.js)  
> **Deployment:** Vercel (Frontend SPA + Backend Serverless Functions)

---

## Tech Stack & Dependencies

### Backend (Node.js / Express)
| Technology | Purpose |
|---|---|
| **Express.js** | RESTful API framework |
| **MongoDB + Mongoose** | NoSQL database with ODM |
| **JWT (jsonwebtoken)** | Stateless authentication tokens |
| **bcryptjs** | Password hashing (salt rounds: 10) |
| **Passport.js + Google OAuth 2.0** | Social login via Google |
| **Stripe** | International card payment processing (BDT currency) |
| **Cloudinary + Multer** | Cloud image upload, storage, auto-optimization |
| **Socket.IO** | Real-time WebSocket for chat & notifications |
| **Nodemailer** | Transactional email via SMTP |
| **PDFKit** | Server-side PDF invoice generation |
| **Helmet** | HTTP security headers |
| **express-rate-limit** | API rate limiting (DDoS protection) |
| **cookie-parser** | HTTP-only cookie management |
| **nanoid** | Collision-resistant public ID generation |
| **cors** | Cross-origin resource sharing |

### Frontend (React)
| Technology | Purpose |
|---|---|
| **React 18** | Component-based SPA UI |
| **React Router v6** | Client-side routing with nested routes |
| **Axios** | HTTP client with interceptors |
| **Bootstrap 5** | Responsive grid & utility classes |
| **Socket.IO Client** | Real-time WebSocket client |
| **React Toastify** | Toast notification system |
| **React Icons (Feather)** | Consistent icon library |
| **js-cookie** | Client-side cookie management |
| **@react-oauth/google** | Google OAuth frontend integration |

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT (React SPA)                │
│  Vercel Static Hosting + SPA Fallback Routing       │
│  Context API (Auth + Socket) → Hooks → Components   │
└────────────────────────┬────────────────────────────┘
                         │ RESTful API (Axios + JWT)
                         │ WebSocket (Socket.IO)
┌────────────────────────▼────────────────────────────┐
│               SERVER (Express.js API)               │
│  Vercel Serverless Functions (@vercel/node)          │
│  Middleware Pipeline → Routes → Controllers → DB    │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼──────┐
  │MongoDB │ │Cloudinary│ │Stripe │ │Nodemailer│
  │ Atlas  │ │  (CDN)  │ │(Pay)  │ │  (SMTP)  │
  └────────┘ └────────┘  └───────┘ └──────────┘
```

- **Monorepo Structure:** `/client` (React SPA) + `/server` (Express API) in one repo
- **Dual Entry Points:** `server.js` (local dev with Socket.IO + HTTP server) and `api/index.js` (Vercel serverless — exports Express app)
- **Real-time Dual Mode:** Socket.IO for localhost, automatic polling fallback for Vercel serverless (where persistent WebSocket connections aren't supported)

---

## All Panels & Features

### 1. Public Storefront (No Login Required)
| Feature | Description |
|---|---|
| **Homepage** | Hero section, city selector, category browser, trending & latest products |
| **Product Listing** | Full-text search, filter by category/subcategory/city/price, sort (price, rating, popular, newest) |
| **Product Detail** | Image gallery, seller info, reviews & ratings, add to cart, contact seller (chat) |
| **Cart** | LocalStorage-based cart, quantity management, cart badge in navbar |
| **Checkout** | Shipping address form, 5 payment methods (COD, Stripe, bKash, Nagad, Rocket) |
| **Guest Checkout** | Allows ordering without login — stores guest name/email/phone |
| **Public Profiles** | View seller/shop profiles with their product listings |
| **Category Browse** | Dynamic categories with images and subcategories |
| **Wishlist** | Save products to wishlist (login required) |
| **Cookie Consent** | GDPR-style cookie consent banner |
| **Policies** | Dynamic About Us, Privacy Policy, Terms & Conditions, Refund Policy, Cookie Policy — all managed from SuperAdmin |
| **Password Reset** | Email-based forgot/reset password with secure hashed tokens |
| **Google Login** | One-click OAuth login/register via Google |

### 2. User Panel (`/user/*`)
| Feature | Description |
|---|---|
| **Dashboard** | Overview of account activity |
| **My Orders** | View purchase history with order status tracking, PDF invoice download |
| **Sell Product** | Users can list products for sale (C2C marketplace model) — pending admin approval |
| **Seller Orders** | View and manage orders received as a seller, update order status, update payment status for COD |
| **Profile Management** | Update name, phone, address, avatar upload to Cloudinary |
| **Change Password** | Secure password change with current password verification |
| **Wishlist** | View and manage saved products |

### 3. Shop Panel (`/shop/*`)
| Feature | Description |
|---|---|
| **Dashboard** | Revenue stats (total/today), order counts, status breakdown chart |
| **Product Management** | Full CRUD — create with multi-image upload, edit, delete, image management |
| **Order Management** | View incoming orders, update order status (pending → confirmed → processing → shipped → delivered), update COD payment status |
| **Shop Profile** | Edit shop name, description, logo, banner, contact info |
| **Statistics** | Aggregated sales analytics with MongoDB aggregation pipeline |

### 4. Admin Panel (`/admin/*`) — City-Scoped
| Feature | Description |
|---|---|
| **Separate Login** | Dedicated admin login endpoint (`/auth/admin/login`) |
| **Dashboard** | City-scoped statistics — users, shops, products, orders, revenue (total/today), order status breakdown, recent orders |
| **User Management** | View/search users in assigned city, activate/deactivate accounts |
| **Shop Management** | View/search shops in assigned city |
| **Product Moderation** | Approve/reject products, view pending products, delete products |
| **Order Management** | View all orders in assigned city, filter by status |
| **Category Management** | CRUD categories with image upload and subcategories |

> **Key Design:** Each admin is assigned to a specific city. All dashboard data and management capabilities are scoped to that city only.

### 5. SuperAdmin Panel (`/superadmin/*`) — Global
| Feature | Description |
|---|---|
| **Separate Login** | Dedicated superadmin login endpoint |
| **Global Dashboard** | Platform-wide statistics — all users/shops/admins/products/orders, total & today's revenue, order status breakdown, **city-wise analytics** (orders, shops, products, revenue per city) |
| **Admin Management** | Full CRUD for admin accounts — create admins with assigned cities, edit, delete, activate/deactivate |
| **User Management** | Global user management across all cities |
| **Shop Management** | Global shop management across all cities |
| **Product Moderation** | Global product approve/reject/delete |
| **Order Management** | Global order view with city and status filters |
| **Category Management** | CRUD categories (shared across all cities) |
| **Site Settings** | Full CMS control — site name, tagline, logo upload, hero banners (add/remove with image), contact info, social links, delivery charges (inside/outside city), min order amount, guest checkout toggle, maintenance mode, featured categories |
| **Policy Management** | Edit About Us, Privacy Policy, Terms & Conditions, Refund Policy, Cookie Policy (rendered on public `/policies` page) |

---

## Real-Time Features
- **Live Chat:** One-to-one buyer-seller messaging via Socket.IO with typing indicators, unread count badges, and auto-scroll
- **Push Notifications:** Real-time notifications for new orders, order status changes, product approvals, payment confirmations — delivered via Socket.IO events
- **Polling Fallback:** Automatic HTTP polling (1.5s interval) when Socket.IO is unavailable (Vercel serverless), with `CustomEvent` dispatch for UI reactivity
- **Notification Bell:** Navbar bell icon with unread count badge, dropdown with mark-all-read

---

## Payment Integration
| Method | Implementation |
|---|---|
| **Cash on Delivery (COD)** | Order created with `pending` payment, seller marks as `paid` upon delivery |
| **Stripe** | `PaymentIntent` API — creates intent on server, confirms after client-side payment |
| **bKash / Nagad / Rocket** | Mobile payment with transaction ID verification (demo mode) |

---

## Email System
- **Welcome Email** on registration
- **Order Confirmation** email to buyer (styled HTML template with order details table, shipping address, payment method)
- **New Order Notification** email to seller(s)
- **Order Status Update** email to buyer
- **Payment Confirmation** email to buyer
- **Password Reset** email with secure token link (30-minute expiry)
- **Account Activation/Deactivation** email
- All emails use professional HTML templates with branded styling

---

## Security Features
| Feature | Implementation |
|---|---|
| **Password Hashing** | bcryptjs with 10 salt rounds (Mongoose pre-save hook) |
| **JWT Authentication** | Stateless tokens with 7-day expiry, stored in HTTP-only cookies + localStorage dual strategy |
| **CORS** | Configured origin whitelist with credentials support |
| **Helmet** | Security HTTP headers (XSS, clickjacking, MIME sniffing protection) |
| **Rate Limiting** | 3-tier: General (200/15min), Auth (20/15min), Upload (30/15min) |
| **Role-Based Access** | `authorize()` middleware checks `req.user.role` against allowed roles |
| **Account Status Check** | `isActive` flag checked on every authenticated request — deactivated accounts blocked |
| **Public IDs** | MongoDB `_id` never exposed to clients — nanoid-generated `publicId` used instead |
| **Token Expiry Handling** | Separate error codes for expired vs. invalid tokens |
| **Password Reset Tokens** | Cryptographically random, SHA-256 hashed, 30-minute TTL |

---

## PDF Invoice Generation
- Server-side PDF generation using **PDFKit**
- Styled invoice with branded header, order details table, customer/shipping info, payment summary
- Authorization check — only buyer, seller, or admin can download
- Streamed directly to client via `res.pipe()` for memory efficiency

---

## Deployment Architecture
| Component | Platform |
|---|---|
| **Frontend** | Vercel (Static SPA with client-side routing fallback) |
| **Backend** | Vercel Serverless Functions (Express app exported as module) |
| **Database** | MongoDB Atlas (Cloud) |
| **Images** | Cloudinary CDN (auto-optimized, width-limited to 800px) |
| **Email** | SMTP via Nodemailer |

---

## Summary for Resume/Portfolio

> **BD-MarketPlace** — A full-stack MERN e-commerce marketplace for Bangladesh featuring 4-role RBAC (User, Shop, Admin, SuperAdmin), city-scoped admin management, real-time chat & notifications (Socket.IO + polling fallback), multi-payment integration (Stripe, bKash, Nagad, Rocket, COD), Google OAuth, Cloudinary image management, PDF invoices, transactional emails, and a complete CMS for site settings — deployed on Vercel as serverless functions with MongoDB Atlas.
