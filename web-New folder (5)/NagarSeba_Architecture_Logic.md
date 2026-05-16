# NagarSeba - Core Architecture & Technical Logic

This document details the core implementation logic, system architecture, and specific development patterns utilized in the NagarSeba platform.

---

## 1. System Architecture Overview

NagarSeba follows a decoupled Client-Server architecture utilizing the **MERN** stack (MongoDB, Express, React, Node.js). 

- **Frontend:** React 18 single-page application built with Vite for optimized bundling and fast hot-module replacement (HMR).
- **Backend:** Express.js RESTful API serving JSON data.
- **Real-Time Layer:** WebSockets (Socket.IO) handling real-time, bi-directional communication between client and server for instant ticket status updates.
- **Background Jobs:** Node-cron tasks running within the Node process to handle time-based events (SLAs, Auto-resolutions).

---

## 2. Backend Implementation & Core Logic

### 2.1 Routing & Controllers
The backend strictly follows the MVC (Model-View-Controller) design pattern. 
- **Routes:** Categorized by domain (`auth`, `issues`, `authority`, `admin`, `tenders`, `public`).
- **Controllers:** Controllers handle business logic, database queries, and response formatting. This keeps route definitions clean and readable.

### 2.2 Middleware Integration
Middleware functions intercept incoming requests before they reach the controllers.
- **Authentication (`authenticate`):** Validates the JWT Access Token in the `Authorization` header. If valid, attaches the user object to `req.user`. If expired, it handles `TokenExpiredError` securely.
- **Role-Based Access Control (`authorize`):** Takes a list of allowed roles (e.g., `authorize('admin', 'authority')`). Verifies if `req.user.role` matches the requirement.
- **File Uploads (Multer):** Intercepts multipart form data, storing images in memory briefly before streaming them directly to Cloudinary.

### 2.3 Authentication Flow (Access & Refresh Tokens)
To balance security and UX, a dual-token JWT system is implemented:
1. **Login:** Server issues a short-lived `accessToken` (e.g., 15m) and a long-lived `refreshToken` (e.g., 7d).
2. **Access:** Client sends the `accessToken` with every API request.
3. **Refresh:** If `accessToken` expires, the frontend's centralized API interceptor catches the `401 Unauthorized` error, automatically hits the `/api/auth/refresh-token` endpoint with the `refreshToken`, receives a new `accessToken`, and retries the failed request invisibly.

### 2.4 Models & Database Logic (MongoDB)
Mongoose is used as the ODM. Complex querying logic includes:
- **Geospatial Queries:** The `Issue` model uses a GeoJSON `Point` schema for location data. A `2dsphere` index is applied. To detect duplicate reports, the server uses the MongoDB `$near` operator to find issues within a 150-meter radius submitted recently.
- **Data Encryption:** For anonymous reporters, personal identifiable information (PII) is AES-encrypted before being saved to MongoDB, ensuring even direct database access cannot reveal the reporter's identity.

### 2.5 Background Jobs (node-cron)
The server runs lightweight background tasks without needing external queue managers (like Bull/Redis) to keep free-tier costs zero.
- **SLA Monitor:** Runs every hour. Queries issues where `slaDeadline < now` and `status != 'Resolved'`. Updates status to `Overdue`, triggers emails to authorities, and alerts Admins.
- **Auto-Confirm Loop:** Runs every 6 hours. Auto-closes `Resolved` tickets if the citizen hasn't confirmed or rejected the fix within 48 hours.

### 2.6 External Service Utilities (`/utils`)
- **Gemini AI Categorization:** Extracts context from citizen complaints via prompt engineering and returns a structured JSON predicting the best category and urgency.
- **Cloudinary Integration:** Automatically resizes and compresses image uploads before saving the URL to MongoDB.

---

## 3. Frontend Implementation & Core Logic

### 3.1 Code Splitting & Routing
To ensure lightning-fast initial load times on mobile networks, React Router is paired with `React.lazy()` and `Suspense`. 
- Only public routes and the login page are bundled in the initial JS payload.
- Heavy dashboard views and Chart.js bundles are fetched dynamically only when the user navigates to them.
- A `<ProtectedRoute>` wrapper component checks the User Context. If unauthorized, it redirects to `/login`.

### 3.2 Centralized API Service (`api.js`)
Instead of scattered `fetch()` calls, all HTTP requests pass through a custom API utility.
- **Why?** It guarantees the JWT token is attached to every outgoing request.
- **Interceptor Logic:** Contains logic to catch `401` errors globally, handle the refresh token handshake, and retry the request, resulting in zero disruptions for the user.

### 3.3 Context API for State Management
- `AuthContext` provides global access to `user` state, `login()`, and `logout()` functions. Complex Redux was avoided in favor of native Context + Hooks, reducing boilerplate and bundle size.

### 3.4 Custom Hooks
Custom hooks abstract away UI complexity:
- `useSocket`: Manages Socket.IO connection lifecycle, joins user-specific rooms on mount, and handles disconnects on unmount.

### 3.5 Localization (i18next)
The UI is fully bilingual (Bangla/English) using `react-i18next`. The user's preference is synced to their profile and localStorage, dynamically switching text dictionaries without reloading the application.

---

## 4. Key Logic Workflows

### The "Issue Submission to Resolution" Workflow:
1. **Client:** Uses HTML5 Geolocation to get Lat/Lng. Invokes Web Speech API for dictation. Submits FormData.
2. **Backend:** Multer intercepts photos → Uploads to Cloudinary.
3. **Backend:** Creates `Issue` doc in MongoDB. Calculates SLA deadline based on Category rules.
4. **Backend:** Emits a Socket.IO event to the Authority Dashboard room. Uses Firebase Admin SDK to push a notification to the assigned officer's phone.
5. **Authority:** Opens ticket, marks "In Progress". Socket.IO instantly updates the citizen's UI.
6. **Authority:** Marks "Resolved".
7. **Client (Citizen):** Receives an actionable notification to Verify (Confirm/Reject). If rejected, the backend increments the `reopenCount` and pushes it back to the top of the Authority's inbox.
