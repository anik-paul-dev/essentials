# BD-MarketPlace — Interview Q&A Preparation

> **How to use:** Read each question, then practice answering in your own words using the provided answer as a guide. Focus on the "why" — interviewers care more about reasoning than memorization.

---

## Section 1: Project Overview

### Q1: What is BD-MarketPlace? Explain the project.
**A:** BD-MarketPlace is a full-stack city-based e-commerce marketplace I built for Bangladesh. It allows local buyers to purchase products from sellers and shops in their city. It supports 4 user roles — User, Shop, Admin, and SuperAdmin — each with their own panel. Users can buy products, sellers can list products, admins manage their assigned city, and the superadmin has global control including site settings and admin management. It features real-time chat, multiple payment methods (Stripe, bKash, Nagad, Rocket, COD), email notifications, PDF invoices, and Google OAuth login.

### Q2: What tech stack did you use and why?
**A:** I used the MERN stack — MongoDB, Express.js, React, and Node.js. MongoDB because it's flexible for marketplace data with varying product schemas and embedded documents like chat messages. Express.js for the REST API because it's lightweight and has a huge middleware ecosystem. React for the SPA frontend because of its component-based architecture and ecosystem (React Router, Context API). Node.js ties everything together with JavaScript on both ends. I also used Socket.IO for real-time chat, Cloudinary for image hosting, Stripe for payments, and Nodemailer for emails.

### Q3: How many panels does the website have? What does each do?
**A:** Five panels:
1. **Public Storefront** — Browse products, search, filter by city/category, cart, guest checkout
2. **User Panel** — Dashboard, orders, sell products (C2C), manage profile, wishlist
3. **Shop Panel** — Product CRUD, order management, revenue stats, shop profile
4. **Admin Panel** — City-scoped: manage users/shops/products/orders only in their assigned city
5. **SuperAdmin Panel** — Global: everything admin can do plus manage admins, site settings, policies, city-wise analytics

### Q4: What's the role-based access control (RBAC) system?
**A:** I implemented 4 roles: `user`, `shop`, `admin`, `superadmin`. On the backend, I have an `authorize(...roles)` middleware that checks `req.user.role` against allowed roles. It's a higher-order function — `authorize('admin')` returns a middleware that blocks non-admin users with a 403 error. On the frontend, I have a `ProtectedRoute` component that checks the user's role and redirects to the appropriate login page or dashboard if they don't have access.

---

## Section 2: Authentication & Security

### Q5: How did you implement authentication?
**A:** JWT-based stateless authentication. On login/register, the server generates a JWT with the user's `_id` and `role`, signs it with a secret, and sends it in both an HTTP-only cookie and the response body. The frontend stores the token in js-cookie and localStorage as a dual strategy. On every request, my Axios interceptor attaches the token to the `Authorization: Bearer` header. The `protect` middleware on the server extracts the token from either the cookie or the header, verifies it, fetches the user from the database, and attaches it to `req.user`.

### Q6: Why do you store the token in both cookies and localStorage?
**A:** Because of cross-origin deployment challenges. When the frontend and backend are on different Vercel domains, browsers may not send HTTP-only cookies due to SameSite policies. The Authorization header with a token from localStorage works as a fallback. The cookie is still the primary method because it's HTTP-only (safer from XSS), but localStorage ensures authentication works across all deployment scenarios.

### Q7: How does your password reset flow work?
**A:** When a user requests a password reset, I generate a cryptographically random 32-byte token using Node's `crypto.randomBytes()`. I SHA-256 hash this token and store the hash in the database along with a 30-minute expiry timestamp. The raw token is sent in the reset email link. When the user clicks the link and submits a new password, I hash the URL token again and match it against the stored hash. If it matches and hasn't expired, I update the password and clear the reset token fields.

### Q8: How do you handle security?
**A:** Multiple layers:
- **Password hashing** with bcryptjs (10 salt rounds) via Mongoose pre-save hook
- **Helmet** for HTTP security headers (XSS, clickjacking, MIME sniffing protection)
- **Rate limiting** — 3 tiers: 200 req/15min general, 20 for auth, 30 for uploads
- **CORS** with origin whitelist and credentials support
- **Public IDs** — MongoDB `_id` is never exposed to clients; I use nanoid-generated `publicId` instead
- **Input validation** at model level with Mongoose validators
- **Account status check** — `isActive` flag verified on every authenticated request

### Q9: Why do you have separate login endpoints for admin and regular users?
**A:** For security isolation. The `/auth/login` endpoint only queries users with `role: 'user'` or `'shop'`. The `/auth/admin/login` endpoint only queries `role: 'admin'` or `'superadmin'`. This prevents a regular user from accidentally or maliciously attempting to access admin functionality, and provides role-specific error messages.

### Q10: How does Google OAuth work in your project?
**A:** I implemented two approaches. The primary one is a token-based flow: the frontend uses `@react-oauth/google` to get an `access_token` from Google, sends it to my `/auth/google/token` endpoint. My server verifies this token by calling Google's userinfo API, then finds or creates the user, and generates a JWT. I also have a Passport.js redirect-based flow as a fallback. The Google OAuth strategy only initializes if `GOOGLE_CLIENT_ID` is set in env — so it degrades gracefully if not configured.

---

## Section 3: Database & Models

### Q11: Why MongoDB and not SQL?
**A:** MongoDB fits marketplace data well because product schemas can vary (different categories have different attributes), embedded documents work great for chat messages and order items, and the flexible schema makes rapid iteration easy. MongoDB's aggregation pipeline is powerful for analytics (revenue calculations, city-wise stats). Also, MongoDB Atlas provides easy cloud deployment with automatic scaling.

### Q12: Explain your Order model design.
**A:** The Order model has a custom `orderId` (format: `ORD-{NANOID}`) for human readability. It supports both authenticated and guest orders — `buyer` is nullable, with `isGuest` flag and `guestInfo` embedded subdocument. Order items are denormalized — I store `title`, `price`, `image` directly in the order, not just the product reference. This ensures order history survives even if products are deleted. It tracks `paymentMethod` (5 options), `paymentStatus` (pending/paid/failed/refunded), `orderStatus` (6 stages), and `orderCity` for city-scoped admin queries.

### Q13: Why did you embed chat messages instead of a separate collection?
**A:** For marketplace chat, conversations are typically short (buyer asking about a product). Embedding avoids extra collection joins on every message fetch and simplifies real-time updates — I just push to the embedded array. The `lastReadAt` Map field tracks when each participant last read the chat, enabling efficient unread count calculation without a separate read-receipts collection.

### Q14: How do you handle product reviews and ratings?
**A:** I have a separate Review model with a compound unique index on `{ product, user }` — this enforces one review per user per product at the database level. When a review is submitted, I use upsert logic: if the user already reviewed, I update it; otherwise, I create new. After each review, I run a MongoDB aggregation pipeline (`$avg` on ratings, `$sum` for count) and update the product's `avgRating` and `numReviews` fields for fast display without recalculating on every product fetch.

### Q15: What is the `publicId` pattern and why?
**A:** Every User and Product has a `publicId` generated by nanoid (12 characters, lowercase alphanumeric). I never expose MongoDB's `_id` to the client. This provides security (ObjectIDs reveal creation time), shorter URLs, and prevents enumeration attacks. All API endpoints and frontend routes use `publicId` for lookups.

---

## Section 4: API Architecture

### Q16: Explain your middleware pipeline.
**A:** Requests flow through: Helmet (security headers) → CORS (origin validation) → `express.json` (10MB limit for image base64) → URL parser → Cookie parser → General rate limiter → Route handlers → Centralized error handler. Each middleware serves a specific purpose, and the order matters — security middlewares come first, parsing next, then rate limiting before route handlers.

### Q17: How does your centralized error handler work?
**A:** Every controller uses `try/catch` with `next(error)`. My `errorHandler` middleware at the end of the Express pipeline catches all errors and normalizes them. It specifically handles Mongoose errors: CastError → 404, duplicate key (code 11000) → 400 with field name, ValidationError → 400 with joined messages. JWT errors get 401. Everything else gets 500. The response format is always `{ success: false, message }` — consistent for the frontend to parse.

### Q18: How do you handle pagination?
**A:** I have a `paginate(page, limit)` helper that calculates `skip`, `limit`, and `page` values. It clamps the limit to max 50 (prevents huge queries) and ensures page is at least 1. Every list endpoint returns `{ data, page, totalPages, total }`. The frontend passes `?page=2&limit=12` query parameters.

### Q19: How does product search and filtering work?
**A:** The `getProducts` controller builds a dynamic MongoDB query object:
- **Text search**: `$text: { $search: query }` — uses the text index on title, description, tags
- **Category**: Finds the Category document by name (regex), then filters by its `_id`
- **City/Subcategory**: Case-insensitive regex match
- **Price range**: `$gte` and `$lte` operators
- **Sort**: Maps sort parameter to MongoDB sort object (price_low, price_high, rating, popular)
All filters are optional — only applied if the query parameter exists.

### Q20: How does stock management work?
**A:** When an order is placed, I iterate through each item, check if `product.stock >= item.quantity`, and return a 400 error with the specific product name if insufficient. Then I reduce stock atomically: `product.stock -= item.quantity`. If stock hits 0, I set `product.status = 'soldout'`. This happens inside the order creation controller, before the order is saved.

---

## Section 5: Real-Time Features

### Q21: How does the real-time chat work?
**A:** I use Socket.IO for real-time messaging. When a user opens the app, the frontend connects to Socket.IO and joins a personal room (their userId). When they open a specific chat, they join the chat room (`chat_{chatId}`). When a message is sent, the controller pushes it to the embedded messages array, saves, and emits the message to the chat room via `io.to(chat_${chatId}).emit('newMessage', msg)`. The sender also gets notified via their personal room for unread count updates.

### Q22: How do you handle real-time on Vercel serverless?
**A:** Vercel serverless functions are stateless — they can't maintain WebSocket connections. So I built a dual-mode system. The `SocketContext` on the frontend first tries to connect via Socket.IO. If it gets a `connect_error`, it sets `usePolling = true` and starts an HTTP polling interval (every 1.5 seconds) that calls `GET /chat/unread`. Updates are dispatched via browser `CustomEvent`. I also created a mock socket object that has the same `emit/on/off` interface but uses CustomEvents underneath — so components don't need to know if they're using real Socket.IO or polling.

### Q23: How do notifications work?
**A:** When events happen (new order, status change, product approval), the controller creates a Notification document in MongoDB and emits a Socket.IO event to the target user's room. The `NotificationBell` component on the frontend listens for these events and refreshes the notification list. It shows a badge with unread count, a dropdown with recent notifications, and supports "mark all read". Each notification has a `link` field for deep navigation when clicked.

---

## Section 6: Payment Integration

### Q24: What payment methods did you integrate?
**A:** Five methods: Stripe (card payments), bKash, Nagad, Rocket (mobile banking), and Cash on Delivery (COD). Stripe uses the PaymentIntent API — I create an intent on the server with amount in paisa (BDT × 100), get a client secret, and confirm after payment. Mobile payments accept a transaction ID for verification. COD creates the order with pending payment — the seller marks it as paid upon delivery.

### Q25: How does the order + payment flow work together?
**A:** 1) User submits checkout form → `POST /orders` creates the order with `paymentStatus: 'pending'`. 2) Based on payment method, a second API call is made: Stripe → creates PaymentIntent then confirms, mobile → records TxnID and marks paid, COD → simply confirms the order. 3) Seller can later update payment status for COD orders via `PUT /orders/:orderId/payment-status`. This two-step approach ensures the order is always created, even if payment processing has issues.

---

## Section 7: Frontend Patterns

### Q26: How do you manage state in the frontend?
**A:** I use React Context API for global state (AuthContext for user auth, SocketContext for real-time connections) and local component state (`useState`) for page-specific data. Cart state is managed at the App component level and persisted to localStorage. I chose Context over Redux because the state is relatively simple — authentication and socket connections are the only truly global concerns.

### Q27: Explain your custom `useApi` hook.
**A:** It's a centralized API layer that wraps Axios. It provides `get`, `post`, `put`, `del`, and `downloadFile` methods. Each method handles loading state, error state, and auto-toasts for success/error messages. The Axios instance has interceptors: request interceptor attaches the JWT token, response interceptor handles 401 errors by clearing tokens. It supports `silent` mode (no error toasts) and `showSuccess` mode (auto success toast). For file downloads (PDF invoices), it requests with `responseType: 'blob'` and triggers a browser download via a hidden anchor element.

### Q28: How does the ProtectedRoute component work?
**A:** It waits for `isInitialized` from AuthContext (prevents flash of login page during initial token check). If no user is authenticated, it redirects to the appropriate login page based on the required role. If the user has the wrong role (e.g., a user trying to access admin panel), it redirects them to their own dashboard. This prevents both unauthorized access and confusing navigation.

### Q29: How do you handle the cart without a backend cart API?
**A:** The cart is entirely client-side using React state + localStorage. The `addToCart`, `updateCartQty`, and `clearCart` functions are defined in App.js and passed as props. Cart data is stored as `ag_cart` in localStorage and loaded on initial render. This approach is simpler, works for guest users without authentication, and reduces server load. The cart only interacts with the backend during checkout when the order is created.

### Q30: How does your file upload work on the frontend?
**A:** For product images, I use `<input type="file" multiple>` with `accept="image/*"`. The files are sent as `FormData` via Axios. My `useApi` hook detects `FormData` and automatically sets the `Content-Type` to `multipart/form-data`. On the server, Multer parses the multipart data and CloudinaryStorage streams files directly to Cloudinary. The Cloudinary response provides the image URL and public ID, which I store in the product document.

---

## Section 8: Admin System

### Q31: How does city-scoped admin management work?
**A:** Each admin has an `assignedCity` field. In every admin controller function, I use `req.user.assignedCity` to scope all queries. For example, `getUsers` queries `{ role: 'user', 'address.city': { $regex: city, $options: 'i' } }`. The regex with case-insensitive flag handles variations in city name capitalization. This means an admin in Chittagong can only see users, shops, products, and orders related to Chittagong.

### Q32: How does the SuperAdmin dashboard calculate city-wise analytics?
**A:** The `getDashboard` controller loops through the `bangladeshCities` array (60+ cities) and runs aggregation queries for each: order count, shop count, product count, and revenue. This gives a per-city breakdown of marketplace activity. It also calculates global totals (all users, shops, products, orders) and today's revenue using date-range aggregation with `$gte` (start of day) and `$lt` (start of next day).

### Q33: How are site settings managed?
**A:** The SiteSettings model is a singleton — only one document exists. The public endpoint `GET /api/settings/public` returns it (creates with defaults if missing). The SuperAdmin can update all fields via `PUT /api/superadmin/settings`. I use a dynamic update approach: I define an array of allowed field names and loop through them, applying only fields that exist in `req.body`. This avoids overwriting fields that weren't included in the request.

---

## Section 9: Email System

### Q34: How does the email system work?
**A:** I use Nodemailer with SMTP configuration. The `sendEmail()` function is async but returns `true/false` instead of throwing — so email failures don't crash order or registration flows. I have 4 styled HTML email templates for order confirmation, status updates, payment confirmation, and seller notifications. Each template uses JavaScript template literals for dynamic data injection. Emails are triggered from controllers after key events (registration, order creation, status change).

### Q35: How do you generate PDF invoices?
**A:** I use PDFKit on the server side. The `createOrderPDF` function creates a new PDF document, draws branded headers, customer/shipping info, an items table with alternating row colors, and a summary section. Instead of saving to a file, I pipe the PDF directly to the HTTP response: `doc.pipe(res)` with `Content-Type: application/pdf` header. On the frontend, I use my `useApi.downloadFile()` method which requests with `responseType: 'blob'` and triggers a browser download.

---

## Section 10: Deployment & DevOps

### Q36: How is the project deployed?
**A:** Both frontend and backend are deployed on Vercel. The frontend is a standard React SPA build with client-side routing fallback (`/index.html` for all unmatched routes). The backend uses Vercel's serverless function runtime — `api/index.js` exports the Express app, and `vercel.json` routes all requests to it via `@vercel/node`. MongoDB is on MongoDB Atlas (cloud), and images are on Cloudinary CDN.

### Q37: Why do you have two server entry points?
**A:** `server.js` is for local development — it creates an HTTP server, initializes Socket.IO, and listens on a port. Socket.IO requires a persistent server process. `api/index.js` is for Vercel — it exports the Express app as a module (no `server.listen()`). Vercel wraps it as a serverless function. Socket.IO can't work in serverless, so the frontend falls back to HTTP polling.

---

## Section 11: Error Handling & Edge Cases

### Q38: How do you handle errors across the application?
**A:** **Backend**: Every controller wraps logic in `try/catch` and passes errors to `next(error)`. A centralized error handler normalizes all errors (Mongoose, JWT, generic) into `{ success: false, message }`. **Frontend**: The `useApi` hook catches errors, shows toast notifications (unless `silent` mode), and returns error state. The Axios response interceptor handles 401 errors globally by clearing tokens.

### Q39: How do you prevent the app from breaking under load?
**A:** Rate limiting prevents DDoS (200 requests per 15 minutes per IP). MongoDB connection pooling handles concurrent database connections. Cloudinary handles image serving (CDN offloads static content from my server). The serverless architecture on Vercel auto-scales functions based on demand. Error handling ensures one failed request doesn't crash the server — `next(error)` prevents unhandled promise rejections.

### Q40: How do you handle guest checkout?
**A:** The Order model has `buyer` as nullable and an `isGuest` boolean. The checkout route uses `optionalAuth` middleware — it sets `req.user` if a token exists but doesn't block guests. In the controller, I check `req.user ? req.user._id : null` for the buyer field and store guest info (name, email, phone) in the `guestInfo` subdocument. Email notifications go to `guestInfo.email` for guest orders.

---

## Section 12: Scenario-Based Questions

### Q41: A user reports they can't log in after deployment. How would you debug?
**A:** First, I'd check if the token is being sent — open browser DevTools, check the Network tab for the login response (does it contain a token?). Then check if the token is being stored — look at Application tab for cookies and localStorage. Then check subsequent requests — does the Authorization header have the token? If it's a cookie issue, I'd check SameSite settings (must be 'none' for cross-origin with secure:true). If it's a CORS issue, I'd verify the `CLIENT_URL` env var matches the actual frontend domain.

### Q42: How would you add a new payment method?
**A:** 1) Add the new value to the Order model's `paymentMethod` enum array. 2) Create a new controller function in `paymentController.js` similar to `mobilePayment`. 3) Add a new route in `paymentRoutes.js`. 4) Add a new payment option card in the Checkout component on the frontend. 5) Handle the payment confirmation flow in `handleSubmit`. The architecture is designed to make adding payment methods straightforward.

### Q43: How would you optimize the SuperAdmin dashboard if it's slow?
**A:** The current implementation runs multiple aggregation queries including per-city loops. To optimize: 1) Cache the city-wise stats with a TTL (Redis or in-memory cache). 2) Use a single aggregation pipeline with `$facet` for multiple aggregations in one query. 3) Pre-compute stats in a separate collection using MongoDB change streams or a scheduled job. 4) Add pagination or lazy-loading for the city stats section.

### Q44: What happens if Cloudinary is down when a user uploads?
**A:** The Multer-CloudinaryStorage pipeline would throw an error, which gets caught by the controller's try/catch and passed to the error handler. The user would see a toast error message. The product/avatar wouldn't be updated because the save only happens after successful upload. The error handler would return a 500 with a descriptive message. No partial data is left in an inconsistent state.

### Q45: How do you ensure order data survives product deletion?
**A:** I denormalize order item data — when an order is created, I copy the product's `title`, `price`, `image` directly into the order item subdocument, not just the product reference. So even if the product is later deleted, the order still has all the information needed for display and invoice generation.

---

## Section 13: Code Quality & Patterns

### Q46: What design patterns did you use?
**A:** 
- **MVC**: Models (Mongoose schemas), Controllers (business logic), Routes (Express routing)
- **Middleware chain**: Authentication, authorization, rate limiting, error handling as composable middleware
- **Singleton**: Socket.IO instance via `initSocket`/`getIO`, SiteSettings model
- **Provider pattern**: React Context API for Auth and Socket state
- **Interceptor pattern**: Axios request/response interceptors for auth and error handling
- **Strategy pattern**: Payment processing (different handlers for Stripe, mobile, COD)
- **Observer pattern**: Socket.IO event listeners for real-time updates

### Q47: How do you handle code organization?
**A:** Clear separation of concerns:
- `models/` — Data schemas and database logic
- `controllers/` — Business logic per domain (auth, product, order, admin, etc.)
- `routes/` — Route definitions with middleware chains
- `middleware/` — Reusable cross-cutting concerns (auth, upload, error, rate limiting)
- `utils/` — Pure helper functions (pagination, token generation, email templates, PDF)
- `config/` — External service configuration (DB, Cloudinary, email, Socket.IO)

### Q48: How does your frontend handle loading states?
**A:** The `useApi` hook manages loading state automatically — sets `loading = true` before request, `false` after (in `finally` block). Components use this for button disabled states and loading spinners. I also have a `SkeletonLoader` component for card-shaped loading placeholders. The `ProtectedRoute` shows "Initializing..." until the auth check completes, preventing flash of wrong content.

---

## Section 14: Quick-Fire Technical Questions

### Q49: What is `optionalAuth` and where do you use it?
**A:** It's middleware that sets `req.user` if a valid token exists but doesn't block unauthenticated requests. I use it for product listing (could personalize results for logged-in users), product detail viewing, and checkout (supports both guest and authenticated checkout).

### Q50: How do you handle file deletion when updating images?
**A:** When a product image is deleted or an avatar is replaced, I call `deleteFromCloudinary(publicId)` which uses Cloudinary's `uploader.destroy()` API. For product image deletion, the controller removes the image from the product's `images` array and saves. For avatar updates, I delete the old avatar before uploading the new one. The `deleteFromCloudinary` function catches errors silently to prevent blocking the main operation.

### Q51: How does the text search work in MongoDB?
**A:** I created a text index on the Product model: `productSchema.index({ title: 'text', description: 'text', tags: 'text' })`. When a search query comes in, I use `$text: { $search: searchTerm }` which performs MongoDB's built-in full-text search across all three indexed fields. It handles stemming and stop words automatically.

### Q52: How do you calculate delivery charges?
**A:** The SiteSettings model has `deliveryCharges.insideCity` (default ₹60) and `deliveryCharges.outsideCity` (default ₹120). In the order controller, I compare the shipping city with the first item's city to determine inside/outside. Currently, the frontend hardcodes ₹60 as default, but it could be made dynamic by fetching settings.

### Q53: What happens if Socket.IO connection fails?
**A:** The SocketContext has `reconnectionAttempts: 3` and `reconnection: false` (prevents reconnection spam). On `connect_error`, it sets `usePolling = true` and creates a fallback polling interval. The mock socket object maintains the same API interface, so components don't crash. Chat still works through HTTP APIs — the real-time part just becomes 1.5-second polling instead of instant WebSocket.

### Q54: How do you prevent duplicate reviews?
**A:** At the database level with a compound unique index: `reviewSchema.index({ product: 1, user: 1 }, { unique: true })`. If a user tries to create a duplicate, the controller first checks with `findOne`, and if found, updates instead of creating. This gives a clean upsert behavior without relying solely on the database constraint.

### Q55: How does the Notification system differ from Chat?
**A:** Notifications are one-way, server-to-user — they're created by controllers when events happen (order placed, status changed, product approved). Chat is two-way, user-to-user — it requires real-time message exchange. Notifications are displayed in a dropdown bell in the navbar; chat is a floating widget at the bottom. Both use Socket.IO for real-time delivery but serve different purposes.

---

## Section 15: Architecture Decision Questions

### Q56: Why Context API over Redux?
**A:** The global state in this app is minimal — just authentication data and socket connections. Redux would add unnecessary boilerplate (actions, reducers, store setup). Context API with hooks provides the same functionality with less code. Each page fetches its own data locally via `useApi`, so there's no complex shared state that would benefit from Redux's centralized store.

### Q57: Why did you choose Cloudinary over storing images locally?
**A:** Local file storage doesn't work with serverless deployment (Vercel functions have ephemeral filesystems). Cloudinary provides CDN delivery (fast globally), automatic image optimization (width limiting, quality auto), persistent storage, and easy deletion via API. The `multer-storage-cloudinary` package streams uploads directly to Cloudinary without touching the server's filesystem.

### Q58: Why Vercel for deployment?
**A:** Vercel offers: free tier for both frontend and backend, automatic HTTPS, global CDN for the SPA, serverless functions for the API (auto-scaling), and easy environment variable management. The trade-off is no persistent WebSocket support — which I solved with the polling fallback system.

### Q59: How would you scale this application?
**A:** 1) Add Redis for caching frequently accessed data (settings, categories, dashboard stats). 2) Use MongoDB indexes more aggressively (compound indexes for common query patterns). 3) Move to a dedicated server (AWS EC2 or DigitalOcean) for persistent Socket.IO connections. 4) Implement image lazy-loading and pagination throughout. 5) Add a CDN for the frontend. 6) Use MongoDB's read replicas for analytics queries to not burden the primary.

### Q60: If you built this again, what would you change?
**A:** I'd use TypeScript for type safety on both frontend and backend. I'd use Next.js instead of Create React App for SSR (better SEO for product pages). I'd implement WebSocket on a separate service (like a dedicated Socket.IO server on Railway or Render) instead of the polling fallback. I'd also add comprehensive unit and integration tests with Jest, and implement a proper caching layer with Redis.
