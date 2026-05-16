# Mirinjapaingtong Valley — Core Logic & Technical Implementation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Backend Implementation](#backend-implementation)
3. [Frontend Implementation](#frontend-implementation)
4. [Core Logic Deep-Dives](#core-logic-deep-dives)
5. [API Design & Endpoints](#api-design--endpoints)
6. [Security Implementation](#security-implementation)

---

## Architecture Overview

### Project Structure
```
backend/
├── config/          → DB connection, Cloudinary setup
├── middleware/       → auth.js (JWT verify), admin.js (role check)
├── models/          → 13 Mongoose schemas
├── routes/          → 12 route files + 4 admin sub-routes
├── utils/           → email.js (Nodemailer), validation.js (Joi schemas)
├── server.js        → Express app setup, middleware chain, route mounting
└── vercel.json      → Serverless deployment config

frontend/
├── src/
│   ├── components/  → 15 reusable components (layouts, forms, cards, receipts)
│   ├── hooks/       → useAuth.jsx (Context + JWT), useApi.jsx (Axios instance)
│   ├── pages/       → public/ (12), user/ (4), admin/ (15), auth/ (4)
│   ├── utils/       → constants.js, formatters.js, receipts.js
│   ├── App.jsx      → Router with nested routes + ProtectedRoute
│   └── main.jsx     → Entry point, AuthProvider wraps entire app
└── vercel.json      → SPA rewrite rules
```

### Design Pattern
**The app follows a layered architecture:**
- **Frontend**: Component-based (React) with Context API for global auth state
- **Backend**: Route-handler pattern (no separate controller files — route files contain both routing and business logic)
- **Why no controllers?** For a project this size, keeping route definitions and handlers together in one file reduces file-hopping. Each route file acts as both router and controller.

---

## Backend Implementation

### 1. Server Entry Point (`server.js`)

**What it does:** Initializes Express, connects MongoDB, applies global middleware, mounts all 16 API route groups.

**Middleware chain order (critical — order matters):**
```
1. helmet()              → Sets secure HTTP headers (X-Content-Type, HSTS, etc.)
2. cors({ origin })      → Restricts API access to the production frontend domain only
3. express.json()        → Parses JSON request bodies
4. express.urlencoded()  → Parses URL-encoded form data
5. rateLimit()           → 10,000 requests per 15-minute window per IP
```

**Why this order?** Security headers (helmet) go first so every response is secured. CORS runs before parsing to reject disallowed origins early. Rate limiting is last global middleware so it only counts valid requests.

**Deployment:** The app exports `module.exports = app` instead of calling `app.listen()`. This is because Vercel's `@vercel/node` runtime expects a module export — it handles the HTTP server internally in its serverless environment.

---

### 2. Database Configuration (`config/db.js`)

**What it does:** Connects to MongoDB Atlas using `mongoose.connect()` with the connection string from `.env`.

**Why `process.exit(1)` on failure?** If the database can't connect, the API can't function. Crashing immediately is better than silently serving 500 errors on every request. In Vercel serverless, each cold start retries the connection anyway.

---

### 3. Cloudinary Configuration (`config/cloudinary.js`)

**What it does:** Initializes Cloudinary SDK v2 with cloud credentials from `.env`.

**Why Cloudinary?** Filesystem storage doesn't work on serverless (Vercel). Cloudinary provides a CDN-backed media storage with automatic image optimization and transformation.

---

### 4. Middleware

#### `middleware/auth.js` — JWT Authentication Middleware
```
Flow: Request → Extract Bearer token → jwt.verify() → Find user in DB → Check isActive → Attach to req.user → next()
```

**Key decisions:**
- **Extracts token from `Authorization: Bearer <token>` header** using optional chaining (`?.replace`)
- **Verifies against `JWT_SECRET`** — if the token is tampered, `jwt.verify` throws and the catch returns 401
- **Looks up the user in DB** — this ensures deactivated accounts can't use old valid tokens. Even if the JWT is valid, if `user.isActive === false`, access is denied
- **Attaches full user document to `req.user`** — downstream handlers can access user data without re-querying

**Why not just trust the JWT payload?** Because the admin might deactivate a user between token issuance and request. The DB lookup ensures real-time access control.

#### `middleware/admin.js` — Role Authorization Middleware
```
Flow: Check req.user.role === 'admin' → If not, return 403 → If yes, next()
```

**Key design:** This middleware is always used AFTER `auth.js` in the chain: `router.get('/', auth, admin, handler)`. The `auth` middleware populates `req.user`, then `admin` checks the role. This is the **middleware chaining pattern** — composable, single-responsibility middleware.

---

### 5. Models (Mongoose Schemas)

#### User Model (`models/User.js`)
**Fields:** name, email (unique, lowercase), password, phoneNumber, address, pinCode, dateOfBirth, role (enum: user/admin), isVerified, isActive, profileImage, registrationLocation (city/country), registrationTime, wishlist (ObjectId array ref Room), passwordResetToken, passwordResetExpires

**Critical logic:**
- **`pre('save')` hook:** Hashes password with bcrypt (salt rounds: 12) only when `isModified('password')` — prevents re-hashing on non-password updates
- **`pre('findOneAndUpdate')` hook:** Hashes password in update operations too — covers `findByIdAndUpdate` used in admin routes
- **`comparePassword` instance method:** Uses `bcrypt.compare()` for timing-safe comparison during login
- **Wishlist as embedded array:** Room ObjectIds stored directly in user doc. For a resort with limited rooms, this avoids a separate join collection

#### Room Model (`models/Room.js`)
**Fields:** name, description, pricePerNight, maxAdults, maxChildren, totalGuests, images (string array), facilities/features (ObjectId arrays ref Facility/Feature), isActive, availability (subdocument array with from/to dates + bookedBy ref), averageRating

**Availability design:** The `availability` array stores booked date ranges as subdocuments: `{ from: Date, to: Date, bookedBy: ObjectId }`. When a booking is confirmed, a new slot is pushed. When cancelled, it's filtered out. This approach allows overlap checking without a separate availability collection.

#### Booking Model (`models/Booking.js`)
**Fields:** room (ref), user (ref), checkIn, checkOut, adults, children, totalGuests, totalPrice, status (enum: pending/confirmed/cancelled), fullName, email, phoneNumber, address, paymentMethod (enum: bkash/nagad/upai), paymentAccount, bookingTime, paidAmount, dueAmount, paymentDate

**Payment tracking:** `paidAmount` and `dueAmount` are separate fields updated by admin — enabling partial payment tracking. `paymentDate` records when payment was verified.

#### Content Model (`models/Content.js`)
**Uses nested sub-schemas** — `exploreSchema` and `aboutSchema` are defined separately and composed into `ContentSchema`. This is a **singleton document pattern** — only one Content document exists in the DB, fetched via `Content.findOne()`.

**Why singleton?** The resort has one "Explore" section and one "About" page. Using `findOne()` without a filter always returns the single document. If it doesn't exist, the GET route auto-creates it with defaults.

#### SiteSetting Model (`models/SiteSetting.js`)
**Also a singleton.** Contains all configurable site settings: branding, contact, social links, operating hours, check-in/out times, currency, tax rate, and system toggles (maintenanceMode, bookingPaused).

**`upsert: true` in update route:** Ensures the document is created if it doesn't exist during the first admin update.

#### VisitAnalytics Model (`models/VisitAnalytics.js`)
**Compound index:** `{ date: 1, city: 1, country: 1 }` with `unique: true`. This ensures one document per day per location. The `record-visit` endpoint uses `findOne` + increment pattern instead of `upsert` to handle the uniqueness.

---

### 6. Routes (API Handlers)

#### Auth Routes (`routes/auth.js`)
**Registration flow:**
1. Validate input with Joi schema (abortEarly: false → returns ALL errors)
2. Check for duplicate email
3. Create user (password auto-hashed by pre-save hook)
4. Send welcome email via Nodemailer
5. Generate JWT (1-hour expiry) and return it

**Login flow:**
1. Find user by email
2. Compare password using bcrypt instance method
3. Generate and return JWT

**Forgot Password flow:**
1. Generate cryptographically random token (`crypto.randomBytes(20)`)
2. Store token and expiry (1 hour) on the user document
3. Send branded HTML email with reset link containing the token
4. Reset endpoint: find user by token + check expiry → update password → clear token fields → send confirmation email

**Profile routes (`GET /me`, `PUT /me`):** The `PUT /me` route explicitly `delete updates.email` to prevent email modification — a security measure.

#### Booking Routes (`routes/bookings.js`)
**Booking creation flow:**
1. Validate with Joi bookingSchema
2. Find the room
3. **Overlap check:** Iterates room's availability array; if any slot overlaps with requested dates, returns 400
4. Create booking with status `pending`, paidAmount `0`, dueAmount = totalPrice
5. Send detailed HTML booking confirmation email

**Overlap detection algorithm:**
```javascript
const overlap = room.availability.some(slot => {
  return !(new Date(checkOut) <= new Date(slot.from) || new Date(checkIn) >= new Date(slot.to));
});
```
**Logic:** Two ranges DON'T overlap only if one ends before the other starts. The negation catches all overlap cases.

**Admin booking update flow:**
- If status changed to `confirmed`: Push date range to room's availability array + send confirmation email
- If status changed to `cancelled`: Filter out the matching availability slot from room + send cancellation email
- If payment updated (no status change): Send payment update email

**User cancellation rules:**
- Only `pending` bookings can be cancelled by users
- Must be within 24 hours of booking time: `(now - bookingTime) / (1000 * 60 * 60) > 24` → reject
- On cancel: set status to `cancelled` + send email

**Pagination:** Recent bookings (last 30 days) and full history both use `skip/limit` with `Promise.all([query, countDocuments])` for parallel execution.

#### Room Routes (`routes/rooms.js`)
**Smart filtering:** The GET `/` endpoint builds a dynamic MongoDB query object:
```javascript
if (search) query.name = { $regex: search, $options: 'i' };
if (priceMin) query.pricePerNight = { $gte: Number(priceMin) };
if (adults) query.maxAdults = { $gte: parseInt(adults) };
if (facilities) query.facilities = { $all: facilities.split(',') };  // ALL listed facilities must be present
if (checkIn && checkOut) query.availability = { $not: { $elemMatch: overlap condition } };
```
**Date filtering uses `$not` + `$elemMatch`:** Returns rooms that do NOT have any availability slot overlapping the requested dates — meaning the room IS available.

**Availability cleanup:** Both GET `/` and GET `/:id` filter out expired slots: `slot.to > now`. This prevents past bookings from showing as "booked" on the calendar.

**Room update preserves availability:** When editing room details, the update route merges `req.body.availability` only if explicitly sent, otherwise keeps existing availability. This prevents admin edits from accidentally clearing booking data.

#### Review Routes (`routes/reviews.js`)
**Rating recalculation:** After creating or deleting a review, the route fetches ALL reviews for that room, computes the average, and updates `room.averageRating`. This is a **derived field pattern** — the average is stored for fast reads but recalculated on every write.

**Top reviews endpoint:** `GET /top` filters for rating >= 4 and returns the 10 most recent — used on the homepage review slider.

#### Upload Routes (`routes/uploads.js`)
**File upload pipeline:**
```
Client (FormData) → Multer (memoryStorage) → Cloudinary upload_stream → Return secure_url
```
**Why `memoryStorage`?** On serverless (Vercel), there's no persistent filesystem. Files are buffered in memory, streamed directly to Cloudinary via `upload_stream`, then discarded.

**Multi-image upload:** Uses `upload.array('images', 10)` — accepts up to 10 files. Each is uploaded via `Promise.all` for parallel Cloudinary uploads.

**Three endpoints:** `/image` (multi, auth required), `/single-image` (single, no auth — for profile pics during registration), `/video` (single, auth required, `resource_type: 'video'`).

#### Admin Analytics (`routes/admin/analytics.js`)
**Uses `Promise.all` extensively** to run 15+ count/aggregate queries in parallel:
```javascript
const [totalRooms, activeRooms, inactiveRooms] = await Promise.all([...]);
```
**Revenue uses MongoDB aggregation:** `$match` (confirmed bookings in period) → `$group` (sum totalPrice/paidAmount/dueAmount). Returns 0 if no results via `revenueData[0]?.total || 0`.

**Period filtering:** Calculates `fromDate` based on query param (today/week/month/90days/year/all).

#### Admin Email Routes (`routes/admin/emails.js`)
**Three email types:**
- `individual`: Send to specific recipients
- `all`: Fetch all user emails from DB, send to everyone
- `marketing`: External email addresses

**Uses `Promise.allSettled`** (not `Promise.all`) for sending — this ensures one failed email doesn't abort the rest. Returns partial success counts.

#### Visitor Analytics (`routes/admin/visitorAnalytics.js`)
**Recording:** Uses find-or-create pattern with compound key (date + city + country). If record exists, increment count; otherwise create with count 1.

**Reporting:** MongoDB aggregation groups by city/country, sums counts, sorts by most visits.

---

### 7. Utilities

#### `utils/validation.js` — Joi Schemas
**Three schemas:** userSchema, bookingSchema, roomSchema

**Notable validations:**
- Phone: Regex supporting Bangladesh (+88), India (+91), and other Asian country codes
- PIN code: 4-6 digit pattern
- Date of birth: `Joi.date().less('now')` — must be in the past
- Booking checkOut: `Joi.date().greater(Joi.ref('checkIn'))` — must be after check-in
- Room: Custom validator ensuring `maxAdults + maxChildren <= totalGuests`
- Room images: `Joi.array().items(Joi.string().uri()).min(1)` — at least one valid URL

#### `utils/email.js` — Nodemailer Utility
**Configures Gmail SMTP** with app password. The `sendEmail` function accepts a `isHtml` flag — if true, sets `mailOptions.html` instead of `.text`. Returns `{ success, error }` for error handling upstream.

---

## Frontend Implementation

### 1. Entry Point & Auth Provider (`main.jsx`)

**`AuthProvider` wraps the entire app** — this is the React Context pattern for global state. Any component can access `user`, `login`, `register`, `logout`, etc. via the `useAuth()` hook.

### 2. Custom Hooks

#### `useAuth.jsx` — Authentication Context
**On mount:** Checks `localStorage` for token → calls `GET /auth/me` to verify → sets user state. If token is invalid/expired, clears localStorage and shows toast.

**Login flow:**
1. POST `/auth/login` → receive JWT
2. Store in localStorage
3. Immediately fetch `/auth/me` to get full user data
4. Set user in context state

**Why fetch `/me` after login?** The login response only returns `{ token, role }`. We need the full user profile (name, email, profileImage, etc.) for the UI, so we make a second request with the new token.

**Logout:** Simply removes token from localStorage and sets user to null. No server-side session to invalidate — JWT is stateless.

#### `useApi.jsx` — Axios Instance with Interceptors
**Request interceptor:** Automatically attaches `Authorization: Bearer <token>` from localStorage to every request. Supports `skipAuth` config option for public endpoints.

**Response interceptor:** Global error handler — shows toast with error message from server (`err.response.data.msg`) on any failed request.

**FormData detection:** The `post` and `put` methods check if data is `instanceof FormData` and set `Content-Type: multipart/form-data` automatically — used for file uploads.

**Why a custom hook?** Centralizes API configuration, token management, and error handling. Components just call `const { get, post, put, delete } = useApi()` without worrying about headers or error toasts.

### 3. Routing (`App.jsx`)

**Three-tier nested routing:**
```
/ (public routes — no auth)
  ├── /rooms, /rooms/:id, /rooms/:id/book, etc.
  
/user (ProtectedRoute role="user")
  ├── /user/dashboard, /user/profile, /user/bookings, /user/wishlist
  
/admin (ProtectedRoute role="admin")
  ├── /admin/dashboard, /admin/rooms, /admin/bookings, ... (15 routes)
```

**Layout components:** `UserLayout` and `AdminLayout` use React Router's `<Outlet />` for nested rendering. The admin sidebar is part of `AdminLayout`, so it persists across all admin pages.

### 4. Protected Route Component

```jsx
if (loading) return <div>Loading...</div>;
if (!user) return <Navigate to="/login" replace />;
if (role && user.role !== role) return <Navigate to="/" replace />;
return children;
```
**Three checks in order:**
1. **Loading** — wait for auth check to complete (prevents flash of login page)
2. **Not authenticated** — redirect to login
3. **Wrong role** — redirect to home (prevents user accessing admin and vice versa)

### 5. Key Components

#### `BookingForm.jsx` — Client-Side Availability Check
**The availability check runs entirely on the client** using room data already fetched:
```javascript
const isAvailable = (() => {
  // Build set of all booked day keys
  // Check if any requested day is in the booked set
  return true/false;
})();
```
**Why client-side?** Reduces server round-trips. The room's availability data is already loaded. The server does a second check on submission as the source of truth.

**Price calculation:** `nights * pricePerNight` — recalculated via `useEffect` whenever check-in or check-out dates change.

#### `VisitTracker.jsx` — Visitor Analytics Collection
**Flow:**
1. Skip if on admin pages
2. Generate or retrieve session ID from `sessionStorage`
3. Check if already counted today (using `sessionStorage`)
4. Wait 10 seconds (to filter out bounces)
5. Get visitor IP via ipify API
6. Get geolocation via ipapi API
7. POST to `/admin/visitorAnalytics/record-visit`
8. Mark today as counted

**Why 10-second delay?** Filters out bots and accidental page loads. Only genuine visitors who stay on the page get counted.

#### `AdminLayout.jsx` — Real-Time Sidebar Badges
**Fetches three counts on mount and every 30 seconds:**
- Unread queries count
- Pending bookings count
- Unverified users count

**Resets count when navigating** to the relevant page (queries → 0 when on /admin/queries).

### 6. Frontend Utilities

#### `formatters.js`
- `formatDate`: Formats dates to "May 12, 2026" format
- `formatPrice`: Formats to Bangladeshi Taka (`৳`) with locale formatting

#### `constants.js`
Design tokens: primary teal (#008080), accent orange (#FF8C00), background beige (#F5F5DC).

---

## Core Logic Deep-Dives

### Room Availability Algorithm
**Problem:** Multiple users might try to book overlapping dates for the same room.

**Solution (Backend):**
1. Room stores `availability[]` array with `{ from, to, bookedBy }` subdocuments
2. On booking creation: check if ANY existing slot overlaps with requested dates
3. Overlap formula: `!(checkOut <= slot.from || checkIn >= slot.to)` — if this is true for any slot, room is unavailable
4. On confirmation: push new slot to array
5. On cancellation: filter out the matching slot

**Solution (Frontend):**
1. Build a `Set` of all booked date keys (YYYY-MM-DD)
2. Iterate from check-in to check-out, checking if each day is in the booked set
3. Calendar component uses `tileClassName` to color-code booked (orange) vs available (teal) dates

### Authentication Flow
```
Register → Joi validate → Check duplicate → bcrypt hash (pre-save hook) → Save → JWT sign → Return token
Login → Find by email → bcrypt compare → JWT sign → Return token
Every protected request → Extract Bearer token → jwt.verify → DB lookup (check isActive) → Attach to req.user
```

### Email Notification Pipeline
**All emails use branded HTML templates** with inline CSS (for email client compatibility). Each template includes:
- Resort header with name and location
- Content section with booking/action details
- Color-coded alert box (warning=yellow, success=green, danger=red)
- Footer with support contact

### File Upload Pipeline
```
Client: FormData with file(s) → 
Multer: memoryStorage (buffer in RAM) → 
Cloudinary: upload_stream (stream buffer to CDN) → 
Response: Return secure_url(s) to client → 
Client: Store URL in form state → Submit to API → Save URL in MongoDB
```

---

## API Design & Endpoints

### Route Mounting Map
| Prefix | Route File | Auth Required |
|---|---|---|
| `/api/auth` | auth.js | Mixed (register/login: no, me: yes) |
| `/api/rooms` | rooms.js | Mixed (GET: no, POST/PUT/DELETE: admin) |
| `/api/bookings` | bookings.js | Yes (user for create/cancel, admin for manage) |
| `/api/facilities` | facilities.js | Mixed (GET: no, CUD: admin) |
| `/api/features` | features.js | Mixed (GET: no, CUD: admin) |
| `/api/carousel` | carousel.js | Mixed (GET public: no, admin CRUD: admin) |
| `/api/reviews` | reviews.js | Mixed (GET: no, POST: user, DELETE: admin) |
| `/api/queries` | queries.js | Mixed (POST: no, GET/manage: admin) |
| `/api/menu` | menu.js | Mixed (GET: no, CUD: admin) |
| `/api/settings` | settings.js | Mixed (GET: no, PUT: admin) |
| `/api/uploads` | uploads.js | Mixed (single-image: no, others: yes) |
| `/api/content` | content.js | Mixed (GET: no, PUT/manage: admin) |
| `/api/admin/users` | admin/users.js | Admin only (+ wishlist: user) |
| `/api/admin/analytics` | admin/analytics.js | Admin only |
| `/api/admin/visitorAnalytics` | admin/visitorAnalytics.js | Mixed (record: no, get: admin) |
| `/api/admin/emails` | admin/emails.js | Admin only |

---

## Security Implementation

| Mechanism | Implementation | Why |
|---|---|---|
| **Password Hashing** | bcryptjs with 12 salt rounds | Industry standard, timing-safe comparison |
| **JWT Auth** | 1-hour expiry, secret from env var | Stateless auth for serverless |
| **DB User Lookup on Every Request** | auth middleware queries User model | Ensures deactivated users lose access immediately |
| **Helmet** | Sets secure HTTP headers | Prevents XSS, clickjacking, MIME sniffing |
| **CORS** | Restricted to production domain only | Prevents unauthorized API access from other domains |
| **Rate Limiting** | 10,000 requests / 15 min per IP | Prevents brute-force and DoS |
| **Joi Validation** | Server-side schema validation on all inputs | Prevents injection and malformed data |
| **Email Immutability** | `delete updates.email` in PUT routes | Prevents account takeover via email change |
| **Password Immutability** | `delete updates.password` in admin user update | Forces password changes through proper auth flow |
| **Reset Token Expiry** | 1-hour window + token cleared after use | Prevents replay attacks on reset links |
| **Crypto Random Tokens** | `crypto.randomBytes(20)` | Cryptographically secure, unpredictable tokens |
