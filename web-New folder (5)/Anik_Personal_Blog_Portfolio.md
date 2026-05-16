# Anik Personal Blog - Portfolio Details

## Project Overview
**Anik Personal Blog** is a dynamic, full-stack web application designed to serve as a comprehensive personal portfolio and blogging platform. It allows the owner to showcase projects, publish blog posts, and share professional details seamlessly. Built with a modern tech stack (MERN + Vite + Firebase), it ensures a robust, secure, and highly interactive user experience.

## Live Technologies Used
- **Frontend:** React.js (Vite), React Router DOM, Context API, CSS3 (Themeable), Firebase Auth, Vercel Analytics.
- **Backend:** Node.js, Express.js.
- **Database:** MongoDB Atlas (Mongoose ORM).
- **Cloud Services:** Cloudinary (for Media/Image hosting), Firebase (for Authentication).
- **Security & Utilities:** JWT Verification (Firebase Admin SDK), Nodemailer (Email Notifications), Multer (Memory Storage), Sanitize-HTML (XSS Prevention), UAParser & IP-API (Device & Location tracking).

## Key Features & Core Capabilities

### 1. Advanced Administrative Control (Admin Panel)
- **Role-Based Access Control:** Differentiates between a 'Super Admin' and standard 'Admin Users'. New admin registrations undergo a strict approval workflow (Pending → Approved/Rejected).
- **Security & Monitoring:** Tracks IP addresses, geographical locations, devices, and browsers for every login attempt.
- **Rate Limiting & Blocking:** Implements automated account lockouts (15 minutes) after excessive login attempts to prevent brute-force attacks.
- **Real-Time Notifications:** Super Admin receives email alerts for new registrations, logins from unrecognized devices/locations, and blocked attempts.
- **Content Management System (CMS):** Full CRUD operations for Blogs, Projects, Profile, and About sections with integrated Cloudinary media uploads.
- **Analytics Dashboard:** Visualizes website traffic, blog/project views, likes, shares, and comments.

### 2. Interactive User Experience (User Panel)
- **Dynamic Content Consumption:** Users can seamlessly browse blogs and projects, filtered by categories, tags, or archives.
- **Engagement Mechanisms:** Secure, location-aware commenting system with built-in XSS protection (Sanitize-HTML). Users can also "Like", "Share", and "View" content, feeding into the admin analytics engine.
- **Theme Customization:** Integrated Light/Dark mode toggling managed globally via React Context API.
- **Responsive Design:** Highly optimized UI tailored for cross-device compatibility.

### 3. Automated Email Ecosystem
- **Instant Alerts:** Sends customized HTML emails via Nodemailer whenever a user comments on a blog or project, ensuring the owner stays instantly updated.

## System Architecture Highlights
- **Client-Server Separation:** Decoupled architecture where the React frontend communicates securely with the Express backend via RESTful APIs.
- **Media Optimization:** Offloads media storage to Cloudinary directly from memory buffers (Multer), preventing local server bloat and ensuring fast global content delivery.
- **Analytics Tracking:** Records granular events (Views, Likes, Shares, Comments) with timestamps and user details to generate robust insights without relying exclusively on third-party tracking scripts.
