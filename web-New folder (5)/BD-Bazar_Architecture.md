# BD-Bazar: Architecture & Core Logic Implementation

This document outlines the architectural decisions, design patterns, and core logic implemented in the BD-Bazar application. The system follows an MVC pattern enhanced with Service classes to maintain thin controllers and reusable logic.

## 1. System Architecture & Patterns

The application is structured using **Laravel 10**, leveraging its built-in features while adding custom logic to handle complex e-commerce requirements.

*   **Service Pattern:** Complex business logic, external API calls, and caching are abstracted into dedicated services (`MailService`, `CloudinaryService`, `CacheService`). This keeps Controllers clean and makes the logic highly testable.
*   **Security via ID Obfuscation:** Exposing raw sequential database IDs (e.g., `/product/1`) is a security risk (Insecure Direct Object Reference). The system overrides standard ID handling using a mathematical encoding algorithm (`base_convert($id * salt, 10, 36)`). Models define `getPublicIdAttribute()` and `decodePublicId()`, ensuring users only ever see and interact with hashed IDs.

## 2. Authentication & Middleware (RBAC)

The system employs a robust Role-Based Access Control (RBAC) mechanism.

*   **Models:** The `User` model defines constants (`ROLE_USER`, `ROLE_ADMIN`, `ROLE_SUPERADMIN`) and helper methods (`isAdmin()`, `isSuperAdmin()`).
*   **Middleware:** Custom role middleware protects routes. For example, `Route::middleware(['auth', 'role:admin'])` ensures only users with the `admin` role can access the Vendor panel.
*   **Disabled Accounts:** The `AuthController` checks the `$user->status` flag during login. If a Superadmin has disabled a user, the system immediately logs them out and returns a `403 Forbidden` response.

## 3. Core Logic: Session Migration (The "Aha!" Moment)

One of the most complex implementations is the Guest-to-User transition. E-commerce platforms lose conversions if users are forced to log in before browsing.

*   **How it works:** When a guest interacts with the Cart, Wishlist, or Checkout, the data is saved against their `session_id()`.
*   **The Transition:** In `AuthController.php`, during `login()` and `register()`, the system captures the `$oldSessionId` *before* the session is regenerated (which happens automatically upon login to prevent session fixation).
*   **The Logic:** A custom `migrateSessionData()` method is called. It updates the `Cart`, `Wishlist`, and `Order` tables, changing `session_id` to `null` and populating the `user_id` with the newly authenticated user's ID. This creates a seamless, uninterrupted user journey.

## 4. Models & Database Relationships

Eloquent ORM is heavily utilized to map complex relationships and encapsulate business rules.

*   **Products & Categories:** A `Category` hasMany `Products`. The `Product` model includes accessors like `getFinalPriceAttribute()` which dynamically calculates the current price based on `discount_price` or `discount_percent`. It also includes model events (Hooks) to clear the cache via `CacheService` on `saving` and `deleting`.
*   **Orders:** The `Order` model tracks the entire lifecycle. It utilizes constants for Statuses (Pending, Processing, Shipped, Delivered) and Payment Methods. It handles automatic order number generation (`BB-YYYYMMDD-UNIQUEHASH`).
*   **Polymorphic-like Behavior in Emails:** Orders can be placed by Guests or Users. The `AdminController@updateOrderStatus` dynamically determines if it should send the email to a registered `$order->user` object or construct an ad-hoc `(object)` with guest shipping details to pass to the `MailService`.

## 5. Controllers & Request Handling

*   **Form Requests & Validation:** Controllers utilize Laravel's `Validator` facade to strictly validate incoming requests. AJAX requests return `422 Unprocessable Entity` with detailed error bags for the frontend to render.
*   **File Uploads:** Controllers handle file uploads by streaming them directly to Cloudinary via the `CloudinaryService`. This ensures the local server remains stateless and scalable, reducing disk I/O bottlenecks.

## 6. Frontend Handling (Blade + Tailwind + Vite)

The frontend eschews heavy SPAs (Single Page Applications) for a hybrid approach using Blade templating engine compiled via Vite. 

*   **Why Blade?** Faster initial page load (SSR by default) which is critical for E-commerce SEO. 
*   **Styling:** Tailwind CSS provides a highly customizable utility-first design system, making the UI responsive and modern without writing custom CSS files.
*   **Interactivity:** Axios is used for asynchronous operations like adding to cart or updating quantities without full page reloads, providing an app-like feel.
