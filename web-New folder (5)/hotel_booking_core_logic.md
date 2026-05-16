# Core Logic & Implementation Details (Hotel Booking System)

This document breaks down the core architecture, logic, and implementation strategies used in the AP-Hotel Booking System.

## 1. System Architecture
The project strictly follows the **MVC (Model-View-Controller)** architecture pattern provided by Laravel.
- **Why?** MVC enforces a strong separation of concerns. The data layer (Models) is isolated from the presentation layer (Views), with Controllers acting as the bridge. This makes the codebase highly scalable, easier to test, and simpler to debug (a critical requirement for AI-assisted development).

## 2. Routing Logic (`routes/web.php`)
Routes are logically separated and grouped to maintain clean code and secure access.
- **Public Routes:** Open to all users (Home, Rooms, Contact, About).
- **Authentication Routes:** Handles Login, Register, Password Resets.
- **User Routes (`/user`):** Grouped inside the `auth` middleware. Ensures only logged-in users can book rooms, cancel bookings, or view profiles.
- **Admin Routes (`/admin`):** Grouped inside a prefix (`/admin`) and protected by multiple middlewares: `['auth', \App\Http\Middleware\AdminMiddleware::class]`.
- **Why?** Route grouping minimizes code duplication and centrally enforces security constraints. If a new admin feature is added, placing it in the admin route group automatically secures it without needing to add validation logic to the controller manually.

## 3. Middleware & Authentication
- **Authentication (`auth`):** Laravel's built-in session-based authentication manages user sessions securely using HTTP-only cookies, protecting against XSS and CSRF attacks.
- **AdminMiddleware:** A custom middleware that intercepts requests to the admin panel. It checks if the authenticated user has the necessary privileges (e.g., `role == 'admin'`). If not, it redirects them or returns a 403 Forbidden error.
- **Why?** Middleware acts as a firewall for HTTP requests. Handling role verification at the middleware layer prevents unauthorized access *before* the request even reaches the Controller, saving server resources and preventing security loopholes.

## 4. Models & Database Logic (Eloquent ORM)
The database structure is mapped using Laravel's Eloquent ORM.
- **Relationships:** Complex relationships are defined inside the models to retrieve relational data easily.
  - `Room` model `hasMany` `RoomImage` (One-to-Many).
  - `Room` `belongsToMany` `Feature` and `Facility` (Many-to-Many).
  - `Booking` `belongsTo` `User` and `belongsTo` `Room`.
- **Why?** Eloquent abstracts complex SQL joins into readable, object-oriented syntax. Instead of writing raw SQL, we use `$room->images` or `$user->bookings`, which improves readability, reduces SQL injection risks, and makes data manipulation intuitive.

## 5. Controllers
Controllers are neatly divided into namespaces: `App\Http\Controllers`, `App\Http\Controllers\Admin`, and `App\Http\Controllers\User`.
- **AdminRoomController:** Handles creating, updating, and deleting rooms. When a room is created, images are processed and uploaded to **Cloudinary**, and the Cloudinary secure URL is stored in the database.
- **BookingController:** Implements core business logic.
  - **Availability Check:** Before creating a booking, the controller checks if the requested dates overlap with existing bookings for that specific room.
  - **State Management:** Bookings have statuses (e.g., pending, assigned, cancelled). Admin can transition a booking from "new" to "assigned".
- **Why?** Namespacing prevents naming collisions (e.g., `Admin\BookingController` vs `User\BookingController`). It adheres to the Single Responsibility Principle, ensuring each controller only handles logic relevant to its specific domain.

## 6. Frontend Handling (Blade + Tailwind CSS + Vite)
- **Blade Templating:** The UI is rendered server-side using Blade. Layouts (e.g., `app.blade.php`, `admin.blade.php`) act as master templates, while individual pages extend these layouts. This implements the DRY (Don't Repeat Yourself) principle for headers, footers, and sidebars.
- **Vite & Tailwind CSS:** Vite is used to bundle CSS and JS assets efficiently. Tailwind CSS provides utility-first styling, enabling rapid UI development directly within the Blade files.
- **Dynamic Content Injection:** Using Blade directives (`@if`, `@foreach`), PHP data passed from the Controllers is injected directly into the HTML to render dynamic tables, carousels, and room listings.

## 7. Advanced Integrations & Utils
- **Cloudinary Integration:** For image management (Rooms, Carousel, Team). Instead of storing images on the local server (which breaks in stateless deployments or containerized environments like Docker), images are offloaded to Cloudinary via API.
- **DOMPDF:** Used in `BookingController` to generate PDF invoices on-the-fly. The controller passes booking data to a specific Blade view, which DOMPDF parses and converts into a downloadable PDF stream.
- **Settings & "Shutdown" Mechanism:** The `Setting` model is queried on App boot or via middleware. If the "Shutdown" flag is active, the application intercepts booking requests and returns a maintenance message, preventing data inconsistencies during system updates.

## 8. Logic Tracing Example: The Booking Flow
1. **User Request:** User selects dates on the Room Details page and clicks "Book Now".
2. **Route:** Request hits `POST /book-now`.
3. **Middleware:** `auth` verifies the user is logged in.
4. **Controller (`BookingController@store`):**
   - Validates input (dates, room ID).
   - Queries the database for overlapping dates to prevent double-booking.
   - Calculates the total price based on the `Room` price and the number of days.
   - Inserts a new row into the `bookings` table with status "pending".
5. **Response:** Redirects user to their `user/bookings` page with a success flash message.
6. **Admin Side:** Admin sees the new booking in `/admin/new-bookings` and assigns a physical room number, changing status to "assigned".
