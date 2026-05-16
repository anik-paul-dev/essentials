# NagarSeba - Interview Preparation Q&A
*Tailored for Full Stack JavaScript Developer Role at XPONENT*

---

## 1. System Architecture & Tech Stack

**Q1: Can you explain the overall system architecture of NagarSeba and why you chose this specific stack?**

**Answer:** 
NagarSeba is built on a decoupled Client-Server architecture using the MERN stack (MongoDB, Express, React, Node.js). 
I chose React for the frontend due to its component-driven architecture, which allowed me to build a highly interactive and dynamic UI for maps and dashboards. Vite was used for ultra-fast bundling and HMR. 
For the backend, Node.js and Express were ideal because the system relies heavily on asynchronous I/O operations—specifically real-time Socket.IO connections and parallel API requests to external services (like Cloudinary and Gemini API). 
MongoDB was the perfect database choice because of its native support for GeoJSON and geospatial querying (`$near`), which was critical for mapping civic issues and detecting duplicate reports based on proximity.

---

## 2. Authentication & Security

**Q2: Walk me through your authentication flow. How does the frontend handle token expiration securely without interrupting the user?**

**Answer:** 
I implemented a dual-token JWT system. On login, the user receives a short-lived Access Token (e.g., 15 mins) and a long-lived Refresh Token (e.g., 7 days). 
The frontend uses a centralized API utility file (`api.js`) that acts as an interceptor. Every `fetch` request passes through this file. If the backend returns a `401 Unauthorized` error (Token Expired), the interceptor automatically pauses the request, calls the `/api/auth/refresh-token` endpoint using the Refresh Token, retrieves a new Access Token, updates the `localStorage`, and then seamlessly retries the original request. The user experiences zero interruption. 
To enhance security, role-based access control (RBAC) middleware is implemented on the backend to protect sensitive routes based on roles (`citizen`, `authority`, `admin`).

---

## 3. Real-Time Data & WebSockets

**Q3: How did you implement real-time ticket tracking in NagarSeba? Explain the flow.**

**Answer:** 
I used Socket.IO to enable real-time, bi-directional communication. 
When a citizen logs in, a custom React hook (`useSocket`) establishes a connection to the server and joins a specific "room" identified by their `userId`. 
When an Authority updates a ticket status (e.g., from "Assigned" to "In Progress"), the Express controller updates the database and then uses the globally accessible `io` instance to emit a `status_update` event directly to that specific user's room. 
The React frontend listens for this event and instantly updates the UI state without requiring a page refresh. This significantly improves UX compared to traditional polling.

---

## 4. Geospatial Data & Duplicate Detection

**Q4: NagarSeba features a duplicate detection system. How did you implement this logic in MongoDB and Node.js?**

**Answer:** 
The duplicate detection logic relies on MongoDB's geospatial indexing. In the Mongoose schema for the `Issue` model, the location is stored as a GeoJSON `Point`, and I created a `2dsphere` index on it.
When a user submits a new report, before saving it, the Express controller runs a query using the `$near` operator. It searches for existing issues within a 150-meter max distance (`$maxDistance: 150`), matching the same category, and created within the last 30 days. 
If a match is found, the server returns a specific response prompting the frontend to show a modal: "Similar issue found nearby. Upvote instead?" This prevents database bloat and authority inbox flooding.

---

## 5. Background Jobs & Automation

**Q5: The application features automated SLA (Service Level Agreement) escalations. How did you handle background scheduling in a Node.js environment?**

**Answer:** 
Instead of relying on heavy external task queues like Redis/Bull, I utilized `node-cron` directly within the Node.js process to keep infrastructure costs low. 
I have a cron job that runs every hour (`0 * * * *`). It queries the MongoDB database for any unresolved issues where the `slaDeadline` is older than the current time (`$lt: now`). 
It iterates through these overdue issues, updates their status to 'Overdue', flags them as breached, saves the new status to the `statusHistory` array, and triggers notification utilities (emails/webhooks) to alert the administration. A separate cron job runs every 6 hours to auto-confirm resolved tickets if the citizen hasn't responded in 48 hours.

---

## 6. AI Integration & Prompt Engineering

**Q6: You integrated the Gemini API for automatic issue categorization. How do you ensure the API responses are structured correctly for your database?**

**Answer:** 
I integrated the `@google/generative-ai` SDK. The key to getting structured data was strict prompt engineering. I explicitly instructed the AI in the prompt to return the response *only* as a stringified JSON object matching a specific schema (e.g., `{ "category": "Road Damage", "urgency": "High", "reason": "..." }`) and provided the exact allowed enum values for categories and urgency.
In the Node.js utility function, I parse the JSON output. I wrapped this in a `try...catch` block. If the AI hallucinates or returns malformed JSON, the catch block intercepts the parsing error and returns a safe fallback response to the frontend, ensuring the application doesn't crash.

---

## 7. Deep Debugging & Troubleshooting

**Q7: If the real-time Socket.IO status update fails on the client's end, how would you trace and debug this issue from backend to frontend?**

**Answer:** 
I would follow a structured trace:
1. **Database Check:** Verify if the Express controller actually updated the status in MongoDB. If not, the issue is in the HTTP request payload or database query.
2. **Server Emit Check:** Add a console log right before `io.to().emit()` in the backend controller to ensure the code block is reached and the correct `userId` room is being targeted.
3. **Socket Connection Check:** On the frontend, verify if the socket is actually connected using `socket.connected` and ensure the client successfully emitted the initial `join` event with the correct User ID. Check the network tab in dev tools to ensure the WebSocket connection upgraded successfully.
4. **Client Listener Check:** Ensure the `socket.on('status_update')` listener in the React component is mounted, isn't being unmounted prematurely, and that the state updater function inside it is executing properly.

---

## 8. Frontend Performance Optimization

**Q8: How did you optimize the frontend performance in React, specifically dealing with heavy components like Leaflet Maps and Chart.js?**

**Answer:** 
I aggressively utilized code splitting using React's `lazy` and `Suspense`. Only the critical public routes and login pages are included in the initial JavaScript bundle. 
Heavy dependencies like Leaflet maps (`PublicMap` component) and Chart.js (`Scoreboard` component) are lazy-loaded. When a user navigates to the dashboard, Vite dynamically fetches that specific JavaScript chunk over the network. 
This drastically reduced the initial load time. Furthermore, I utilized React Context effectively to prevent prop drilling and avoid unnecessary re-renders of heavy components.

---

## 9. Security & Data Privacy

**Q9: NagarSeba has an "Anonymous Safe Reporting" feature. How did you implement this to ensure true anonymity?**

**Answer:** 
If a user selects anonymous reporting, their name and email are not saved in plain text. I used the Node.js built-in `crypto` module to AES-encrypt their identifiable data before saving it to MongoDB. 
The API endpoints that serve data to the Authorities and Public dashboards strictly exclude the reporter's information for anonymous tickets. The decryption key is stored securely in environment variables. The backend decrypts the email only in memory when it needs to send an automated status update via Resend, ensuring the identity is never exposed in API payloads or easily accessible via direct database query.

---

## 10. AI Coding & Code Verification (Crucial for XPONENT)

**Q10: The role at XPONENT requires heavily reviewing and verifying AI-generated code. Based on your experience building complex logic in NagarSeba, how do you verify code you didn't write from scratch?**

**Answer:** 
Building NagarSeba taught me not to trust code just because it "looks right." When reviewing complex logic (like an AI-generated aggregation pipeline for the Chart.js dashboard or the `$near` geospatial query), I take these steps:
1. **Trace the Happy Path:** I read the code line-by-line to understand the exact data flow from input to output.
2. **Mental Sandbox:** I identify the assumptions the code is making. For example, in a cron job, what happens if the database connection drops halfway through the loop? 
3. **Edge Case Testing:** I actively try to break it. I feed it null inputs, unexpected data types, or simulate network latency. 
4. **Verify Requirements:** I cross-reference the output strictly with the business requirements. If AI generates a complex RegEx for form validation, I test it against a suite of valid and invalid strings rather than assuming the RegEx is correct. Reading code deeply and testing to failure is the only way to take true ownership of the final product.
