# Interview Q&A Preparation: Anik Personal Blog

This document is tailored for the Full Stack JavaScript Developer interview at XPONENT. It focuses on deep code understanding, security, architecture, and AI-driven development verification.

### Q1: How did you implement Authentication and Authorization in your application? Why did you choose this approach?
**Answer:** I implemented a hybrid approach using Firebase Authentication for credential management and a custom Node.js/Express backend for Authorization. When a user logs in, Firebase generates a JWT. For protected API routes, I built a `verifyToken` middleware using the Firebase Admin SDK to decode and validate this JWT. For Authorization, I implemented a Role-Based Access Control (RBAC) system. I have a `verifySuperAdmin` middleware that checks if the decoded token's email matches the environment's super admin email. Additionally, for regular admins, I built an approval workflow where they sit in a "pending" state in MongoDB until the super admin explicitly approves them. I chose this because Firebase securely handles the complex logic of password hashing and social logins, while my custom backend logic gives me strict, granular control over my custom admin hierarchy.

### Q2: I see you implemented brute-force protection on the admin login. Can you walk me through exactly how that logic works in your code?
**Answer:** Yes. In my `POST /login-attempt` route, I query the `AdminUser` model by email. This model has a `loginAttempts` array and a `blockedUntil` Date field. First, I check if `blockedUntil` exists and is in the future; if so, I reject the request immediately. If not, I push the current timestamp into the `loginAttempts` array. I then filter this array to find attempts within the last 5 minutes. If the count exceeds 5, I set `blockedUntil` to 15 minutes from now, save the document, and use Nodemailer to trigger an instant email alert to the Super Admin. This logic ensures the application actively defends itself and alerts administrators in real-time.

### Q3: You used `sanitize-html` for your commenting system. What specific attack vector does this prevent, and why is it necessary if React already escapes HTML?
**Answer:** `sanitize-html` prevents Stored Cross-Site Scripting (XSS) attacks. While it is true that React automatically escapes variables rendered in JSX (e.g., `{comment.content}`), if I ever need to render rich text using `dangerouslySetInnerHTML`, or if the data is consumed by a different client (like a mobile app or an email client, which I do use via Nodemailer), the malicious script would execute. By sanitizing the input on the backend *before* it hits the database, I ensure the data is inherently safe regardless of where or how it is rendered in the future.

### Q4: How are you handling file uploads (like images) in this application?
**Answer:** I handle uploads using Multer and Cloudinary. Instead of saving files to the local disk, which causes issues with ephemeral hosting environments like Vercel or Heroku, I configured Multer to use `memoryStorage()`. When a file is uploaded, Multer stores it as a Buffer in RAM. I then wrote a helper function that wraps `cloudinary.uploader.upload_stream` in a Promise, passing the Buffer directly to Cloudinary. Once Cloudinary resolves with a `secure_url`, I save that URL string to MongoDB. This approach optimizes server disk space and leverages Cloudinary's CDN for faster image delivery to the frontend.

### Q5: Can you explain how your `verifyToken` middleware works line-by-line?
**Answer:** Certainly. 
1. `const token = req.headers.authorization?.split('Bearer ')[1];` - This safely extracts the JWT from the Authorization header.
2. `if (!token) return res.status(401).json({ error: 'Unauthorized' });` - Early return if no token is provided.
3. `try { const decodedToken = await admin.auth().verifyIdToken(token);` - This is the core logic. It sends the token to the Firebase Admin SDK, which cryptographically verifies the signature and checks expiration.
4. `req.user = decodedToken; next();` - If successful, it attaches the decoded user payload to the request object so downstream controllers can use it, and calls `next()` to pass control to the route handler.
5. `catch (error) { res.status(401).json({ error: 'Invalid token' }); }` - Catches expired or tampered tokens and safely rejects the request.

### Q6: If an AI tool generated your `Analytics` aggregation route, how would you verify it works correctly? What edge cases would you test?
**Answer:** First, I would trace the logic flow. The route fetches all blogs and projects, then uses `flatMap` to normalize likes, shares, views, and comments into a single unified array of event objects, which it then sorts by timestamp. 
To verify it, I wouldn't just look at it; I would test edge cases:
- **Empty Database:** Does it crash if there are no blogs or projects? (No, `flatMap` on an empty array returns an empty array).
- **Missing Fields:** What if an older document doesn't have a `views` array? I would ensure the schema defaults to an empty array, or the code handles `undefined`.
- **Memory Limits:** Fetching *all* blogs and projects into memory (`await Blog.find()`) works for a small portfolio, but won't scale. I would flag this to the AI/Team as a technical debt item. We should ideally perform this aggregation directly in MongoDB using the Aggregation Pipeline (`$lookup`, `$unwind`, `$sort`) rather than loading everything into Node.js RAM.

### Q7: How does your application track user locations? Are there any failure modes here?
**Answer:** I track locations by taking the user's IP address and making a server-side HTTP GET request to `ip-api.com/json/`. 
The primary failure mode is network latency or API rate limits. To handle this, I wrapped the Axios call in a `try/catch` block and added a `timeout: 5000` parameter. If the external API fails or times out, the `catch` block intercepts the error, prevents the application from crashing, and gracefully falls back to `{ city: 'Unknown', country: 'Unknown' }`. This ensures that a failure in an analytics dependency doesn't break the core user experience (like logging in or commenting).

### Q8: As an AI-first developer, what would you identify as a "gap" in this codebase that an AI might have missed, and how would you fix it?
**Answer:** One gap is in the error handling of the Cloudinary uploads. Currently, if an image upload fails, the backend returns a 500 error, but it doesn't clean up or rollback any database transactions. Another gap is the lack of pagination in the `GET /blogs` route. An AI might generate a simple `Blog.find()`, which works initially but degrades performance as the database grows. I would prompt the AI to implement MongoDB `skip()` and `limit()` functions based on query parameters, and update the frontend to handle infinite scrolling or pagination controls.

### Q9: How is the Light/Dark mode state managed and persisted across the application?
**Answer:** I used the React Context API. I created a `ThemeContext` that holds the current theme state. This state is wrapped around the entire application in `main.jsx`. Inside `<App>`, I consume this context and apply it to the main wrapper div as a data attribute: `data-theme={theme}`. My `index.css` utilizes CSS variables scoped to `[data-theme='dark']` and `[data-theme='light']`. This allows the entire application's color palette to switch instantly without prop-drilling state down through every component.

### Q10: Why did you separate `admin.js` and `user.js` in your routing? What is the architectural benefit?
**Answer:** Separation of Concerns. `user.js` contains public-facing endpoints (fetching blogs, adding comments) which require minimal authentication, while `admin.js` contains highly sensitive CRUD operations and analytics that require strict Firebase JWT verification and Super Admin checks. By separating them at the router level in `server.js` (`app.use('/api/admin', adminRoutes); app.use('/api', userRoutes);`), I can apply security middleware globally to the entire `/api/admin` path. This drastically reduces the risk of accidentally exposing a secure endpoint, which can happen if admin and public routes are mixed in the same file.
