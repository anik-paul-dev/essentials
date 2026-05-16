# BD-MarketPlace — Technical Implementation Deep Dive

## Table of Contents
1. [Backend Architecture](#1-backend-architecture)
2. [Middleware Pipeline](#2-middleware-pipeline)
3. [Authentication System](#3-authentication-system)
4. [Database Models](#4-database-models)
5. [Controllers — Business Logic](#5-controllers--business-logic)
6. [Route Organization](#6-route-organization)
7. [Utility Functions](#7-utility-functions)
8. [Config Layer](#8-config-layer)
9. [Frontend Architecture](#9-frontend-architecture)
10. [State Management — Context API](#10-state-management--context-api)
11. [Custom Hooks](#11-custom-hooks)
12. [Component Architecture](#12-component-architecture)
13. [Real-Time Communication](#13-real-time-communication)
14. [Deployment Strategy](#14-deployment-strategy)

---

## 1. Backend Architecture

### Dual Entry Points

**`server.js`** — Used for local development:
- Creates HTTP server with `http.createServer(app)` (needed for Socket.IO to attach)
- Initializes Socket.IO via `initSocket(server)`
- Listens on `PORT` (default 5000)

**`api/index.js`** — Used for Vercel serverless deployment:
- Same Express app setup but `module.exports = app` (no `server.listen()`)
- Vercel's `@vercel/node` runtime wraps it as a serverless function
- No Socket.IO initialization (serverless can't maintain persistent connections)

**Why two entry points?** Vercel serverless functions are stateless and short-lived — they can't hold WebSocket connections. So `server.js` runs the full app with Socket.IO locally, while `api/index.js` exports a bare Express app for serverless. The frontend detects this and falls back to HTTP polling.

### Middleware Stack (applied in order)
```
Request → Helmet → CORS → JSON Parser (10MB limit) → URL Parser → Cookie Parser → Rate Limiter → Routes → Error Handler
```

---

## 2. Middleware Pipeline

### `middleware/auth.js` — Authentication & Authorization

**`protect` middleware** — Guards authenticated routes:
1. Extracts JWT from `req.cookies.token` (HTTP-only cookie) OR `Authorization: Bearer <token>` header
2. Verifies token with `jwt.verify(token, JWT_SECRET)`
3. Fetches full user from DB: `User.findById(decoded.id).select('-password')`
4. Checks `user.isActive` — blocks deactivated accounts with 403
5. Attaches user to `req.user` for downstream controllers
6. Handles `TokenExpiredError` and `JsonWebTokenError` separately for proper error messages

**Why dual token extraction?** HTTP-only cookies work for same-origin requests, but cross-origin requests (frontend on different Vercel domain) can't always send cookies due to browser SameSite policies. The `Authorization` header fallback ensures tokens work across all deployment scenarios.

**`optionalAuth` middleware** — Soft authentication:
- Same token extraction logic but **never blocks** the request
- If token exists and is valid → sets `req.user`
- If no token or invalid → sets `req.user = null` and continues
- Used for: product listing (personalized results), checkout (guest vs. logged-in)

**`authorize(...roles)` middleware** — Role-based access:
- Higher-order function returning middleware
- Checks `req.user.role` against allowed roles array
- Returns 403 if role doesn't match
- Usage: `authorize('admin')`, `authorize('shop', 'user')`

**Google OAuth (Passport.js):**
- Only initializes if `GOOGLE_CLIENT_ID` env var exists (graceful degradation)
- Strategy: finds user by `googleId`, or by email (links existing account), or creates new user
- Also supports direct token-based login via `googleTokenLogin` — frontend sends Google `access_token`, backend verifies with Google API (`googleapis.com/oauth2/v3/userinfo`)

### `middleware/errorHandler.js` — Centralized Error Handling

Catches all errors passed via `next(error)`:
- **Mongoose CastError** (bad ObjectId) → 404 "Resource not found"
- **Mongoose Duplicate Key** (code 11000) → 400 with field name
- **Mongoose ValidationError** → 400 with all validation messages joined
- **JWT errors** → 401 with specific messages
- **Everything else** → 500 "Server Error"

**Why centralized?** Every controller uses `try/catch` with `next(error)` — this single handler normalizes all error responses to `{ success: false, message }` format.

### `middleware/rateLimiter.js` — DDoS Protection

Three tiers using `express-rate-limit`:
| Limiter | Window | Max Requests | Applied To |
|---|---|---|---|
| `generalLimiter` | 15 min | 200 | All API routes |
| `authLimiter` | 15 min | 20 | Login/Register/Forgot Password |
| `uploadLimiter` | 15 min | 30 | Image upload routes |

**Why tiered?** Auth endpoints are prime brute-force targets, so they get stricter limits. Upload endpoints consume server resources (Cloudinary processing), so they're also restricted.

### `middleware/upload.js` — File Upload Pipeline

- **Multer** handles multipart/form-data parsing
- **CloudinaryStorage** streams files directly to Cloudinary (no local disk storage)
- Auto-transformation: width limited to 800px, quality auto-optimized
- Allowed formats: jpg, jpeg, png, gif, webp, mp4
- Max file size: 10MB
- Exports `deleteFromCloudinary(publicId)` for cleanup when images are replaced/deleted

---

## 3. Authentication System

### Token Flow
```
Register/Login → Server generates JWT (user._id + role) → Token sent in:
  1. HTTP-only cookie (secure, SameSite varies by env)
  2. Response body (client stores in localStorage + js-cookie)
→ Every subsequent request: token attached via Axios interceptor
→ Server extracts from cookie OR Authorization header
```

### JWT Configuration
- **Payload:** `{ id: user._id, role: user.role }`
- **Expiry:** 7 days (configurable via `JWT_EXPIRE` env)
- **Cookie settings:** `httpOnly: true`, `secure: true` in production, `sameSite: 'none'` in production (cross-origin), `'lax'` in development

### Password Reset Flow
1. User submits email → `forgotPassword` controller
2. Generate random 32-byte token → SHA-256 hash stored in DB
3. Raw token sent in email link: `/reset-password/{token}`
4. User clicks link → `resetPassword` controller hashes the URL token, matches against DB
5. Token has 30-minute TTL (`resetPasswordExpire` field)
6. On success: password updated (triggers `pre('save')` hook for hashing), token fields cleared

### Separate Login Endpoints
- `/auth/login` — Only allows `role: 'user'` or `'shop'`
- `/auth/admin/login` — Only allows `role: 'admin'` or `'superadmin'`
- **Why?** Prevents regular users from accidentally accessing admin panels and provides distinct error messages.

---

## 4. Database Models

### User Model
- **`publicId`**: nanoid (12 chars, lowercase alphanumeric) — used in URLs and API responses instead of MongoDB `_id`
- **`role`**: enum `['user', 'shop', 'admin', 'superadmin']`
- **`shopInfo`** (embedded subdocument): shopName, description, logo, banner, contact, address, `isVerified` flag
- **`address`** (embedded): street, area, city, division, postalCode — structured for Bangladesh
- **`wishlist`**: array of Product ObjectId refs
- **`savedProfiles`**: array of User ObjectId refs
- **`assignedCity`**: for admin role — scopes their management access
- **Pre-save hook**: hashes password with bcryptjs (only if password field modified)
- **Instance method**: `comparePassword()` for login verification

### Product Model
- **`publicId`**: nanoid for URL-safe identification
- **`category`**: ObjectId ref to Category (with `.populate()` for name)
- **`seller`** + **`sellerType`**: tracks who listed it (user vs. shop)
- **`images`**: array of `{ url, publicId }` — supports multi-image with Cloudinary public IDs for deletion
- **`unit`**: enum for BD market units (piece, kg, gram, liter, dozen, etc.)
- **`isApproved`**: defaults to `false` — requires admin/superadmin approval
- **`isFeatured`**: for homepage featured products
- **Text index**: on `title`, `description`, `tags` — enables MongoDB `$text` search

### Order Model
- **`orderId`**: custom format `ORD-{NANOID}` (10 chars uppercase) — human-readable
- **`buyer`**: nullable ObjectId (null for guest orders)
- **`isGuest`** + **`guestInfo`**: supports guest checkout
- **`items`**: embedded array with denormalized product data (title, price, image, seller ref) — ensures order history survives product deletion
- **`paymentMethod`**: enum `['stripe', 'cod', 'bkash', 'nagad', 'rocket']`
- **`paymentStatus`**: tracks payment lifecycle: pending → paid → failed → refunded
- **`orderStatus`**: tracks fulfillment: pending → confirmed → processing → shipped → delivered → cancelled
- **`orderCity`**: denormalized from shipping address — used by city-scoped admin queries

### Chat Model
- **`participants`**: array of 2 User ObjectId refs (indexed)
- **`messages`**: embedded subdocument array with `sender`, `text`, `read`, timestamps
- **`lastReadAt`**: `Map<userId, Date>` — tracks when each participant last read the chat for accurate unread counting
- **Why embedded messages?** For a marketplace chat, conversations are typically short. Embedding avoids extra collection joins and simplifies real-time updates.

### Category Model
- **`subcategories`**: string array (e.g., "Electronics" → ["Phones", "Laptops", "Accessories"])
- **`image`** + **`imagePublicId`**: category image stored on Cloudinary
- **`createdBy`**: tracks which admin created it

### SiteSettings Model (Singleton)
- Only one document exists — `findOne()` always returns the site config
- **CMS fields**: siteName, tagline, logo, favicon, hero banners (array with images), contact info, social links
- **Policy fields**: aboutUs, privacyPolicy, termsConditions, refundPolicy, cookiePolicy
- **Business fields**: currency, delivery charges (inside/outside city), min order amount, guest checkout toggle, maintenance mode
- **`featuredCategoryIds`**: ObjectId refs to Category — populated on public endpoint

### Notification Model
- **`type`**: enum categorizing notification source (order, payment, product, account, chat, system, approval)
- **`link`**: deep link URL for navigation when clicked
- Indexed on `user` field for fast per-user queries

### Review Model
- **Compound unique index**: `{ product, user }` — enforces one review per user per product
- **Aggregation pipeline** in controller recalculates `avgRating` and `numReviews` on the Product after each review

---

## 5. Controllers — Business Logic

### `authController.js`
- **`register`**: Validates role (only 'user'/'shop' allowed from public), creates user, generates token+cookie, sends welcome email
- **`login`**: Finds user by email+role filter, compares password, checks `isActive`, generates token
- **`adminLogin`**: Same as login but filters for admin/superadmin roles only
- **`googleTokenLogin`**: Receives Google OAuth `access_token` from frontend, verifies with Google API, creates/links user, generates JWT
- **`getMe`**: Returns authenticated user data (used by frontend AuthContext on page load)
- **`forgotPassword`/`resetPassword`**: Secure token-based password reset flow

### `productController.js`
- **`createProduct`**: Parses multi-file upload, maps Cloudinary response to `{ url, publicId }`, sets `isApproved: false`
- **`getProducts`**: Complex query builder — handles text search (`$text`), category lookup by name (finds Category doc first), regex filters for city/subcategory, price range (`$gte/$lte`), sort options, pagination
- **`getProduct`**: Finds by `publicId`, increments `views` counter, populates seller and category, fetches related reviews
- **`addReview`**: Upsert logic — updates existing review or creates new, then runs MongoDB aggregation pipeline to recalculate product's `avgRating`/`numReviews`
- **`deleteProduct`**: Iterates product images and deletes each from Cloudinary, then deletes product + associated reviews

### `orderController.js`
- **`createOrder`**: Most complex controller:
  1. Validates each item exists and has sufficient stock
  2. Calculates prices (respects `discountPrice`)
  3. Reduces stock atomically, marks `soldout` if stock hits 0
  4. Calculates delivery charge based on city match
  5. Creates order with buyer (or guest info)
  6. Creates Notification for each unique seller + emits Socket.IO event
  7. Sends styled email to buyer + each seller
- **`getSellerStats`**: Uses MongoDB aggregation pipeline for revenue calculations (total, today, by status)
- **`updateOrderStatus`**: Authorization check — sellers can only update their own orders, admins/superadmins can update any. Sends notification + email on status change
- **`updatePaymentStatus`**: Only for COD orders — sellers mark payment as received upon delivery
- **`downloadOrderPDF`**: Authorization check (buyer/seller/admin), then pipes PDFKit-generated invoice directly to response

### `adminController.js` — City-Scoped
- **All queries** use `req.user.assignedCity` with regex matching: `{ city: { $regex: city, $options: 'i' } }`
- **`getDashboard`**: Aggregates users, shops, products, orders, revenue (total+today), order status breakdown — all scoped to admin's city
- **`approveProduct`**: Toggles `isApproved`, creates notification for seller, emits Socket.IO event
- **`toggleUserStatus`**: Flips `isActive`, sends email notification, creates in-app notification

### `superAdminController.js` — Global
- **`getDashboard`**: Same aggregations as admin but **no city filter** (global), plus **city-wise statistics** — loops through `bangladeshCities` array and aggregates per-city data
- **Admin CRUD**: Create admin with assigned city, update (including password/email with duplicate check), delete
- **`updateSettings`**: Dynamic field updater — iterates field list and applies only provided fields
- **Banner management**: Add/remove hero banners with Cloudinary image upload/deletion

### `chatController.js`
- **`getOrCreateChat`**: Finds existing chat by `participants: { $all: [user1, user2] }` or creates new one
- **`getMyChats`**: Returns chats with computed `unreadCount` per chat using `lastReadAt` Map
- **`sendMessage`**: Pushes message to embedded array, updates `lastMessage`/`lastMessageAt`, emits via Socket.IO to chat room + notification to other participants
- **`getSafeIO()`**: Wraps `getIO()` in try/catch — returns null on Vercel where Socket.IO isn't initialized (prevents server crash)
- **Unread counting**: Uses `lastReadAt` Map — counts messages from other users with `createdAt > lastReadAt[userId]`

### `paymentController.js`
- **Stripe**: Creates `PaymentIntent` with amount in paisa (×100), BDT currency, order metadata
- **Mobile payments**: Records transaction ID, marks order as paid+confirmed
- **COD**: Simply confirms the order (payment status stays pending until seller marks paid)

### `notificationController.js`
- CRUD with `markRead`, `markAllRead` (bulk update), paginated list with `unreadCount`

---

## 6. Route Organization

### Route-Level Middleware Pattern
```javascript
// Admin routes — ALL routes behind protect + authorize
router.use(protect, authorize('admin'));
router.get('/dashboard', getDashboard);  // No per-route auth needed

// Product routes — mixed auth levels
router.get('/', optionalAuth, getProducts);     // Public (optional auth)
router.post('/', protect, upload.array('images', 5), createProduct);  // Auth required
```

### API Endpoints Summary
| Prefix | Auth | Description |
|---|---|---|
| `/api/auth` | Mixed | Register, login, admin login, Google OAuth, password reset |
| `/api/users` | `protect` | Profile, avatar, password, wishlist, public profiles |
| `/api/products` | Mixed | CRUD, search, reviews, categories |
| `/api/orders` | Mixed | Create (optionalAuth for guest), manage, PDF |
| `/api/admin` | `protect + authorize('admin')` | City-scoped management |
| `/api/superadmin` | `protect + authorize('superadmin')` | Global management |
| `/api/chat` | `protect` | Real-time messaging |
| `/api/notifications` | `protect` | Notification management |
| `/api/payment` | `optionalAuth` | Payment processing |
| `/api/settings/public` | None | Public site settings |

---

## 7. Utility Functions

### `utils/helpers.js`
- **`generateTokenAndCookie(user, res)`**: Creates JWT, sets HTTP-only cookie with environment-aware settings (secure/sameSite differ between dev/prod)
- **`generateResetToken()`**: Returns `{ token, hashed }` — raw token for email, hashed version for DB storage
- **`paginate(page, limit)`**: Calculates `skip`, `limit`, `page` with bounds clamping (max 50 per page)
- **`bangladeshCities`**: Array of 60+ Bangladesh cities — used for admin city assignment and city-wise analytics

### `utils/emailTemplates.js`
- 4 styled HTML email templates: `orderConfirmed`, `orderStatusUpdated`, `paymentConfirmed`, `newSellerNotification`
- Each uses template literals with dynamic data injection
- Professional styling with branded colors, responsive layout, CTA buttons

### `utils/pdfGenerator.js`
- Uses PDFKit to generate styled invoices
- Branded header with green gradient, company name
- Customer info + shipping address side-by-side layout
- Items table with alternating row colors
- Summary section with subtotal, delivery, total
- **Streamed to response**: `doc.pipe(res)` — no temp files, memory-efficient

---

## 8. Config Layer

### `config/db.js`
- `mongoose.connect()` with connection string from `MONGO_URI` env
- `process.exit(1)` on failure — fails fast instead of running with broken DB

### `config/cloudinary.js`
- Configures Cloudinary SDK with cloud name, API key, API secret from env vars

### `config/email.js`
- Creates Nodemailer transporter with SMTP config
- `sendEmail()` helper — returns `true/false` (non-throwing) so email failures don't crash order flows

### `config/socket.js`
- **Singleton pattern**: `initSocket(server)` creates Socket.IO instance, `getIO()` returns it
- **Room-based architecture**:
  - Each user joins their own room (userId) for targeted notifications
  - Chat rooms: `chat_{chatId}` for message broadcasting
- **Events**: `join`, `joinChat`, `sendMessage`, `typing`, `stopTyping`, `disconnect`

---

## 9. Frontend Architecture

### Entry Point (`index.js`)
```
BrowserRouter → GoogleOAuthProvider → AuthProvider → SocketProvider → App
```
- **Provider nesting order matters**: Socket needs Auth (to know user), Auth needs API client, Google OAuth wraps everything

### App Component (`App.js`)
- **Cart state** managed at App level (lifted state) — persisted to `localStorage` as `ag_cart`
- **Route layout split**:
  - Admin/SuperAdmin routes: no Navbar/Footer (standalone panels)
  - Public/User/Shop routes: wrapped in Navbar + Footer + ChatWidget + CookieConsent
- **Cart functions** (`addToCart`, `updateCartQty`, `clearCart`) passed as props to Cart, Checkout, ProductDetail

### Routing Strategy
- Nested `<Routes>` for admin/superadmin panels (wrapped in `<ProtectedRoute>`)
- Wildcard `path="*"` catches all non-admin routes and renders with layout
- `react-router-dom` v6 with declarative route definitions

---

## 10. State Management — Context API

### `AuthContext.js`
- **State**: `user`, `loading`, `isInitialized`, `isLoggingOut`
- **`checkAuth()`**: Called once on mount — checks for token in cookie/localStorage, verifies with `/auth/me` API call
- **Token dual storage**: `js-cookie` + `localStorage` — js-cookie for same-origin, localStorage for cross-origin fallback
- **`login(email, password, isAdmin)`**: Posts to appropriate endpoint, stores token in both storages, sets user immediately
- **`register(formData)`**: Same flow as login
- **`logout()`**: Calls `/auth/logout` API, clears both token storages, sets user null
- **Smart 401 handling**: Only clears token on explicit 401 response (not on network errors) to prevent logout on temporary connectivity issues

### `SocketContext.js`
- **Connection strategy**: Attempts Socket.IO first → falls back to HTTP polling
- **Socket config**: `reconnectionAttempts: 3`, `transports: ['websocket', 'polling']`, `reconnection: false` (prevents spam)
- **Polling fallback**: 1.5-second interval polling `/chat/unread` → dispatches `CustomEvent('chatUpdateFromPolling')` for UI reactivity
- **Mock socket**: When polling, creates mock object with same `emit/on/off/close` interface using `CustomEvent` — components don't need to know if using real Socket.IO or polling

---

## 11. Custom Hooks

### `useApi.js` — Centralized API Layer
- **`apiClient`** (Axios instance): `baseURL` from env, `withCredentials: true`
- **Request interceptor**: Attaches JWT token from js-cookie (fallback: localStorage) to `Authorization: Bearer` header
- **Response interceptor**: On 401 → clears tokens from all storages. Normalizes error to `{ message, status }`
- **`request(method, url, data, options)`**: Core method — handles JSON and FormData (auto-sets multipart headers), supports `params`, `showSuccess` (auto-toast), `silent` (suppress error toast)
- **Convenience methods**: `get`, `post`, `put`, `del` — wrap `request` with proper method
- **`downloadFile(url, filename)`**: Requests with `responseType: 'blob'`, creates object URL, triggers browser download via hidden `<a>` element — used for PDF invoice download

---

## 12. Component Architecture

### `ProtectedRoute.js` — Route Guard
- Waits for `isInitialized` before rendering (prevents flash of login page)
- If no user: redirects to appropriate login (admin → `/admin/login`, superadmin → `/superadmin/login`, others → `/login`)
- If wrong role: redirects to user's own dashboard (prevents cross-panel access)

### `ChatWidget.js` — Floating Chat
- Floating action button (bottom-right) with unread badge
- Two views: chat list and active conversation
- **Real-time sync**: Socket.IO events for new messages + unread updates, with polling fallback via `CustomEvent` listener
- **Optimistic UI**: Message added to local state immediately before API confirms
- **Auto-scroll**: `useRef` on message end element with `scrollIntoView({ behavior: 'smooth' })`
- **Unread tracking**: Per-chat unread counts with visual indicators (blue highlight, bold text, count badge)

### `NotificationBell.js` — Navbar Notifications
- Dropdown with notifications list, unread badge
- Socket.IO listener for real-time notification events
- "Mark all read" bulk action
- Relative time formatting (Just now, 5m ago, 2h ago, 3d ago)
- Click-outside-to-close via `useRef` + `mousedown` event listener

### `ProductCard.js` — Reusable Product Card
- Displays image, title, price (with discount strike-through), rating, city, seller info
- Link to product detail page using `publicId`

### `SkeletonLoader.js` — Loading States
- CSS-animated placeholder cards for loading states
- Configurable `type` and `count`

### `ShopPanelLayout.js` / `UserPanelLayout.js` — Dashboard Layouts
- Sidebar navigation with active link highlighting
- Responsive — collapses on mobile
- Wraps panel page content

---

## 13. Real-Time Communication

### Socket.IO Architecture
```
Client connects → joins personal room (userId) → receives targeted events
Client opens chat → joins chat room (chat_{chatId}) → receives messages
Server emits:
  - 'notification' → to userId room (order, payment, approval events)
  - 'newMessage' → to chat room (new messages)
  - 'unreadCountUpdate' → to userId room (unread count changes)
  - 'userTyping'/'userStopTyping' → to chat room
```

### Polling Fallback (Vercel)
```
SocketContext detects connect_error → sets usePolling = true
→ setInterval(1500ms) polls GET /chat/unread
→ dispatches CustomEvent('chatUpdateFromPolling')
→ ChatWidget/NotificationBell listen for CustomEvent
→ UI updates as if real-time
```

### Why this dual approach?
Vercel serverless functions are stateless — each request may hit a different instance, so persistent WebSocket connections are impossible. The polling fallback provides near-real-time experience (1.5s delay) while keeping the same component API via the mock socket interface.

---

## 14. Deployment Strategy

### Server (`vercel.json`)
```json
{
  "builds": [{ "src": "api/index.js", "use": "@vercel/node" }],
  "routes": [{ "src": "/(.*)", "dest": "api/index.js" }]
}
```
All requests routed to the Express app exported from `api/index.js`.

### Client (`vercel.json`)
```json
{
  "routes": [
    { "src": "^/static/(.*)$", "dest": "/static/$1", "headers": { "cache-control": "public, max-age=31536000" } },
    { "src": "^/(.*\\.[a-z0-9]+)$", "dest": "/$1" },
    { "src": "^/(.*)$", "dest": "/index.html" }
  ]
}
```
- Static assets: 1-year cache headers
- Known files: served directly
- Everything else: SPA fallback to `index.html` (client-side routing)

### Environment Variables
- Server: `MONGO_URI`, `JWT_SECRET`, `JWT_EXPIRE`, `CLIENT_URL`, `CLOUDINARY_*`, `SMTP_*`, `STRIPE_SECRET_KEY`, `GOOGLE_CLIENT_ID/SECRET`, `COOKIE_DOMAIN`
- Client: `REACT_APP_API_URL`, `REACT_APP_SOCKET_URL`, `REACT_APP_GOOGLE_CLIENT_ID`
