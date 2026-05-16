# Architecture and Core Logic - Foodie-Spot

## System Architecture

Foodie-Spot is built using the **MVC (Model-View-Controller)** architecture natively provided by Laravel. This structure separates the application's data layer (Models), business logic (Controllers), and presentation layer (Views), making the system highly scalable, maintainable, and secure.

### 1. Frontend Architecture
- **Blade Templating Engine:** Handles the dynamic rendering of HTML. It allows for reusable layouts (`app.blade.php`, `admin.blade.php`) and component-based UI without the overhead of a full SPA framework, optimizing initial page load times.
- **Vanilla CSS & Tailwind:** Tailwind is used for utility-first styling alongside Vanilla CSS (`style.css`) for custom, complex animations and glassmorphism UI components. This hybrid approach keeps the design unique while utilizing Tailwind's rapid structural classes.
- **JavaScript Interactions:** Vanilla JS and jQuery are used for client-side interactions, such as real-time cart updates, toast notifications, and AJAX API calls (e.g., getting live cart counts or chat messages) without requiring full page reloads.

### 2. Backend Architecture
- **Laravel Framework (PHP):** Provides a robust backend foundation. It handles routing, database connections, and session management.
- **Database (MySQL):** A relational database is used because food ordering involves highly structured and relational data (e.g., a User has many Orders, an Order has many OrderItems).

---

## Core Logic & Implementation Details

### 1. Authentication & Authorization
**Why?** To differentiate between general visitors, registered customers, and administrators.
- **Mechanism:** Laravel's built-in session-based authentication is used.
- **Models:** The `User` model handles auth. A boolean column `is_admin` determines if a user has admin privileges.
- **Controllers:** `AuthController` handles login, registration, and password resets.
- **Middleware:** 
  - `auth`: Protects customer routes (checkout, profile, order history).
  - `guest`: Ensures logged-in users cannot access login/register pages.
  - `AdminMiddleware`: A custom middleware that checks if `auth()->user()->is_admin == true`. If not, it aborts with a 403 or redirects. This strictly secures the entire `/admin/*` route group.

### 2. Models & Database Relationships (Eloquent ORM)
**Why?** Eloquent ORM makes querying the database intuitive and prevents SQL injection out-of-the-box.
- **User:** `hasMany` Orders.
- **Category:** `hasMany` MenuItems. (Allows filtering the menu).
- **MenuItem:** `belongsTo` Category.
- **Order:** `belongsTo` User, `hasMany` OrderItems. Tracks total price, delivery status, and notes.
- **OrderItem:** `belongsTo` Order, `belongsTo` MenuItem. Captures the price at the time of order (preventing historical order totals from changing if the menu item price is updated later).

### 3. Cart Logic (Session-Based)
**Why?** Using session-based carts allows guest users to add items to their cart without being forced to register first. This reduces friction and increases conversion rates.
- **Implementation:** `CartController` uses Laravel's `session()->get('cart')`. The session stores an array of key-value pairs `[menu_item_id => quantity]`.
- **AJAX Integration:** When a user clicks "Add to Cart", an AJAX POST request is sent to `/cart/add`. The controller updates the session and returns a success response. The frontend JavaScript then fetches the new cart count via `Route::get('/cart/count')` and updates the UI bubble dynamically without a page refresh.

### 4. Order & Checkout Workflow
**Why?** To securely transition a user's intent into a permanent database record.
- **Implementation (`CheckoutController`):** 
  1. Validates the cart is not empty.
  2. Creates a new `Order` record, calculating the final total + `delivery_fee` (fetched from `SiteSettings`).
  3. Iterates over the session cart, creating `OrderItem` records for each item.
  4. Clears the cart session.
  5. Redirects the user to the Order Success page / Order History.
- **Invoice Generation:** `OrderController@downloadPdf` uses `barryvdh/laravel-dompdf` to convert an HTML blade view into a downloadable PDF receipt.

### 5. Routing Strategy
**Why?** To keep code clean and apply middlewares efficiently.
- **Public Routes:** Accessible by anyone (Home, Menu).
- **Cart Routes:** Accessible by anyone, utilizing AJAX endpoints.
- **Protected Customer Routes:** Wrapped in `auth` middleware (Checkout, Profile, User Orders, Notifications).
- **Admin Routes:** Grouped under an `/admin` prefix and wrapped in `['auth', AdminMiddleware::class]`. This bulk-applies security to all Dashboard, Category CRUD, and Order Management controllers.

### 6. Hooks & Event Listeners (Notifications/Chat)
- **Live Chat & Notifications:** Implemented via specific API-like routes. The `ChatController` handles `sendMessage` and `getMessages` using JSON responses. The frontend polls or uses WebSockets (if configured) to update the UI.
- **Why?** Real-time feedback is crucial for a food delivery app to keep users engaged and informed about their order status.

## Summary
The architecture heavily relies on **Session state** for pre-checkout flows and **Relational Database mapping** for post-checkout data integrity. The combination of Blade components for quick server-side rendering and Vanilla JS for micro-interactions creates a highly performant and user-friendly web application.
