# Mirinjapaingtong Valley — Resort Booking Website (Portfolio)

## Project Summary
A full-stack **Resort Booking Website** built as a **paid client project** for "Mirinjapaingtong Valley Resort" located in Lama, Bandarban, Bangladesh. The platform provides a complete online presence for the resort, enabling guests to browse rooms, check availability, and submit bookings — while giving the resort owner a powerful admin dashboard to manage every aspect of the business.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 (Vite), React Router v6, React Bootstrap, Axios |
| **Backend** | Node.js, Express.js |
| **Database** | MongoDB (Mongoose ODM) |
| **Authentication** | JWT (JSON Web Tokens), bcryptjs |
| **Media Uploads** | Cloudinary (images & video), Multer (memory storage) |
| **Email Service** | Nodemailer (Gmail SMTP) |
| **Validation** | Joi (server-side schema validation) |
| **Security** | Helmet (HTTP headers), express-rate-limit, CORS |
| **Charts & Calendar** | Chart.js + react-chartjs-2, react-calendar, react-datepicker |
| **PDF Generation** | jsPDF (booking receipts) |
| **Notifications** | react-hot-toast |
| **Icons** | React Icons, Font Awesome |
| **Deployment** | Vercel (frontend + backend as serverless functions) |

---

## System Architecture

```
┌─────────────────┐       REST API (Axios)       ┌─────────────────┐
│  React Frontend │  ──────────────────────────►  │  Express Backend │
│  (Vite, Vercel) │  ◄──────────────────────────  │  (Vercel Node)   │
└────────┬────────┘       JSON + JWT Auth         └────────┬────────┘
         │                                                  │
         │                                      ┌───────────┼───────────┐
         │                                      │           │           │
         ▼                                      ▼           ▼           ▼
   Client Browser                          MongoDB     Cloudinary   Gmail SMTP
   (SPA, React Router)                    (Atlas)     (Media CDN)  (Nodemailer)
```

- **Monorepo structure**: Separate `frontend/` and `backend/` directories, each independently deployed to Vercel.
- **RESTful API**: 16 route modules with 60+ endpoints, organized by resource.
- **Role-based access**: Two roles — `user` and `admin` — enforced by middleware chaining (`auth` → `admin`).
- **Serverless deployment**: Backend exported as a module (`module.exports = app`) for Vercel's `@vercel/node` runtime.

---

## Panels & Features

### 1. Public Website (Guest-Facing)

| Feature | Description |
|---|---|
| **Dynamic Home Page** | Hero carousel (admin-managed), featured rooms, facilities showcase, guest reviews slider, image gallery, Google Maps embed, live weather widget |
| **Room Browsing** | Multi-filter search (price range, guest capacity, facilities, features, check-in/out dates), server-side pagination |
| **Room Details** | Image carousel, full description, facilities & features tags, availability calendar (booked vs. available), guest reviews section, recommended rooms |
| **Booking Workflow** | Date picker with overlap validation, guest count inputs (adults/children), personal info form, mobile payment method selection (bKash/Nagad/Upai), pricing summary with advance payment calculation (50%), booking & cancellation policy display |
| **Availability Page** | Dedicated page to check room availability across all rooms with date filtering |
| **Menu & Packages** | Food items and packages with pricing, offers, and descriptions |
| **Facilities & Features** | Dedicated pages with image cards for resort facilities and room features |
| **Contact Page** | Contact form (saved as queries in DB), resort info, map |
| **About Page** | Resort history, mission, vision, team members, achievements — all admin-editable |
| **Reviews** | All guest reviews page with ratings |
| **Visitor Tracking** | IP-based geolocation tracking (ipify + ipapi), session-aware (counts once per day), stored per city/country/date |

---

### 2. User Panel (Authenticated Guests)

| Feature | Description |
|---|---|
| **Dashboard** | Booking statistics overview, recent bookings |
| **Profile Management** | Edit personal details (name, phone, address, PIN, DOB), change password, upload/change profile image via Cloudinary |
| **My Bookings** | View all bookings with status (pending/confirmed/cancelled), booking details modal, cancellation (only pending bookings within 24 hours), downloadable PDF receipts |
| **Wishlist** | Save/remove favorite rooms, toggle wishlist from room cards |

---

### 3. Admin Panel (Resort Owner)

| Feature | Description |
|---|---|
| **Dashboard** | Period-based analytics (today/week/month/90-days/year/all-time): rooms, bookings, revenue, users, queries, reviews — with detailed breakdowns (active/inactive rooms, confirmed/pending/cancelled bookings, paid/due amounts, verified/unverified users) |
| **Room Management** | Full CRUD, multi-image upload to Cloudinary, facility/feature assignment via ObjectId references, active/inactive toggle |
| **Booking Management** | View recent bookings (last 30 days) with search, status control (pending → confirmed → cancelled), payment update (paid/due amounts, payment date), availability auto-update on confirm/cancel, admin booking receipts |
| **Booking History** | All-time bookings with search and pagination |
| **User Management** | Paginated user list with search and role filter, activate/deactivate, verify/unverify, role change, admin-created users, registration insights (location, time) |
| **Facility Management** | CRUD for resort facilities with images |
| **Feature Management** | CRUD for room features with images |
| **Menu Management** | CRUD for food items and packages, categories (food/package), offer support with offer text |
| **Carousel Management** | CRUD for homepage carousel slides with captions, subtitles, CTA buttons, active/order control |
| **Content Management** | Edit explore section (gallery images, video, map, weather coordinates), edit about section (title, description, history, mission, vision, cover image), manage team members (CRUD), manage achievements (CRUD) |
| **Query Management** | View contact form submissions, mark as read, reply via email, delete |
| **Review Management** | View all reviews with pagination, mark as read, delete reviews (auto-recalculates room's average rating) |
| **Email Center** | Send individual, bulk (all users), or marketing emails with HTML content, email history with pagination, delete individual/all history |
| **Site Settings** | Branding (site name, description, logo), contact info, social media links, map embed, operating hours, check-in/out times, currency, tax rate, maintenance mode, booking pause toggle |
| **Visitor Analytics** | Period-based visitor statistics aggregated by city/country, total visit counts |
| **Real-time Badges** | Sidebar badges showing unread queries count, pending bookings count, unverified users count — auto-refreshed every 30 seconds |

---

## Email Notification System

Automated HTML emails sent at every critical point:
- **Registration**: Welcome email
- **Booking Submitted**: Full booking details + advance payment instructions
- **Booking Confirmed**: Confirmation with payment summary
- **Booking Cancelled**: Cancellation notice (admin or user-initiated)
- **Payment Updated**: Updated payment details
- **Password Reset**: Branded reset link with 1-hour expiry
- **Password Reset Confirmation**: Success notice with login link
- **Query Reply**: Admin reply to contact form submissions
- **Admin Emails**: Individual, bulk, and marketing communications

---

## Deployment

- **Frontend**: Vercel static site with SPA redirect (`vercel.json` rewrite)
- **Backend**: Vercel serverless function using `@vercel/node` with CORS headers configured for the production domain
- **Database**: MongoDB Atlas (cloud)
- **Media CDN**: Cloudinary
- **Environment Variables**: Managed via `.env` (MONGODB_URI, JWT_SECRET, Cloudinary keys, Email credentials, API URL)

---

## Professional Value

This is a **production-grade, paid client project** that handles real business operations. It combines:
- **Customer-facing booking convenience** with a smooth UX
- **Strong back-office operations** for the resort owner
- **End-to-end booking lifecycle** (browse → book → pay → confirm/cancel)
- **Real-time analytics** and visitor tracking
- **Complete content management** — the client can update every part of the website without code changes
- **Transactional email system** for professional communication
- **Security hardened** with JWT auth, rate limiting, input validation, and role-based access control
