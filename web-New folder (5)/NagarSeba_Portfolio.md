# NagarSeba - Civic Infrastructure Complaint & Resolution Platform

**NagarSeba** is a comprehensive, real-time civic issue reporting and management platform designed to connect citizens, local authorities, and contractors. It bridges the gap between public grievances and administrative action by offering structured reporting, transparent tracking, automated SLA escalations, and micro-tender bidding.

## 🚀 Key Features

### For Citizens
*   **Geotagged Issue Reporting:** Report civic issues (e.g., road damage, waterlogging) with a map pin, photos, and auto-categorization.
*   **Voice-to-Text (Bangla & English):** Browser-native speech recognition for easy and fast reporting, especially for low-literacy users.
*   **AI Issue Categorizer:** Integration with Google Gemini API to automatically suggest categories, urgency levels, and appropriate departments based on the issue description.
*   **Real-Time Status Tracking:** Live updates on ticket status via Socket.IO, Push Notifications (Firebase FCM), and Email (Resend).
*   **Community Upvoting & Duplicate Detection:** Prevent redundant reports through MongoDB `$near` geospatial queries and allow citizens to upvote existing issues.
*   **Anonymous Safe Reporting:** Submit sensitive reports (like illegal construction) securely, with AES-encrypted identity storage.

### For Authorities & Admins
*   **Authority Dashboard:** Dedicated inbox sorted by SLA deadlines and community priority, equipped with live SLA countdown timers.
*   **Automated SLA Escalation:** Node-cron background jobs automatically track and escalate overdue tickets.
*   **Micro-Tender Module:** Authorities can post local micro-tenders directly from an issue ticket for local contractors to bid on.
*   **Trend Analytics Dashboard:** Admin panel powered by Chart.js, visualising monthly trends, worst-performing wards, and category breakdowns. Cached via Upstash Redis.
*   **Open Data API & Webhooks:** Public REST API endpoints and NGO webhook subscriptions to foster transparency and allow third-party monitoring.

## 🛠️ Technology Stack
*   **Frontend:** React 18, Vite, React Router v6, Bootstrap 5, Leaflet.js, Chart.js, Socket.IO Client.
*   **Backend:** Node.js, Express.js, Socket.IO, node-cron.
*   **Database & Caching:** MongoDB Atlas (with GeoJSON support), Mongoose, Upstash Redis.
*   **Authentication:** Custom JWT Auth (Access & Refresh tokens).
*   **Third-Party Services:** Cloudinary (Image storage/compression), Firebase FCM (Push Notifications), Resend (Email), Google Gemini API (AI categorization).
*   **Deployment:** Vercel (Frontend & Serverless Backend).

## 🏗️ System Architecture Highlights
*   **Microservice-like Decoupling via Events:** Heavy tasks (emails, push notifications, webhooks) are triggered asynchronously to keep the main API fast.
*   **Optimized Performance:** Aggressive code-splitting in React (`Suspense`/`lazy`), Upstash Redis caching for high-traffic public pages (like the heatmap), and Cloudinary on-the-fly image compression.
*   **Security & RBAC:** Strict Role-Based Access Control protecting routes for Citizens, Authorities, Contractors, and Admins.
