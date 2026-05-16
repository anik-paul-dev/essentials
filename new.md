# AETHERIX Limited - Mid-Level Full Stack Developer Interview Preparation
**Role**: Full Stack Developer (Laravel + Node.js + Modern Frontend)  
**Company**: AETHERIX Limited  
**Candidate**: Anik Paul  
**Focus**: Technical Questions Only (Laravel, Node.js, Next.js/React, MySQL, etc.)

---

### Laravel Questions (1-20)

**1. What is Laravel and why is it popular?**  
Answer: Laravel is a powerful PHP framework that follows MVC architecture. It is popular because it has elegant syntax, built-in tools like Eloquent ORM, Artisan CLI, routing, middleware, and excellent documentation that speeds up development.

**2. Explain MVC architecture in Laravel with example.**  
Answer: Model handles database logic (e.g., User.php), View handles frontend (Blade templates), Controller handles request logic (UserController.php). User sends request → Controller processes it → Model interacts with database → Data passed to View.

**3. What are Migrations and why do we use them?**  
Answer: Migrations are like version control for database. Instead of writing raw SQL, we create tables using PHP code with `php artisan make:migration` and run `php artisan migrate`. It helps in team collaboration and rollback.

**4. What is Eloquent ORM? How is it different from Query Builder?**  
Answer: Eloquent is Laravel’s Active Record ORM. We can write `User::find(1)` or `User::where('status', 'active')->get()`. Query Builder is more fluent for complex queries like `DB::table('users')->select(...)`.

**5. Explain Middleware with example.**  
Answer: Middleware filters HTTP requests. Example: `auth` middleware checks if user is logged in. We can create custom middleware for API authentication or role checking using `php artisan make:middleware`.

**6. What is Route Model Binding?**  
Answer: Laravel automatically injects model instance when we type-hint it in route. Example: `Route::get('/users/{user}', function(User $user){})` – it automatically finds user by ID.

**7. What are Service Providers?**  
Answer: They are the central place to configure application services. They have `register()` and `boot()` methods. All core services (auth, database, etc.) are bootstrapped through service providers.

**8. How does Laravel handle Authentication?**  
Answer: Laravel has built-in auth scaffolding. We use `php artisan make:auth` or Fortify/Sanctum for APIs. Sanctum is best for SPA and mobile token-based authentication.

**9. What is Laravel Sanctum? When do you use it?**  
Answer: Sanctum provides lightweight API authentication for SPAs and mobile apps using personal access tokens. Preferred over Passport for most modern projects.

**10. How do you optimize Laravel application performance?**  
Answer: Use Eager Loading (`with()`), Indexing on database columns, Cache queries with Redis, Config and Route caching (`php artisan config:cache`, `route:cache`), Queue heavy jobs, and use Octane for better speed.

**11. What are Events and Listeners? Give a use case.**  
Answer: Events are actions that happen (e.g., `UserRegistered`). Listeners react to them (send welcome email). Useful for decoupling code.

**12. Explain Queues in Laravel.**  
Answer: Queues allow running time-consuming tasks (email, PDF generation, image processing) in background so user doesn’t wait. Configured with Redis or database driver.

**13. What is Form Request Validation?**  
Answer: Separate validation logic from controller using `php artisan make:request StoreUserRequest`. It keeps controllers clean.

**14. How to handle File Uploads in Laravel?**  
Answer: Use `$request->file('image')`, store with `Storage::disk()->put()`, and validate file type and size.

**15. What is Soft Delete in Laravel?**  
Answer: Instead of permanently deleting records, we mark them as deleted using `deleted_at` column. Enabled by using `SoftDeletes` trait in model.

---

### Node.js + Express Questions (16-30)

**16. What is Node.js and its main advantage?**  
Answer: Node.js is a JavaScript runtime for server-side development. Its biggest advantage is non-blocking, event-driven architecture which handles many concurrent requests efficiently.

**17. Explain Event Loop in Node.js.**  
Answer: Event Loop handles asynchronous operations. It continuously checks call stack and callback queue. When stack is empty, it moves callbacks to stack for execution.

**18. Difference between `async/await` and Promises?**  
Answer: Promises handle async code with `.then().catch()`. Async/await is syntactic sugar over promises that makes code look synchronous and more readable.

**19. What is Express.js?**  
Answer: Express is a minimal and flexible Node.js web framework for building APIs and web applications with routing and middleware support.

**20. What is Middleware in Express?**  
Answer: Functions that run during request-response cycle. Can modify request/response or end the cycle. Example: authentication middleware, logging, CORS.

**21. How do you handle errors globally in Express?**  
Answer: Using error-handling middleware with 4 parameters `(err, req, res, next)` placed at the end of all routes.

**22. What is REST API and its principles?**  
Answer: REST is architectural style using HTTP methods (GET, POST, PUT, PATCH, DELETE). Stateless, uses URLs as resources, and standard HTTP status codes.

**23. How to secure Node.js/Express API?**  
Answer: Use Helmet, CORS, Rate limiting, JWT or Sanctum tokens, Input validation (Joi/Zod), and HTTPS in production.

**24. What is JWT and how does it work?**  
Answer: JSON Web Token. Client logs in → Server sends signed token → Client stores it and sends in Authorization header for protected routes.

**25. How do you manage environment variables in Node.js?**  
Answer: Using `dotenv` package. Create `.env` file and access with `process.env.VARIABLE_NAME`.

**26. Explain CORS and why it is needed.**  
Answer: Cross-Origin Resource Sharing. Browser security feature that blocks frontend from calling backend on different domain. We enable it using CORS middleware.

**27. What is Clustering in Node.js?**  
Answer: Using multiple CPU cores to handle more load since Node.js is single-threaded by default.

**28. How to connect MySQL with Node.js?**  
Answer: Using `mysql2` package with connection pool for better performance.

**29. Difference between `res.send()` and `res.json()`?**  
Answer: `res.json()` automatically sets Content-Type to application/json.

**30. How do you implement Pagination in Node.js API?**  
Answer: Using `limit` and `offset` or `page` and `per_page` query parameters with proper database queries.

---

### Next.js / React + Tailwind Questions (31-45)

**31. What is Next.js and its advantages over Create React App?**  
Answer: Next.js is React framework that supports SSR, SSG, API routes, file-based routing, and built-in image optimization.

**32. Explain SSR vs SSG vs CSR in Next.js.**  
Answer: SSR (getServerSideProps) - renders on every request. SSG (getStaticProps) - renders at build time. CSR - renders on client side.

**33. What are Server Components in Next.js 13+ App Router?**  
Answer: Components that run only on server by default, reducing bundle size and improving performance. No `useState` or `useEffect` in server components.

**34. How do you fetch data in Next.js?**  
Answer: In App Router we use `async` Server Components with `fetch()`. We can also use React Server Components with caching.

**35. What is Tailwind CSS?**  
Answer: Utility-first CSS framework. We write classes directly like `bg-blue-500 p-4 rounded-lg` instead of custom CSS.

**36. How do you make fully responsive UI with Tailwind?**  
Answer: Using responsive prefixes: `sm:`, `md:`, `lg:`, `xl:`, `2xl:` (mobile-first approach).

**37. How to convert Figma design to Tailwind code?**  
Answer: Set Tailwind config for colors, fonts, spacing. Use consistent spacing scale (4, 8, 12, 16px), build mobile-first, then add larger breakpoints.

**38. What is `next/image` component?**  
Answer: Built-in image optimization with lazy loading, placeholder, and automatic format conversion.

**39. How do you handle Authentication in Next.js?**  
Answer: Using NextAuth.js or custom JWT with HTTP-only cookies.

**40. What is App Router vs Pages Router?**  
Answer: App Router (app/ directory) is the new way with Server Components, nested layouts, and streaming. Pages Router is older.

**41. How to optimize performance in Next.js?**  
Answer: Use Server Components, proper caching, `next/image`, dynamic imports for lazy loading, and analyze bundle with Lighthouse.

**42. Explain React Hooks you use most.**  
Answer: `useState`, `useEffect`, `useContext`, `useCallback`, `useMemo`, `useRef`.

**43. What is `useMemo` and `useCallback`?**  
Answer: `useMemo` caches expensive calculations. `useCallback` caches functions to prevent unnecessary re-renders.

**44. How do you manage global state in large Next.js app?**  
Answer: Context API for simple cases, Zustand or Redux Toolkit for complex state.

**45. How do you implement SEO in Next.js?**  
Answer: Use Metadata API in App Router, dynamic `<title>` and Open Graph tags, and SSG where possible.

---

### Database + Others (46-55+)

**46. What is Indexing in MySQL and why is it important?**  
Answer: Indexing makes data retrieval faster. We create index on frequently searched columns like `email`, `user_id`.

**47. Write a sample optimized query for fetching user with posts.**  
Answer: `SELECT * FROM users u LEFT JOIN posts p ON u.id = p.user_id WHERE u.id = ?` and use Eager Loading in Laravel.

**48. Difference between INNER JOIN and LEFT JOIN?**  
Answer: INNER JOIN returns only matching records. LEFT JOIN returns all from left table and matching from right.

**49. What is N+1 Query Problem? How to solve it?**  
Answer: When we loop and query inside loop. Solved by Eager Loading in Laravel (`with('relation')`) or proper joins.

**50. How do you version control database changes?**  
Answer: Using Laravel Migrations. For production, use Laravel Migrations + Seeders.

**51. Explain Git workflow you follow in team.**  
Answer: Feature branch → Commit meaningful messages → Pull Request → Code Review → Merge to develop → Deploy.

**52. How do you debug Laravel and Node.js applications?**  
Answer: Laravel: `dd()`, `log()`, Telescope, Debugbar. Node.js: `console.log`, VS Code debugger, Winston logger.

**53. What is REST vs GraphQL?**  
Answer: REST has multiple endpoints. GraphQL has single endpoint where client requests exact data needed.

**54. Have you worked with payment gateway integration?**  
Answer: Yes, I have integrated payment systems in hotel and food ordering projects (Laravel).

**55. How do you ensure application security?**  
Answer: Input validation, SQL injection prevention (Eloquent), XSS protection, CSRF tokens, secure headers, rate limiting, and hashed passwords.

---

**Total Questions: 55+**

**Preparation Tips:**
- Focus more on Laravel + Next.js combination.
- Be ready to explain your projects (AP-Hotel, Mirinjapaingtong Valley, VMS, Foodispot).
- Practice writing small code snippets on paper/whiteboard.
- If you don’t know something, say “I have basic understanding but would love to learn more”.

You can copy the above content and save as `aetherix-interview-prep.md`

---

Let me know if you want me to **add more questions** on any specific topic (Laravel advanced, Next.js App Router, Project explanation, etc.). Good luck for tomorrow!