# Core Logic and System Architecture - Anik Personal Blog

This document details the internal mechanisms, architecture, and core logic implemented in the "Anik Personal Blog" application.

## 1. System Architecture
The application follows a **Client-Server Architecture** utilizing the **MERN stack** (MongoDB, Express, React, Node.js), augmented with Firebase and Cloudinary.
- **Frontend (Client):** Built with React and Vite. Handles UI rendering, client-side routing (`react-router-dom`), local state, and global state (Theme Context).
- **Backend (Server):** An Express.js REST API. It acts as the intermediary between the frontend and the database/cloud services.
- **Database:** MongoDB Atlas is used for persistent data storage, utilizing Mongoose as the Object Data Modeling (ODM) library.

## 2. Authentication & Authorization Flow
### Mechanism
Authentication is handled via **Firebase Authentication** on the frontend, which issues a JSON Web Token (JWT). The backend verifies this token using the **Firebase Admin SDK**.

### Implementation Details
- **Frontend:** Users login/register using Firebase Auth (`firebase.js`). Protected routes (`PrivateRoute.jsx`) wrap components that require authentication, checking the current Firebase user state before rendering.
- **Backend Middleware (`verifyToken`):** 
  Intercepts incoming requests, extracts the Bearer token from the `Authorization` header, and verifies it using `admin.auth().verifyIdToken(token)`. If valid, it attaches the decoded user data to `req.user`.
- **Role-Based Access Control (`verifySuperAdmin`):**
  A secondary middleware checks if `req.user.email` matches the predefined `SUPER_ADMIN_EMAIL` environment variable. This secures highly sensitive routes (e.g., approving new admins).
- **Why?** Firebase provides highly secure, out-of-the-box credential management. Verifying the token on the backend ensures that APIs cannot be accessed via forged client-side states.

## 3. Advanced Admin Security Logic
The admin login system is designed with enterprise-grade security features.

### Implementation Details
- **Approval Workflow:** An `AdminUser` model tracks admins with statuses (`pending`, `approved`, `rejected`, `removed`). Even if an admin authenticates via Firebase, they cannot access the dashboard until the Super Admin changes their status to `approved`.
- **Device & Location Tracking:** Uses `ua-parser-js` to extract device/browser info and `axios` with `ip-api.com` to track geographical location during login/registration.
- **Brute-Force Protection:** The backend tracks the timestamps of login attempts in an array. If more than 5 attempts occur within 5 minutes, it sets a `blockedUntil` date (current time + 15 mins). Subsequent requests are rejected until the timer expires.
- **Alert System:** Uses `nodemailer` to send instant email alerts to the Super Admin if a login occurs from an unrecognized IP/Device, or if an account gets blocked.
- **Why?** Since the admin panel contains sensitive portfolio data and analytics, standard password protection is insufficient. These measures protect against brute-force attacks and credential stuffing.

## 4. Media Handling & Storage
### Mechanism
Instead of storing files on the local server file system, images are uploaded directly to **Cloudinary**.

### Implementation Details
- **Multer Memory Storage:** The route uses `multer({ storage: multer.memoryStorage() })`. This keeps the uploaded file as a Buffer in RAM instead of writing it to disk.
- **Cloudinary Stream:** The Buffer is passed to `cloudinary.uploader.upload_stream`. Once uploaded, Cloudinary returns a `secure_url`, which is then saved to the MongoDB document (e.g., Blog or Project model).
- **Why?** Cloudinary provides a global CDN, automatic image optimization, and prevents the Node.js server from running out of disk space. Using memory storage skips the I/O bottleneck of writing/reading local temporary files.

## 5. Security & Data Integrity
### Cross-Site Scripting (XSS) Prevention
- **Implementation:** When a user submits a comment, the backend utilizes `sanitize-html` to strip out any malicious `<script>` tags or attributes before saving it to the database.
- **Why?** Since comments are rendered on the frontend for other users to see, failing to sanitize inputs could allow attackers to inject malicious JavaScript.

### Granular Analytics Tracking
- **Implementation:** Custom schemas track interactions. For example, the `Blog` model has arrays for `likes`, `shares`, and `views`. When a user likes a post, the backend checks if their `userId` is already in the `likes` array. If it is, it removes it (unlike); if not, it pushes it (like). It also stores the timestamp.
- **Why?** Storing explicit timestamps and user IDs allows the admin dashboard to generate precise, custom analytics graphs without paying for third-party analytics services.

## 6. Frontend State & Routing
- **ThemeContext:** Uses React Context to provide a global `theme` variable (light/dark). The `<App>` component attaches `data-theme={theme}` to the root div, allowing CSS variables to dynamically shift colors.
- **React Router:** Uses nested routes (e.g., `<Route path="/" element={<UserDashboard />}> <Route index element={<Home />} /> </Route>`) to maintain persistent layout elements (like Navbars and Footers) while swapping out internal page content.
