# Technical Interview Q&A Preparation
**Project Focus:** Online Learning (Learn with Anik)

Use this guide to prepare for Full Stack Developer interviews. It bridges your specific implementation in this project with broader industry concepts. The questions are numbered clearly for easy reference.

---

## 1. Architecture & Design Decisions

**Q1: I see you didn't use a framework like Laravel or Express. Why did you choose Vanilla Procedural PHP, and how did you manage the architecture?**
**Answer Strategy:** 
"I chose Vanilla PHP to establish a deep, under-the-hood understanding of HTTP requests, session management, and database interactions without the 'magic' of a framework. I implemented a procedural MVC-lite pattern. The top of my files act as Controllers (handling POSTs and logic), PDO handles my Models, and HTML with included components handles Views. This resulted in a highly performant, lightweight application."

**Q2: How did you design the multi-panel system for Users, Tutors, and Superadmins?**
**Answer Strategy:**
"I isolated the logic by creating dedicated directories (`/admin` for tutors, `/superadmin` for platform managers, and root for users). Each panel has its own authentication cookie (`user_id`, `tutor_id`, `superadmin_id`). This separation of concerns ensures that a vulnerability in the User panel cannot easily bleed over and grant access to the Superadmin dashboard."

**Q3: How did you handle user sessions and authentication without a framework?**
**Answer Strategy:** 
"I opted for a persistent cookie-based approach rather than standard PHP sessions. Upon login, I set a 30-day secure cookie. For my 'middleware', I placed authentication checks at the very top of protected files. If the cookie isn't present, the execution stops and redirects the user immediately. This provided a seamless 'remember me' experience across all panels."

---

## 2. Media & Infrastructure Integration

**Q4: Video streaming can be heavy on server resources. How did you architect the platform to handle media?**
**Answer Strategy:** 
"I decoupled media storage entirely from my application server by integrating the Cloudinary API. When a tutor uploads a video, my backend intercepts the `tmp_name`, sends it to Cloudinary via a custom cURL wrapper, and retrieves a `public_id`. My MySQL database only stores this ID. This saved massive bandwidth costs, improved streaming performance through their CDN, and made my database completely portable."

**Q5: How do you handle file deletions? If a user deletes a playlist, what happens to the files?**
**Answer Strategy:** 
"I wrote a robust cascading deletion script. Before a playlist is deleted from the database, the script queries all associated video content. It issues API calls to Cloudinary to destroy the video files and thumbnails, preventing cloud storage bloat. Then, it sweeps the database, deleting associated likes, comments, and views to prevent relational orphans, before finally deleting the content and playlist records."

**Q6: Why did you use PHPMailer instead of PHP's native `mail()` function?**
**Answer Strategy:**
"PHP's native `mail()` function is notoriously unreliable, lacks robust error handling, and often ends up in spam folders because it lacks proper headers. I integrated PHPMailer using SMTP via `vlucas/phpdotenv` to securely inject credentials. This allowed for reliable, TLS-encrypted email delivery for password resets and Superadmin notifications."

---

## 3. Database Logic & Edge Cases

**Q7: How did you implement the 'View Counter' on videos, and how did you prevent users from spamming refresh to inflate views?**
**Answer Strategy:** 
"I implemented temporal rate-limiting in MySQL. When a video is requested, I execute a query checking the `views` table using `DATE_SUB(NOW(), INTERVAL 1 HOUR)`. If the current user or guest IP has a record within the last hour, the view count is ignored. It only increments if the previous view was over an hour ago. This ensures metric integrity."

**Q8: Explain your database search logic. How does it handle different parameters?**
**Answer Strategy:** 
"I used a flexible SQL `LIKE` operator to build a dynamic search engine. The queries dynamically append `%` wildcards to user input. I also designed it to handle both POST requests (from the search bar) and GET requests (filtering by category/topic buttons). I used PDO prepared statements to execute these searches, allowing users to find courses securely based on partial title matches."

**Q9: How did you handle "Bookmarks" and "Likes" to ensure a user can't like a video twice?**
**Answer Strategy:**
"The `likes` and `bookmark` tables act as join tables. Before inserting a new like, the logic runs a `SELECT` query checking if a record exists matching both the `user_id` and the `content_id`. If it returns `rowCount() > 0`, the script executes a `DELETE` query instead, effectively creating a stateless toggle mechanism for liking and unliking."

---

## 4. Security Practices (OWASP)

**Q10: What steps did you take to secure the application against SQL Injection (SQLi)?**
**Answer Strategy:**
"100% of my dynamic database interactions utilize PDO Prepared Statements. Variables are bound to query parameters during execution (`execute([$var])`), meaning the database engine treats the input strictly as data, not executable code. No raw variables ever touch the SQL strings."

**Q11: How did you prevent Cross-Site Scripting (XSS) when users post comments?**
**Answer Strategy:**
"All `$_POST` inputs, especially text areas like comments, are sanitized upon entry using `htmlspecialchars($var, ENT_QUOTES, 'UTF-8')`. This converts special characters like `<` and `>` into HTML entities, neutralizing any malicious `<script>` tags before they reach the database."

**Q12: How did you protect against Insecure Direct Object Reference (IDOR) attacks?**
**Answer Strategy:**
"Instead of standard auto-incrementing integers (`id=1`, `id=2`), I wrote a custom Unique ID generator that creates 20-character random alphanumeric strings for database primary keys. Users cannot guess sequential URLs to access private or unpublished content."

**Q13: If you were to refactor this application today, what security upgrade would be your first priority?**
**Answer Strategy:** 
"Currently, the application uses `sha1()` for password hashing. My immediate refactor would be to upgrade the authentication module to use PHP's native `password_hash()` with the `BCRYPT` or `ARGON2I` algorithm. This implements automatic salting and protects against modern rainbow table and brute-force attacks."

**Q14: How did you secure the "Forgot Password" functionality?**
**Answer Strategy:**
"I utilized `bin2hex(random_bytes(32))` to generate cryptographically secure tokens. These tokens are saved in a specific `password_reset` table. During verification, the system strictly calculates `(current_time - created_at) > 3600` to ensure tokens unequivocally expire after 60 minutes."

---

## 5. Collaboration & Testing (AI-First Context)

**Q15: How do you ensure the code works correctly, especially if parts of it are generated or assisted by AI?**
**Answer Strategy:** 
"I view AI as a powerful pair-programmer, but I act as the Director. I don't just accept code; I review the architecture it suggests. For example, if AI writes a deletion script, my job is to manually verify the edge cases: *Did it delete the Cloudinary asset? Did it leave orphan comments?* I rigorously test boundary conditions, like testing the 1-hour view limit by manipulating the database timestamps manually to ensure the logic holds up under pressure."
