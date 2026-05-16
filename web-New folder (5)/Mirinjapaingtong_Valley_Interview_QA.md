# Mirinjapaingtong Valley — Interview Q&A Preparation

> Prepare these questions and answers so you can confidently explain every part of your resort booking website in an interview.

---

## Section 1: Project Overview Questions

### Q1: Tell me about this project. What is it and who is it for?
**A:** This is a full-stack Resort Booking Website called "Mirinjapaingtong Valley" that I developed as a paid client project. It's built for a real resort in Lama, Bandarban, Bangladesh. The platform allows guests to browse rooms, check availability, and submit booking requests online, while giving the resort owner a complete admin dashboard to manage rooms, bookings, users, content, emails, reviews, and analytics. It's a production website deployed on Vercel.

### Q2: What tech stack did you use and why?
**A:** I used the **MERN stack** — MongoDB, Express.js, React, and Node.js. I chose MongoDB because the resort data (rooms, bookings, users) has flexible schemas — for example, rooms have variable numbers of images and availability slots, which fits well with MongoDB's document model. React with Vite gives fast development and excellent SPA performance. Express is lightweight and perfect for building RESTful APIs. For deployment, I used Vercel because it supports both static frontend hosting and serverless Node.js functions.

### Q3: How many panels does this website have?
**A:** Three panels:
1. **Public website** — For guests: home page, room browsing with filters, room details with availability calendar, booking workflow, facilities, menu, contact, about page
2. **User panel** — For authenticated guests: dashboard with booking stats, profile management, booking management with cancellation, wishlist
3. **Admin panel** — For the resort owner: complete dashboard with analytics, CRUD management for all content, booking operations, user management, email center, visitor analytics, site settings

---

## Section 2: Architecture & Backend Questions

### Q4: Explain your project structure. Why did you organize it this way?
**A:** I separated frontend and backend into independent directories, each deployed separately on Vercel. The backend follows a modular structure: `config/` for database and Cloudinary setup, `middleware/` for auth and admin guards, `models/` for 13 Mongoose schemas, `routes/` for 16 route modules organized by resource, and `utils/` for shared utilities like email and validation. I didn't use a separate controllers directory because for this project size, keeping route definitions and business logic together reduces complexity. Each route file acts as its own controller.

### Q5: How does your middleware chain work in server.js?
**A:** The middleware runs in this exact order — and order matters:
1. **Helmet** first — sets secure HTTP headers on every response immediately
2. **CORS** — restricts API access to only the production frontend domain
3. **express.json() + urlencoded()** — parses request bodies so route handlers can read them
4. **Rate limiter** — 10,000 requests per 15-minute window per IP to prevent abuse

Then all 16 route groups are mounted under `/api/` prefixed paths.

### Q6: How does your authentication middleware work?
**A:** My `auth.js` middleware does four things:
1. Extracts the JWT token from the `Authorization: Bearer <token>` header
2. Verifies the token using `jwt.verify()` with the secret key — if tampered, it throws an error
3. Looks up the user in the database — this is important because even with a valid JWT, if the admin has deactivated the user, access should be denied
4. Attaches the full user document to `req.user` so downstream handlers can use it

I do the DB lookup on every request instead of just trusting the JWT payload because the user's active status might change between when the token was issued and when it's used.

### Q7: How does the admin middleware work with the auth middleware?
**A:** I use **middleware chaining**. For admin-protected routes, I write: `router.get('/', auth, admin, handler)`. The `auth` middleware runs first, verifies the JWT, and populates `req.user`. Then the `admin` middleware checks if `req.user.role === 'admin'`. If not, it returns 403. This is composable — each middleware has a single responsibility.

### Q8: Explain your database schema design decisions.
**A:** Key decisions:
- **User model** has pre-save hooks that hash the password with bcrypt (12 salt rounds). The `isModified('password')` check prevents re-hashing on non-password updates. I also added a `pre('findOneAndUpdate')` hook for admin password resets.
- **Room model** stores availability as a subdocument array `[{ from, to, bookedBy }]`. This embeds booking dates directly in the room document for fast overlap queries without joins.
- **Content and SiteSetting** use the singleton pattern — only one document in each collection, fetched with `findOne()`. The GET endpoint auto-creates with defaults if the document doesn't exist.
- **VisitAnalytics** has a compound unique index on `{ date, city, country }` to prevent duplicate entries for the same location on the same day.

### Q9: Why did you embed availability inside the Room document instead of using a separate collection?
**A:** For a resort with a limited number of rooms (maybe 10-20), embedding availability directly means I can check for booking conflicts with a single query — no joins needed. When I need to check if a room is available for specific dates, I just look at the room's `availability` array. The trade-off is that very heavily booked rooms might have large arrays, but for a small resort this is negligible, and the read performance gain is significant.

### Q10: How do you handle input validation?
**A:** I use **Joi** for server-side schema validation. I have three schemas: `userSchema`, `bookingSchema`, and `roomSchema`. Key validations include:
- Phone numbers validated against a regex supporting multiple Asian country codes (+88, +91, etc.)
- Booking `checkOut` validated with `Joi.date().greater(Joi.ref('checkIn'))` — it must be after check-in
- Room schema has a custom validator ensuring `maxAdults + maxChildren` doesn't exceed `totalGuests`
- User date of birth must be in the past: `Joi.date().less('now')`
- Registration uses `abortEarly: false` to return ALL validation errors at once, not just the first one

---

## Section 3: Booking System Logic

### Q11: Walk me through the complete booking flow.
**A:** 
1. **Guest browses rooms** → filters by price, guests, facilities, features, dates
2. **Clicks "Book Now"** → redirected to booking page (must be logged in)
3. **Fills booking form** → personal info, dates (with DatePicker), guest count, payment method (bKash/Nagad/Upai)
4. **Client-side validation** → form validation + availability check against room data already loaded
5. **Submits** → POST `/api/bookings` → server validates with Joi, re-checks availability on the room, creates booking with status `pending`
6. **Email sent** → branded HTML email with booking details and advance payment instructions
7. **Admin sees pending booking** → sidebar badge shows count, reviews the booking
8. **Admin confirms** → status changes to `confirmed`, date range pushed to room's availability array, confirmation email sent to guest
9. **Or cancels** → availability slot removed, cancellation email sent

### Q12: How does your room availability/overlap detection work?
**A:** On the **backend**, I check overlap with this logic:
```javascript
const overlap = room.availability.some(slot => {
  return !(new Date(checkOut) <= new Date(slot.from) || new Date(checkIn) >= new Date(slot.to));
});
```
Two date ranges DON'T overlap only if one ends before the other starts. I negate this — if the negation is true for any existing slot, there IS an overlap and the room is unavailable.

On the **frontend**, I build a Set of all booked date keys (YYYY-MM-DD format) from the room's availability data, then check each day in the requested range against this set. The calendar component uses `tileClassName` to visually color-code days as booked (orange) or available (teal).

### Q13: What happens when a user cancels a booking?
**A:** Three conditions must be met:
1. The booking must be `pending` status — confirmed bookings can only be cancelled by admin
2. The booking must belong to the requesting user (`booking.user === req.user._id`)
3. The cancellation must be within 24 hours of booking time — I calculate `(now - bookingTime) / (1000 * 60 * 60)` and reject if > 24

If all conditions pass, status is set to `cancelled` and a cancellation email is sent. Since the booking was only `pending` (never confirmed), no availability slot needs to be removed from the room.

### Q14: How do you handle the booking confirmation on the admin side?
**A:** When admin changes status to `confirmed`:
1. The date range `{ from: checkIn, to: checkOut, bookedBy: userId }` is pushed to the room's `availability` array
2. The room is saved
3. A confirmation email with full booking and payment details is sent to the guest

When admin cancels:
1. The matching availability slot is filtered out: `room.availability.filter(slot => !(slot.bookedBy matches && slot.from matches))`
2. Room saved, cancellation email sent

### Q15: How do you prevent double booking?
**A:** Three layers of protection:
1. **Frontend check**: Client-side availability check runs when the user fills the form — disables the submit button if dates overlap
2. **Backend validation**: Server re-checks overlap against the room's latest availability data before creating the booking
3. **Pending status**: New bookings start as `pending` — the availability array is only updated when admin confirms, so the admin has control

---

## Section 4: Frontend Questions

### Q16: How does your authentication work on the frontend?
**A:** I use React Context API with a custom `useAuth` hook. The `AuthProvider` wraps the entire app in `main.jsx`. On mount, it checks localStorage for a JWT token. If found, it calls `GET /auth/me` to verify the token and get user data. If the token is invalid (expired or tampered), it clears localStorage and shows a "Session expired" toast.

The `login` function posts credentials, stores the returned JWT in localStorage, then immediately fetches `/auth/me` to get full user profile data. I fetch `/me` separately because the login endpoint only returns `{ token, role }`, not the full user profile.

### Q17: How does the useApi hook work?
**A:** It creates an Axios instance with the base URL from environment variables. It has two interceptors:
- **Request interceptor**: Automatically attaches `Authorization: Bearer <token>` from localStorage to every request
- **Response interceptor**: Global error handler that shows a toast with the server's error message

The hook also auto-detects FormData and sets `Content-Type: multipart/form-data` for file uploads. Components just call `const { get, post, put, delete } = useApi()` without worrying about headers or error handling.

### Q18: How does your route protection work?
**A:** I have a `ProtectedRoute` component that wraps user and admin routes. It checks three things in order:
1. If auth is still loading, shows a loading state (prevents flash of login page)
2. If user is not authenticated, redirects to `/login`
3. If user's role doesn't match the required role, redirects to home page

For routing, I use React Router v6 nested routes with layout components. `AdminLayout` and `UserLayout` use `<Outlet />` to render child routes while keeping the sidebar persistent.

### Q19: How does the VisitTracker component work?
**A:** It's a component that renders nothing (`return null`) but runs an effect on mount:
1. Skips tracking on admin pages
2. Uses sessionStorage to prevent counting the same user twice in one day
3. Waits 10 seconds before counting — this filters out bots and bounce visits
4. Gets the visitor's IP from the ipify API, then gets city/country from the ipapi geolocation API
5. Posts the location data to the backend analytics endpoint
6. Marks today as counted in sessionStorage

The cleanup function clears the timeout if the component unmounts before 10 seconds.

### Q20: How does the admin sidebar show real-time notification badges?
**A:** The `AdminLayout` component fetches three counts on mount and then every 30 seconds via `setInterval`:
- Unread queries count from `/queries/unread-count`
- Pending bookings count from `/bookings/pending-count`
- Unverified users count from `/admin/users/unverified-count`

These are shown as red `<Badge>` components next to the respective nav links. When the admin navigates to a page (e.g., `/admin/queries`), the corresponding count is reset to 0 using a `useEffect` on `location.pathname`.

---

## Section 5: File Upload & Email Questions

### Q21: How does file upload work in your application?
**A:** I use a three-step pipeline:
1. **Client sends FormData** with files via Axios (multipart/form-data)
2. **Multer middleware** receives files using `memoryStorage()` — files are buffered in RAM, not written to disk. This is necessary because Vercel serverless has no persistent filesystem
3. **Cloudinary `upload_stream`** — the buffer is piped directly to Cloudinary's API, which stores it on their CDN
4. The Cloudinary `secure_url` is returned to the client, which stores it in form state
5. When the form is submitted, the URL is saved to MongoDB

I have three upload endpoints: multi-image (up to 10, auth required), single-image (no auth — for registration profile pic), and video upload.

### Q22: How does your email notification system work?
**A:** I use Nodemailer with Gmail SMTP (app password). The `sendEmail` utility function accepts `to`, `subject`, `text`, and an `isHtml` flag. If `isHtml` is true, it sets `mailOptions.html` instead of `.text`.

Emails are sent automatically at every critical point: registration, booking submission, booking confirmation, booking cancellation, payment update, password reset (request + confirmation), and query replies. Each email uses a branded HTML template with inline CSS for email client compatibility.

The admin also has an email center where they can send individual, bulk (all users), or marketing emails with custom content.

### Q23: How do you handle email failures in bulk sending?
**A:** I use `Promise.allSettled()` instead of `Promise.all()`. This ensures that if one email fails, the rest still get sent. After all promises settle, I count successes and failures and return a response like: "Email sent to 45 recipients. Failed to send to 3 recipients." The email record is saved in the database regardless, with the recipient list and status.

---

## Section 6: Security Questions

### Q24: What security measures did you implement?
**A:**
1. **Password hashing** — bcrypt with 12 salt rounds, plus pre-save hook and pre-findOneAndUpdate hook
2. **JWT authentication** — 1-hour token expiry, server-side user lookup on every request
3. **Helmet** — secure HTTP headers preventing XSS, clickjacking, MIME sniffing
4. **CORS** — restricted to production domain only
5. **Rate limiting** — 10,000 requests per 15 minutes per IP
6. **Joi validation** — server-side input validation on all user inputs
7. **Email immutability** — `delete updates.email` prevents email changes in profile updates
8. **Password immutability** — admin user update route can't modify passwords
9. **Reset tokens** — cryptographically random (`crypto.randomBytes`), 1-hour expiry, cleared after use
10. **Role-based access control** — two-middleware chain (auth → admin) for admin routes

### Q25: Why do you do a DB lookup in the auth middleware instead of just trusting the JWT?
**A:** Because the JWT could be valid (not expired, not tampered) but the user might have been deactivated by the admin since the token was issued. The DB lookup checks `user.isActive` on every request, ensuring deactivated accounts immediately lose access even if they still have a valid token.

### Q26: How does your password reset flow prevent attacks?
**A:** 
1. Token is generated with `crypto.randomBytes(20)` — cryptographically random, unpredictable
2. Token expires in 1 hour — limits the attack window
3. Token is stored as a field on the user document, not in a URL parameter alone — the server verifies it
4. After successful reset, the token fields are cleared (`undefined`) — prevents token reuse
5. A confirmation email is sent after reset — alerts the real user if they didn't initiate it

---

## Section 7: Deployment & DevOps Questions

### Q27: How did you deploy this application?
**A:** Both frontend and backend are deployed on **Vercel**:
- **Frontend**: Vite builds static files. `vercel.json` has a rewrite rule that redirects all routes to `index.html` for SPA client-side routing
- **Backend**: `server.js` exports the Express app as a module (`module.exports = app`). Vercel's `@vercel/node` runtime wraps it in a serverless function. The `vercel.json` routes all requests to `server.js` with CORS headers configured

### Q28: Why did you choose Vercel for the backend instead of a traditional server?
**A:** For a project like this with moderate traffic, serverless is cost-effective (free tier covers it) and auto-scales. The trade-off is cold starts, but for a resort booking website, the latency is acceptable. I had to make one key adaptation: using Multer's `memoryStorage` instead of `diskStorage` because serverless functions have no persistent filesystem.

---

## Section 8: Advanced / Tricky Questions

### Q29: What would happen if two users try to book the same room for the same dates simultaneously?
**A:** This is a race condition. My current approach has the server check availability and create the booking atomically within one route handler. However, there's a theoretical window between the check and the save. In production, the `pending` status acts as a safeguard — the admin manually confirms, so they'd see two pending bookings for the same dates and only confirm one. For a high-traffic system, I'd implement MongoDB transactions or optimistic locking with version fields.

### Q30: Why did you use Joi for validation instead of Mongoose validation alone?
**A:** Mongoose validation only triggers on `save()` and has limited capabilities (no cross-field validation, limited string patterns). Joi validates the request body BEFORE it reaches the database layer, provides much richer validation (regex, cross-field refs like `checkOut > checkIn`, custom validators), and returns user-friendly error messages. This follows the "fail fast" principle — reject bad data at the API layer before it even touches the database.

### Q31: How would you scale this application?
**A:** 
1. **Database**: Add indexes on frequently queried fields (already have compound index on VisitAnalytics). Consider MongoDB Atlas auto-scaling
2. **Caching**: Add Redis for frequently accessed data (room listings, site settings)
3. **File uploads**: Already using Cloudinary CDN — scales independently
4. **API**: Vercel serverless auto-scales horizontally
5. **Email**: Move from Gmail SMTP to a service like SendGrid for higher volume
6. **Real-time**: Add WebSocket (Socket.io) for real-time booking notifications instead of polling

### Q32: What was the most challenging part of building this project?
**A:** The **room availability system** was the most complex. I had to design an algorithm that checks date range overlaps efficiently, works on both frontend (for real-time calendar UI) and backend (for validation), handles edge cases like same-day checkout/check-in, and keeps the Room document in sync when bookings are confirmed or cancelled. The frontend calendar coloring logic required building date key sets and iterating through ranges, which had to match the backend's overlap detection exactly.

### Q33: If you could rebuild this project, what would you change?
**A:** 
1. Add a separate **controllers** directory as the project grew — some route files like `bookings.js` (462 lines) are getting long
2. Implement **WebSocket** for real-time admin notifications instead of 30-second polling
3. Add **MongoDB transactions** for the booking confirmation flow to prevent race conditions
4. Implement **server-side pagination** for all admin lists (some currently load all data)
5. Add **automated testing** — unit tests for validation logic, integration tests for booking flow
6. Use **TypeScript** for better type safety across the full stack

### Q34: How does your application handle errors?
**A:** Multiple layers:
- **Backend**: Every route handler has try/catch. Errors return structured JSON `{ msg: 'error message' }` with appropriate HTTP status codes (400 for validation, 401 for auth, 403 for authorization, 404 for not found, 500 for server errors)
- **Frontend**: The `useApi` hook's response interceptor catches all API errors and shows toast notifications with the server's error message
- **Auth hook**: Catches login/register failures, shows specific error messages from the server
- **Form validation**: Client-side validation with error states shown inline before submission

### Q35: Explain the difference between your `auth` and `admin` middleware and why they're separate.
**A:** They follow the **Single Responsibility Principle**. `auth` only handles authentication (is the user who they say they are?), while `admin` handles authorization (does this user have permission?). They're separate because some routes need auth but not admin (user bookings, profile, wishlist), while admin routes need both. By composing them — `auth, admin` — I can mix and match as needed without duplicating code.

### Q36: How do you handle the "Content" and "SiteSetting" as singleton documents?
**A:** Both models store only one document in their respective collections. The GET endpoint uses `findOne()` without any filter to fetch it. If the document doesn't exist (first-time access), the endpoint auto-creates it with default values and saves it. For updates, SiteSetting uses `findOneAndUpdate({}, body, { upsert: true })` — the empty filter matches the single document, and `upsert` creates it if it doesn't exist. This pattern eliminates the need for a setup/seed script.

### Q37: How does the review system update room ratings?
**A:** When a review is created or deleted, I fetch ALL reviews for that room, calculate the arithmetic mean of all ratings, and update the room's `averageRating` field:
```javascript
const reviews = await Review.find({ room: roomId });
const avgRating = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;
await Room.findByIdAndUpdate(roomId, { averageRating: avgRating });
```
This is a **derived field** — stored for fast reads but recalculated on every write. The alternative would be computing it on every read query, which would be slower for listing pages.

### Q38: What kind of API calls do you use and how do you handle them?
**A:** All communication is **RESTful HTTP**:
- **GET** for reading data (rooms, bookings, analytics) — query params for filtering/pagination
- **POST** for creating resources (bookings, reviews, users) and actions (send email, record visit)
- **PUT** for updating resources (room details, booking status, site settings)
- **DELETE** for removing resources (rooms, reviews, users)

On the frontend, I use a centralized Axios instance via `useApi()` hook that automatically handles JWT attachment, content-type detection (JSON vs FormData), and global error notifications. Pagination uses query parameters (`?page=1&limit=20`), and the server returns `{ data, total, pages, page }` metadata.

### Q39: How does the wishlist feature work?
**A:** The wishlist is stored as an array of Room ObjectIds directly in the User document (`wishlist: [{ type: ObjectId, ref: 'Room' }]`). The toggle endpoint checks if the room ID already exists in the array — if yes, it removes it (splice); if no, it pushes it. After modification, `user.populate('wishlist')` is called to return the full room data. The frontend RoomCard component has a heart button that calls this toggle endpoint, and shows a toast asking to login if the user isn't authenticated.

### Q40: How do you handle the admin analytics dashboard with period filtering?
**A:** The analytics endpoint accepts a `period` query parameter (today/week/month/90days/year/all). It calculates a `fromDate` based on the period, then runs 15+ MongoDB queries in parallel using `Promise.all`:
- Room counts (total, active, inactive)
- Booking counts by status with date filter
- Revenue aggregation using `$match` + `$group` pipeline
- User counts (total, active, verified, new)
- Query and review counts

All queries run concurrently, so the response time equals the slowest single query rather than the sum of all queries. This is critical for dashboard performance.
