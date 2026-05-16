# Interview Q&A: Foodie-Spot (Restaurant Website)

This document contains 12 potential interview questions and detailed answers explaining the logic, architecture, and implementation of the Foodie-Spot project. It is designed to help you explain your thought process during an interview.

---

### Q1: Can you walk me through the architecture of the Foodie-Spot project?
**Answer:** 
The application follows the classic MVC (Model-View-Controller) architecture using Laravel. 
- **Models** interact with the MySQL database using Eloquent ORM. 
- **Controllers** contain the business logic (e.g., `OrderController`, `CartController`). 
- **Views** are handled by Blade templating engine.
I split the routing into logical groups: Public, Auth, Customer, and Admin. The Admin routes are protected by a custom `AdminMiddleware`. For the frontend, I used Vanilla JS and jQuery to make asynchronous API/AJAX calls (like updating the cart) so the user doesn't experience hard page reloads during critical flows.

### Q2: How did you implement the Cart logic without requiring users to log in first?
**Answer:**
I utilized a **Session-based Cart**. When a user clicks "Add to Cart", an AJAX POST request is sent to the `CartController`. The controller retrieves the current cart from the session (or initializes an empty array) and increments the quantity for the specific `menu_item_id`. This allows guest users to shop seamlessly. When they proceed to checkout, they are prompted to log in or register. Only at the checkout stage is the session data mapped to a permanent `Order` record in the database.

### Q3: How do you handle database relationships between Orders and Menu Items? What happens if a menu item's price changes later?
**Answer:**
A User `hasMany` Orders, and an Order `hasMany` OrderItems. 
When an order is placed, I don't just link the Order directly to the MenuItem. I create an intermediate `OrderItem` record that saves the `menu_item_id`, the `quantity`, and critically, the **`price` at the exact time of purchase**. This prevents historical order totals from altering if the admin later updates the price of a menu item in the database. 

### Q4: How is Role-Based Access Control (RBAC) implemented for the Admin panel?
**Answer:**
I added a boolean column called `is_admin` to the `users` table. Then, I created a custom middleware named `AdminMiddleware`. 
In the `handle` method of the middleware, I check if `auth()->check()` and if `auth()->user()->is_admin == true`. If both conditions pass, the request proceeds. If not, they are redirected to the homepage or given a 403 error. In `routes/web.php`, I wrapped all admin controllers (Dashboard, Category CRUD, Order Management) inside a route group utilizing this middleware.

### Q5: How did you handle asynchronous API calls in the frontend?
**Answer:**
While the app uses Blade for initial rendering, I used JavaScript (AJAX/Fetch) for dynamic interactions. For example, updating the cart count in the header. When a user adds an item, the JS intercepts the form submission, sends a POST request to the backend, and upon a successful response, it triggers a GET request to `/cart/count` (which returns a JSON payload). The UI is then updated instantly. This mimics single-page application (SPA) behavior for critical components.

### Q6: How do you ensure the security of the checkout and payment process?
**Answer:**
First, the checkout route is protected by the `auth` middleware. Second, I rely on server-side validation using Laravel's Form Requests to ensure data integrity (e.g., validating that the items actually exist in the database and the quantities are valid integers). Third, I do not rely on the frontend for price calculations. When generating the final order total, the backend pulls the prices directly from the database based on the session cart IDs, preventing any malicious manipulation of prices from the client side.

### Q7: If you were to migrate this project from Laravel to the MERN stack (Next.js/Node), how would your architecture change?
**Answer:**
In MERN, the monolithic architecture would be decoupled. 
- The backend would become an Express.js REST (or GraphQL) API. 
- The MySQL database would likely switch to MongoDB (NoSQL), meaning Eloquent ORM would be replaced by Mongoose ODM. 
- The frontend Blade views would be replaced by Next.js React components. 
- For the cart session, instead of server-side sessions, I would likely use JWT (JSON Web Tokens) for auth, and store the temporary guest cart in local storage or Redis, later syncing it to the database upon login.

### Q8: What was the most challenging part of implementing the Order Management system?
**Answer:**
Handling the state transitions of an order (Pending -> Confirmed -> Preparing -> Delivered). I had to ensure that users could see real-time updates of their order status. I created an admin interface where admins can update these statuses via PUT requests, and the customer dashboard dynamically reflects these changes. Additionally, generating PDF receipts required integrating the `dompdf` package and ensuring the HTML/CSS rendered properly in PDF format.

### Q9: Why did you use Vite instead of Webpack for this project?
**Answer:**
Laravel 11 uses Vite by default because it offers significantly faster Hot Module Replacement (HMR) during local development compared to Webpack/Laravel Mix. It leverages native ES modules in the browser, meaning it only bundles the necessary files on demand rather than rebuilding the entire bundle on every save. This vastly improved my frontend development speed, especially when tweaking Tailwind CSS classes and custom JavaScript.

### Q10: How do you handle file uploads, such as menu item images?
**Answer:**
In the Admin Category and MenuItem controllers, I validate the incoming request to ensure the file is an image (`mimes:jpg,png,jpeg` and within a max file size). Then, I use Laravel's Storage facade to securely store the image in the `public/images` directory. The database only stores the string path to the file. This makes it lightweight and easy to retrieve in the Blade views using the `asset()` helper.

### Q11: How did you implement the Notification and Chat system?
**Answer:**
I built API endpoints for the chat and notifications (`/chat/send`, `/chat/messages`, `/notifications/unread-count`). The frontend polls these endpoints (or uses WebSockets) to fetch new data. The controllers return JSON payloads which are then parsed by the JavaScript on the client side to append new chat bubbles or update the notification bell icon.

### Q12: How would you scale this application if the restaurant got 10,000 orders an hour?
**Answer:**
To scale, I would:
1. **Caching:** Implement Redis to cache the menu items and categories so we aren't querying the database on every page load.
2. **Queues:** Move the PDF generation and email/SMS notifications to background jobs using Laravel Queues (powered by Redis or Beanstalkd).
3. **Database Indexing:** Ensure foreign keys (like `user_id` on orders) and frequently searched columns are properly indexed.
4. **Load Balancing:** Separate the web server and database server, and potentially run multiple web server instances behind a load balancer.
