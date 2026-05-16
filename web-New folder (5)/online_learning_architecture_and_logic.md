# System Architecture & Logic Documentation
**Project:** Online Learning (Learn with Anik)

This document outlines the core architectural patterns, logic flow, and structural decisions implemented in the platform.

## 1. Architectural Pattern: Procedural MVC-Lite
While built without a standard MVC framework (like Laravel), the application mimics an MVC architecture through strict file organization and procedural patterns:

- **Model (Data Layer):** Database interactions are handled exclusively via PHP Data Objects (PDO) in `connect.php` and inline SQL statements. The database acts as the single source of truth, but heavy media files are offloaded to Cloudinary.
- **View (Presentation Layer):** HTML templates intertwined with PHP `echo` statements for dynamic data rendering. Reusable UI components (Headers, Footers, Sidebars) are modularized in the `/components` directory and injected via `include`.
- **Controller (Logic Layer):** The top section of every `.php` file acts as the controller. It processes `POST` requests, handles file uploads, interacts with the DB (Model), and sets variables before the HTML (View) is rendered.

## 2. Request Handling & "Middleware" Implementation
Without a framework, "Middleware" is simulated procedurally at the very beginning of protected route files.

**Logic Flow:**
1. **Cookie Verification:** At the top of `admin/dashboard.php` (or any protected file), the script checks for `isset($_COOKIE['tutor_id'])`.
2. **Access Control:** If the cookie is missing, the request is immediately intercepted, and `header('location:login.php')` is executed, stopping further execution.
3. **Session Hydration:** If the cookie exists, the ID is extracted and used to hydrate the user's state (fetching profile details) for the remainder of the script.

*Why implemented this way?*
Cookies with a 30-day expiration (`time() + 60*60*24*30`) were chosen over native PHP `$_SESSION` to provide a persistent "remember me" functionality, reducing friction for returning learners and tutors.

## 3. Core Utilities & Hooks

### A. Cloudinary Media Pipeline (`components/connect.php`)
Instead of storing video/images on the local server (which consumes bandwidth and storage), a custom Cloudinary API wrapper was built.
- **Upload Hook (`uploadToCloudinary`):** Receives the `tmp_name` and target folder. It uses `curl` to push the file to Cloudinary's REST API. It returns a JSON array containing the `public_id` on success.
- **Delete Hook (`deleteFromCloudinary`):** Used during content deletion. Takes the `public_id`, generates a secure SHA-1 signature using the API Secret, and issues a destroy request to Cloudinary.
- **Why?** This decouples the application from the server infrastructure, making the app highly scalable and deployable anywhere without worrying about migrating massive `uploads/` directories.

### B. SMTP Email Delivery (`sendReplyEmail`, `sendStatusEmail`)
Instead of relying on the unreliable native `mail()` function, PHPMailer is integrated.
- **Logic:** Environment variables (`.env`) securely feed SMTP credentials into the function. It uses TLS encryption (`Port 587`).
- **Use Cases:** Forgot password secure tokens, Superadmin notifications, and direct contact replies.

### C. Unique Identifier Generation (`unique_id()`)
- **Logic:** Generates a 20-character random alphanumeric string using a pool of 62 characters (`a-z, A-Z, 0-9`). 
- **Why?** Auto-incrementing primary keys are predictable. Using long, random string IDs for records prevents Insecure Direct Object Reference (IDOR) attacks, ensuring malicious users cannot simply guess the ID of private content or users (e.g., changing `?get_id=1` to `?get_id=2`).

## 4. Advanced System Mechanics

### Cascading Deletions (Data Integrity)
When a Tutor or Superadmin deletes a Playlist, a simple `DELETE` query is insufficient because of associated media and interactions.
**Implementation Logic in `admin/update_playlist.php` & `superadmin/tutors.php`:**
1. **Fetch Dependencies:** Query the DB to find all `content` (videos) associated with the `playlist_id`.
2. **Cloud Purge:** Loop through the fetched content. Call `deleteFromCloudinary()` for every video thumbnail and video file. Call it for the Playlist thumbnail.
3. **Foreign Key Purge:** Delete all `comments`, `likes`, and `views` where the `content_id` matches the videos being deleted. Delete `bookmarks`.
4. **Primary Purge:** Finally, delete the `content` rows, then the `playlist` row.
*Why?* Ensures zero orphan files in Cloudinary (saving money) and zero orphan rows in MySQL (ensuring query performance).

### Smart View Tracking (Rate Limiting)
**Logic in `watch_video.php`:**
- When a user loads a video, the system checks the `views` table.
- Instead of just checking if the `user_id` watched it, it checks the timestamp: `WHERE content_id = ? AND user_id = ? AND date > DATE_SUB(NOW(), INTERVAL 1 HOUR)`.
- If no recent view is found, it inserts a new view record.
*Why?* This custom rate-limiting logic prevents users from artificially inflating view counts by refreshing the page continuously. Views are restricted to one logged interaction per hour per user/IP.

## 5. Security Implementations
- **SQL Injection (SQLi):** 100% of dynamic queries use PDO Prepared Statements (e.g., `execute([$variable])`). Raw variables are never concatenated into SQL strings.
- **Cross-Site Scripting (XSS):** All user inputs (`$_POST`) are sanitized using `htmlspecialchars($var, ENT_QUOTES, 'UTF-8')` before being processed or inserted into the DB. This neutralizes malicious `<script>` tags.
- **Password Security:** Passwords are hashed using `sha1()` before storage. *(Note for modernization: Upgrading to `password_hash()` with BCRYPT is recommended for future iterations).*
- **Token Expiration:** Password reset links use `bin2hex(random_bytes(32))` for cryptographic security. The logic checks `(current_time - created_at) > 3600` to ensure tokens strictly expire after 1 hour.
