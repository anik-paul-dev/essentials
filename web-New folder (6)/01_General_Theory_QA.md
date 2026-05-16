# 📘 GENERAL THEORY INTERVIEW Q&A — ALL TECHNOLOGIES
### Full Stack JS Developer | XPONENT, Chattogram

---

# ══════════════════════════════════════
# JAVASCRIPT (Core)
# ══════════════════════════════════════

**Q: What is the difference between var, let, and const?**
> `var` is function-scoped and hoisted — it exists before its line runs (value is `undefined`). `let` and `const` are block-scoped. `const` cannot be reassigned but object/array contents can be mutated. I always use `const` by default and `let` only when reassignment is needed. I never use `var`.

---

**Q: What is hoisting?**
> JavaScript moves variable and function declarations to the top of their scope before execution. `var` declarations are hoisted (value is `undefined`). `let`/`const` are hoisted but stay in a "temporal dead zone" — accessing them before declaration throws a ReferenceError. Function declarations are fully hoisted.

---

**Q: What is a closure?**
> A closure is when an inner function remembers variables from its outer function even after the outer function has finished executing. Used for data privacy, factory functions, and callbacks.
```js
function counter() {
  let count = 0;
  return () => ++count;
}
const inc = counter();
inc(); // 1
inc(); // 2
```

---

**Q: What is the difference between == and ===?**
> `==` compares values with type coercion (`"5" == 5` is true). `===` compares value AND type (`"5" === 5` is false). Always use `===` to avoid unexpected bugs.

---

**Q: What are Promises and async/await?**
> A Promise represents a future value — it can be pending, fulfilled, or rejected. `async/await` is syntactic sugar over Promises — it makes async code look synchronous and is much easier to read. I always use `async/await` with `try/catch` for error handling.

---

**Q: What is the event loop in JavaScript?**
> JS is single-threaded. The event loop monitors the call stack and the task queue. When the call stack is empty, it picks callbacks from the queue and pushes them onto the stack. This allows async operations (setTimeout, fetch, DB calls) to work without blocking the main thread.

---

**Q: What is the difference between null and undefined?**
> `undefined` means a variable was declared but not assigned a value. `null` is an intentional absence of value — you set it explicitly. `typeof null === 'object'` is a historical JS bug.

---

**Q: What are arrow functions and how are they different?**
> Arrow functions have shorter syntax and do NOT have their own `this` — they inherit `this` from the surrounding scope. Regular functions have their own `this`. Arrow functions also cannot be used as constructors.

---

**Q: What is destructuring?**
```js
// Array destructuring
const [first, second] = [10, 20];

// Object destructuring
const { name, age } = user;
const { name: userName } = user; // rename

// With default values
const { role = 'user' } = user;
```

---

**Q: What is the spread and rest operator?**
```js
// Spread — expand
const arr2 = [...arr1, 4, 5];
const obj2 = { ...obj1, role: 'admin' };

// Rest — collect remaining
function sum(...nums) { return nums.reduce((a, b) => a + b, 0); }
const { id, ...rest } = user; // rest has everything except id
```

---

**Q: What is a higher-order function?**
> A function that takes another function as argument or returns a function. Examples: `map`, `filter`, `reduce`, `forEach`.
```js
const doubled = [1,2,3].map(n => n * 2);       // [2,4,6]
const evens   = [1,2,3,4].filter(n => n % 2 === 0); // [2,4]
const sum     = [1,2,3].reduce((acc, n) => acc + n, 0); // 6
```

---

**Q: What is debounce vs throttle?**
> **Debounce:** Wait until the user stops triggering an event, then fire once. Used for search input — don't call API on every keystroke.
> **Throttle:** Fire at most once every X milliseconds no matter how many times triggered. Used for scroll or resize events.

---

**Q: What is localStorage vs sessionStorage vs cookies?**

| | localStorage | sessionStorage | Cookie |
|---|---|---|---|
| Expires | Never (manual clear) | Tab close | Set expiry date |
| Size | ~5MB | ~5MB | ~4KB |
| Sent to server | No | No | Yes (every request) |
| Accessible from JS | Yes | Yes | Yes (unless httpOnly) |

> I store JWT token in localStorage for simplicity, or httpOnly cookies for better security.

---

**Q: What is event delegation?**
> Instead of adding listeners to every child, add one listener to the parent and check `event.target`. Efficient for dynamic lists.
```js
document.getElementById('list').addEventListener('click', (e) => {
  if (e.target.tagName === 'LI') console.log(e.target.textContent);
});
```

---

# ══════════════════════════════════════
# REACT
# ══════════════════════════════════════

**Q: What is React and what problem does it solve?**
> React is a JavaScript library for building UIs using reusable components. It solves the problem of manually updating the DOM — React tracks state changes and updates only the necessary DOM nodes via the Virtual DOM.

---

**Q: What is the Virtual DOM?**
> A lightweight JS copy of the real DOM. When state changes: React builds new Virtual DOM → diffs it against old Virtual DOM → updates only the changed parts in the real DOM. Faster than full DOM re-renders.

---

**Q: What is JSX?**
> JSX is JavaScript XML — a syntax that looks like HTML inside JavaScript. Babel compiles it to `React.createElement()` calls. It lets you write UI declaratively alongside logic.

---

**Q: What is the difference between functional and class components?**
> Class components use lifecycle methods (`componentDidMount`, `componentDidUpdate`) and `this.state`. Functional components use hooks (`useState`, `useEffect`). Since React 16.8 hooks were introduced, functional components are the standard. I only write functional components.

---

**Q: Explain all commonly used React hooks.**

**useState** — manage local state
```js
const [count, setCount] = useState(0);
const [user, setUser] = useState(null);
const [form, setForm] = useState({ email: '', password: '' });
```

**useEffect** — run side effects
```js
useEffect(() => { fetchData(); }, []); // on mount
useEffect(() => { fetchUser(id); }, [id]); // when id changes
useEffect(() => {
  const timer = setInterval(tick, 1000);
  return () => clearInterval(timer); // cleanup
}, []);
```

**useContext** — access global state
```js
const { user, login, logout } = useContext(AuthContext);
```

**useRef** — DOM access or persist value without re-render
```js
const inputRef = useRef();
inputRef.current.focus();
```

**useMemo** — memoize expensive value
```js
const filtered = useMemo(() => products.filter(p => p.price < max), [products, max]);
```

**useCallback** — memoize function so child doesn't re-render
```js
const handleDelete = useCallback((id) => deleteItem(id), []);
```

**useReducer** — complex state (like cart, multi-step form)
```js
const [state, dispatch] = useReducer(cartReducer, { items: [], total: 0 });
dispatch({ type: 'ADD_ITEM', payload: product });
```

---

**Q: What is prop drilling and how to fix it?**
> Prop drilling is passing data through many component levels just to reach a deep child. Fix with:
> 1. **Context API** — global store any component can read
> 2. **Zustand/Redux** — external state manager
> 3. **Component composition** — pass children components instead

---

**Q: What is React Context?**
> Lets you share data (auth user, cart, theme) across the entire component tree without passing props manually at each level. Create with `createContext()`, provide with `<Provider value={...}>`, consume with `useContext()`.

---

**Q: What is the difference between controlled and uncontrolled components?**
> **Controlled:** input value driven by React state. I control every keystroke.
> **Uncontrolled:** DOM manages the value; I read it via `useRef`. Controlled is better for validation and form logic. I always use controlled forms.

---

**Q: What is React.memo?**
> Wraps a component to prevent re-rendering if props haven't changed. Useful for expensive child components that receive the same props often.
```js
const ProductCard = React.memo(({ product }) => <div>{product.name}</div>);
```

---

**Q: What is code splitting and lazy loading?**
> Load components only when needed to reduce initial JS bundle:
```js
const AdminPage = lazy(() => import('./AdminPage'));
<Suspense fallback={<Spinner />}><AdminPage /></Suspense>
```

---

**Q: What is React Router? How do you do protected routes?**
> React Router enables client-side navigation. A protected route checks if user is authenticated — if not, redirects to login.

---

**Q: What is the key prop and why is it important?**
> React uses `key` to identify list items during re-renders. Without a stable unique key, React may incorrectly reuse or re-order DOM elements. Always use a database ID as key, never the array index (index causes bugs when the list is reordered).

---

# ══════════════════════════════════════
# NEXT.JS
# ══════════════════════════════════════

**Q: What is Next.js?**
> A React framework with SSR, SSG, ISR, file-based routing, API routes, image optimization, built-in middleware, and TypeScript support out of the box. Best for production apps needing SEO and fast initial load.

---

**Q: SSR vs SSG vs ISR vs CSR — explain each.**
> - **SSG:** HTML built at build time. Fastest, served from CDN. For pages that don't change often.
> - **SSR:** HTML built on every request. Always fresh. For personalized or real-time pages.
> - **ISR:** SSG + auto-refresh in background every N seconds. Best of both worlds.
> - **CSR:** Browser builds the HTML. No SEO benefit. For dashboards/private pages.

---

**Q: What are React Server Components?**
> Components that render only on the server. Zero JS sent to client. Can directly query DB. Cannot use `useState`, `useEffect`, or browser APIs. Add `'use client'` for interactive parts.

---

**Q: What is Next.js middleware?**
> Code that runs at the Edge BEFORE the page loads. Used for: auth redirects, role checks, locale redirects. Created in `middleware.js` at project root. Uses `NextResponse`.

---

**Q: How does Next.js handle SEO?**
> Using `export const metadata` (App Router) or `<Head>` (Pages Router) to set title, description, Open Graph tags. SSR/SSG ensures HTML is pre-rendered so search engine crawlers can read content — unlike CSR where they see an empty shell.

---

**Q: What is `getServerSideProps` vs `getStaticProps`? (Pages Router)**
> - `getServerSideProps` — runs on every request, gets fresh data for SSR
> - `getStaticProps` — runs at build time, data baked into static HTML
> - `getStaticPaths` — used with dynamic routes for SSG to define which paths to pre-build

---

**Q: Pages Router vs App Router?**
> App Router (Next.js 13+) is the modern standard. Uses `app/` directory, React Server Components, nested layouts, `async/await` for data fetching. Pages Router is legacy but still works. New projects use App Router.

---

**Q: How do you use `next/image`?**
> Automatically optimizes images: lazy loading, WebP format, responsive sizing. Must provide `width`/`height` or use `fill` with a positioned parent container.

---

# ══════════════════════════════════════
# NODE.JS
# ══════════════════════════════════════

**Q: What is Node.js?**
> JavaScript runtime built on Chrome's V8 engine. Runs JS on the server. Single-threaded, non-blocking, event-driven. Great for I/O-heavy apps like REST APIs, chat apps, real-time systems. Not ideal for CPU-intensive tasks.

---

**Q: What is the event loop?**
> Node.js is single-threaded. Async work (DB queries, file I/O, network calls) is offloaded to the OS. When done, callbacks go into the event queue. The event loop picks them up when the call stack is empty. This is why Node doesn't block on I/O.

---

**Q: What is the difference between callbacks, promises, and async/await?**
> All handle async operations. Callbacks (old way) lead to "callback hell" — deeply nested code. Promises chain with `.then().catch()`. `async/await` is the cleanest — reads like synchronous code, use `try/catch` for errors.

---

**Q: What is `require` vs `import`?**
> `require` = CommonJS (old). Synchronous. `import` = ES Modules (modern). Static analysis, tree-shakeable. I use ES Modules in new projects.

---

**Q: What is npm? What is the difference between dependencies and devDependencies?**
> npm = Node Package Manager. `dependencies` are needed in production (express, mongoose). `devDependencies` are only for development (nodemon, jest, eslint). Install dev deps with `npm install --save-dev`.

---

**Q: What is `nodemon`?**
> A dev tool that automatically restarts the Node server when file changes are detected. I use it in development: `"dev": "nodemon server.js"`.

---

**Q: What is the purpose of `.env` files?**
> Store sensitive config (DB URI, JWT secret, API keys) outside the codebase. Never commit `.env` to Git. Load with `dotenv` package. Access via `process.env.VARIABLE_NAME`.

---

# ══════════════════════════════════════
# EXPRESS.JS
# ══════════════════════════════════════

**Q: What is Express.js?**
> Minimal Node.js web framework. Provides routing, middleware, request/response utilities. Most popular backend framework for Node.js REST APIs.

---

**Q: What is middleware in Express?**
> Function with `(req, res, next)`. Runs between request and route handler. Can modify request, validate auth, log, handle errors, parse body. Call `next()` to pass to the next middleware.

---

**Q: What is the difference between `app.use()` and `app.get()`?**
> `app.use()` matches ANY HTTP method and optional path — used for global middleware. `app.get()`, `app.post()`, etc. match specific HTTP methods on specific paths.

---

**Q: How do you structure a large Express app?**
```
server/
├── controllers/   — business logic
├── models/        — DB schemas
├── routes/        — route definitions
├── middleware/    — auth, error, validation
├── utils/         — helpers
├── config/        — DB connection
└── server.js      — entry point
```

---

**Q: What is CORS and how to fix it?**
> Browser blocks requests from different origin (domain/port). Fix: `npm install cors` then `app.use(cors({ origin: 'http://localhost:3000' }))`.

---

**Q: How do you handle errors globally in Express?**
> Add a 4-parameter middleware `(err, req, res, next)` at the very end of `server.js`. All controllers call `next(error)` to pass errors here. One place to format and send all error responses.

---

**Q: What is JWT and how does it work?**
> JSON Web Token — a signed token for authentication. Structure: `Header.Payload.Signature`. Server creates it on login, client stores it, sends it in every request header (`Authorization: Bearer token`). Server verifies signature — no DB lookup needed. Stateless.

---

**Q: What is bcrypt and why use it?**
> bcrypt is a password hashing library. Never store plain-text passwords. `bcrypt.hash(password, 12)` creates a salted hash. `bcrypt.compare(plainText, hash)` verifies it. The salt and cost factor make it resistant to rainbow table and brute force attacks.

---

**Q: What is rate limiting and why use it?**
> Limits how many requests a client can make in a time window. Prevents brute-force attacks on login, DDoS, API abuse. Use `express-rate-limit` package.

---

# ══════════════════════════════════════
# MONGODB + MONGOOSE
# ══════════════════════════════════════

**Q: What is MongoDB?**
> NoSQL document database. Stores data as JSON-like documents (BSON) in collections (instead of rows in tables). Schema-less — flexible structure. Great for hierarchical data and rapid development.

---

**Q: SQL vs NoSQL — when to use which?**

| | SQL (MySQL/PostgreSQL) | NoSQL (MongoDB) |
|---|---|---|
| Schema | Fixed | Flexible |
| Relations | Strong (JOINs, FKs) | Weak (embedded/refs) |
| ACID | Full | Partial (4.0+) |
| Best for | Financial, relational data | Nested, evolving data |

---

**Q: What is Mongoose?**
> ODM (Object Document Mapper) for MongoDB in Node.js. Provides: schema definition, validation, middleware (pre/post hooks), model methods, population (populate references).

---

**Q: What is a Mongoose Schema and Model?**
> Schema defines the shape of documents (field names, types, validation, defaults). Model is the compiled class you use to query the collection. One model per collection.

---

**Q: What are Mongoose relationships — embed vs reference?**
> **Embed:** Store related data inside the document. Fast reads. Good for data that belongs together (order + order items).
> **Reference:** Store `ObjectId` and use `.populate()`. Good for data accessed independently (user + posts).

---

**Q: What is populate() in Mongoose?**
> Replaces an ObjectId reference with the actual document from the referenced collection. Like a JOIN in SQL.
```js
const post = await Post.findById(id).populate('author', 'name email');
```

---

**Q: What are Mongoose hooks (pre/post)?**
> Middleware that runs before or after certain operations.
```js
// Hash password before saving
userSchema.pre('save', async function(next) {
  if (this.isModified('password')) {
    this.password = await bcrypt.hash(this.password, 12);
  }
  next();
});
```

---

**Q: What is an index in MongoDB and why use it?**
> An index speeds up query lookups. Without it, MongoDB scans every document (collection scan). Add index on fields you frequently query/sort by. Too many indexes slow down writes.
```js
userSchema.index({ email: 1 }); // ascending index on email
```

---

**Q: What is the MongoDB aggregation pipeline?**
> A sequence of stages that transform documents: `$match` (filter), `$group` (aggregate), `$sort`, `$project` (reshape), `$lookup` (join). Like SQL GROUP BY + JOIN but in stages.

---

# ══════════════════════════════════════
# MySQL / PostgreSQL
# ══════════════════════════════════════

**Q: What is a relational database?**
> Data stored in tables (rows and columns) with defined relationships via primary and foreign keys. Enforces ACID (Atomicity, Consistency, Isolation, Durability) for data integrity.

---

**Q: What are primary key and foreign key?**
> **Primary key:** Uniquely identifies each row in a table (e.g., `id`).
> **Foreign key:** A field in one table that references the primary key of another table, creating a relationship.

---

**Q: What are SQL JOINs?**
> - **INNER JOIN:** Returns rows that match in BOTH tables.
> - **LEFT JOIN:** Returns all rows from left table + matched rows from right (NULLs if no match).
> - **RIGHT JOIN:** Opposite of LEFT.
> - **FULL JOIN:** All rows from both tables.

---

**Q: What is database normalization?**
> Organizing tables to reduce redundancy. 1NF: atomic values. 2NF: no partial dependencies. 3NF: no transitive dependencies. Goal: store each fact once and reference it.

---

**Q: What is an index in SQL?**
> A data structure that speeds up queries on a column. Creates a sorted lookup. Use on `WHERE`, `JOIN`, `ORDER BY` columns. Slows down writes (index must be updated). Don't index every column.

---

**Q: What is a transaction?**
> A group of SQL operations that execute as a unit. Either ALL succeed or ALL are rolled back. Ensures data consistency.
```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 500 WHERE id = 1;
UPDATE accounts SET balance = balance + 500 WHERE id = 2;
COMMIT; -- or ROLLBACK on error
```

---

**Q: What is the difference between TRUNCATE and DELETE?**
> `DELETE` removes rows one by one, can have WHERE clause, fires triggers, is logged. `TRUNCATE` removes ALL rows instantly, cannot have WHERE, faster, resets auto-increment.

---

**Q: What is GROUP BY and HAVING?**
> `GROUP BY` groups rows by a column for aggregation. `HAVING` filters the grouped results (like `WHERE` but for groups).
```sql
SELECT category, COUNT(*) as total, AVG(price) as avg_price
FROM products
GROUP BY category
HAVING COUNT(*) > 5;
```

---

**Q: PostgreSQL vs MySQL?**
> Both are relational. PostgreSQL is more feature-rich: JSONB support, advanced indexing, window functions, better standards compliance, great for complex queries. MySQL is simpler, faster for simple read-heavy apps, very common in PHP/Laravel stack. I use MySQL with Laravel and know PostgreSQL basics.

---

# ══════════════════════════════════════
# PHP / LARAVEL
# ══════════════════════════════════════

**Q: What is Laravel?**
> Laravel is a PHP web framework following MVC architecture. It provides routing, Eloquent ORM, Blade templating, built-in auth, migrations, Artisan CLI, queues, events, and more. Fastest way to build robust PHP applications.

---

**Q: Explain MVC in Laravel.**
> - **Model:** Eloquent class — represents a DB table, handles data logic and relationships
> - **View:** Blade template — HTML presentation layer
> - **Controller:** Receives HTTP request → calls model → returns response (view or JSON)
> **Flow:** `routes/web.php` → `Controller@method` → `Model::find()` → `return view()` or `response()->json()`

---

**Q: What is Eloquent ORM?**
> Laravel's Active Record ORM. Each model maps to a DB table. Provides expressive methods for CRUD without writing raw SQL. Supports relationships, scopes, mutators, accessors, and hooks.

---

**Q: What are Eloquent relationships?**
> - `hasOne` — User hasOne Profile
> - `hasMany` — User hasMany Posts
> - `belongsTo` — Post belongsTo User
> - `belongsToMany` — User belongsToMany Roles (pivot table)
> - `hasManyThrough` — Country has many Posts through Users

---

**Q: What is Laravel middleware?**
> Filters HTTP requests before they reach controllers. Built-in: `auth`, `guest`, `throttle`, `verified`. Custom: create with `php artisan make:middleware CheckRole` → register in `Kernel.php` → apply to routes.

---

**Q: What is Blade templating?**
> Laravel's templating engine. Compiles to plain PHP. Features: `@extends`, `@section`, `@yield` for layouts; `@if`, `@foreach`, `@forelse` for logic; `{{ $var }}` for echoing (auto-escaped); `{!! $html !!}` for raw HTML. `@component` for reusable UI blocks.

---

**Q: What are migrations and seeders?**
> **Migrations:** Version control for your database schema. Create/modify tables with PHP code. Run with `php artisan migrate`. Roll back with `php artisan migrate:rollback`.
> **Seeders:** Populate DB with test/sample data. `php artisan db:seed`. Use **factories** with Faker for realistic random data.

---

**Q: What is Laravel authentication?**
> Laravel provides `Breeze` (simple), `Jetstream` (advanced), or `Sanctum` (API tokens). The built-in `Auth` facade handles login, logout, registration, password hashing, session management. `auth()->user()` gives the current user. Routes protected with `->middleware('auth')`.

---

**Q: What are Laravel Guards and Providers?**
> **Guard:** defines how users are authenticated per request (session for web, token for API). **Provider:** defines how users are retrieved from storage (Eloquent model or DB table). Configured in `config/auth.php`. I use separate guards for admin panel and API.

---

**Q: What is Laravel Sanctum?**
> Simple token-based authentication for SPAs and mobile apps. Issues personal access tokens stored in DB. Better than full Passport for simple API auth. I used it in my Laravel API projects.

---

**Q: What is service container / dependency injection in Laravel?**
> Laravel's IoC container automatically resolves class dependencies. When a controller method type-hints a class, Laravel instantiates it automatically. Promotes loose coupling and testability.

---

**Q: What is the difference between `find()`, `findOrFail()`, `first()`, `firstOrFail()`?**
> - `find($id)` — returns model or `null`
> - `findOrFail($id)` — returns model or throws `ModelNotFoundException` (404)
> - `first()` — first result or `null`
> - `firstOrFail()` — first result or throws 404

---

**Q: What is eager loading vs lazy loading in Eloquent?**
> **Lazy loading (default):** Relationships loaded on access — causes N+1 queries (1 query for posts + 1 per post for user = N+1).
> **Eager loading:** Load relationships upfront with `with()` — 2 queries total.
```php
// BAD (N+1)
$posts = Post::all();
foreach ($posts as $post) { echo $post->user->name; } // 1 extra query per post

// GOOD (eager load)
$posts = Post::with('user')->get(); // 2 queries total
```

---

**Q: What are Artisan commands you use?**
```bash
php artisan make:model Product -mcr    # model + migration + controller
php artisan make:middleware CheckRole
php artisan make:request StoreProductRequest
php artisan migrate
php artisan migrate:rollback
php artisan db:seed
php artisan route:list
php artisan tinker       # REPL for testing code
php artisan cache:clear
php artisan config:clear
```

---

**Q: What is CSRF protection in Laravel?**
> Cross-Site Request Forgery — an attack where a malicious site tricks a logged-in user's browser into making unwanted requests. Laravel auto-generates a CSRF token for every session and validates it on POST/PUT/DELETE requests. In Blade: `@csrf`. For APIs using Sanctum, CSRF is handled differently.

---

**Q: What is soft delete in Laravel?**
> Instead of permanently deleting a record, adds a `deleted_at` timestamp. Record is hidden from normal queries but still in DB. Use `SoftDeletes` trait in model. Restore with `restore()`. Permanently delete with `forceDelete()`.

---

# ══════════════════════════════════════
# REST API / GRAPHQL
# ══════════════════════════════════════

**Q: What is a RESTful API?**
> Architectural style for APIs. Uses HTTP methods (GET/POST/PUT/PATCH/DELETE) on resource URLs. Stateless — each request has all info needed. Returns JSON. Follows conventions: `GET /users` (list), `GET /users/1` (single), `POST /users` (create), `PUT /users/1` (update), `DELETE /users/1` (delete).

---

**Q: What is GraphQL?**
> Query language for APIs. Single endpoint (`/graphql`). Client requests EXACTLY the fields it needs — no over-fetching or under-fetching. Uses Schema, Queries (read), Mutations (write), Resolvers.

---

**Q: REST vs GraphQL?**

| | REST | GraphQL |
|---|---|---|
| Endpoints | Multiple | Single |
| Data control | Server decides | Client decides |
| Over-fetching | Common | Eliminated |
| Versioning | `/api/v1/`, `/v2/` | Schema evolution |
| Best for | Simple CRUD | Complex, nested data |

---

**Q: What are HTTP status codes?**
> 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Server Error.

---

# ══════════════════════════════════════
# GIT
# ══════════════════════════════════════

**Q: What is Git and why use it?**
> Distributed version control system. Tracks changes, enables collaboration, allows branching, rollback, and history. Every developer has a full copy of the repo locally.

---

**Q: What is the difference between `git merge` and `git rebase`?**
> `merge` combines branches and creates a merge commit — preserves full history. `rebase` replays commits on top of another branch — creates a linear history but rewrites commits. I use merge for team collaboration and rebase for cleaning up local feature branches before PR.

---

**Q: What is `.gitignore`?**
> Tells Git which files NOT to track. Always ignore: `node_modules/`, `.env`, `vendor/`, `dist/`, `*.log`, `.DS_Store`.

---

**Q: What is the difference between `git pull` and `git fetch`?**
> `fetch` downloads changes from remote but doesn't merge. `pull` = `fetch` + `merge`. I use `fetch` first to review changes, then merge manually on important branches.

---

**Q: What are common Git commands?**
```bash
git init / git clone <url>
git status / git log --oneline
git add . / git commit -m "message"
git push origin main / git pull origin main
git checkout -b feature/login  # create and switch branch
git merge feature/login        # merge into current branch
git stash / git stash pop      # save/restore uncommitted work
git reset HEAD~1               # undo last commit, keep changes
git revert <commit-hash>       # create new commit that undoes a commit
```

---

# ══════════════════════════════════════
# DOCKER
# ══════════════════════════════════════

**Q: What is Docker and why use it?**
> Docker packages an app and ALL its dependencies into a container — isolated, reproducible environment. "Works on my machine" problem eliminated. Same container runs on any machine, any server.

---

**Q: What is the difference between image and container?**
> **Image:** Blueprint/template (read-only). Built from a `Dockerfile`.
> **Container:** Running instance of an image. You can run multiple containers from one image.

---

**Q: What is docker-compose?**
> Tool to define and run multi-container apps with a `docker-compose.yml` file. One command (`docker-compose up`) starts your app + database + any other services together.

---

**Q: What is a Dockerfile?**
> Text file with instructions to build a Docker image. `FROM` (base image), `WORKDIR`, `COPY`, `RUN` (install packages), `EXPOSE` (port), `CMD` (start command).

---

**Q: What is a volume in Docker?**
> Persistent storage for containers. Container filesystem is ephemeral — data lost when container stops. Volumes persist data outside the container (e.g. database files).

---

# ══════════════════════════════════════
# DEPLOYMENT / CI-CD
# ══════════════════════════════════════

**Q: How do you deploy a Node.js/Next.js app?**
> 1. **Vercel** — push to GitHub, auto-deploys Next.js (simplest)
> 2. **VPS (Ubuntu):** SSH in → install Node.js → clone repo → `npm install && npm run build` → run with **PM2** (`pm2 start server.js`) → Nginx as reverse proxy
> 3. **Docker:** Build image → push to registry → pull and run on server

---

**Q: What is PM2?**
> Process manager for Node.js. Keeps app running after crashes, auto-restarts, manages logs, allows running multiple apps. `pm2 start server.js --name myapp`, `pm2 logs`, `pm2 restart myapp`.

---

**Q: What is Nginx?**
> Web server / reverse proxy. Sits in front of your Node.js app, forwards requests to it, handles SSL termination, serves static files, load balancing.

---

**Q: What is CI/CD?**
> **CI (Continuous Integration):** Auto-run tests on every push/PR to catch bugs early.
> **CD (Continuous Deployment):** Auto-deploy to server when tests pass.
> I use GitHub Actions for simple CI/CD pipelines.

---

# ══════════════════════════════════════
# WEB SECURITY
# ══════════════════════════════════════

**Q: What is XSS and how to prevent it?**
> Cross-Site Scripting — injecting malicious scripts into web pages. Prevention: escape output (React does this automatically), use Content Security Policy headers, never use `dangerouslySetInnerHTML` with user input.

---

**Q: What is SQL Injection and how to prevent it?**
> Injecting SQL code into inputs to manipulate queries. Prevention: use parameterized queries / prepared statements, ORMs (Eloquent, Mongoose) handle this automatically.

---

**Q: What is CSRF and how to prevent it?**
> Cross-Site Request Forgery — trick browser into making unauthorized requests. Prevention: CSRF tokens (Laravel does this automatically for web), SameSite cookie flag, token-based auth for APIs.

---

**Q: What is HTTPS and why is it important?**
> HTTP with SSL/TLS encryption. Encrypts data between browser and server. Prevents man-in-the-middle attacks. Required for production. JWT tokens in cookies should only be sent over HTTPS.

---

**Q: How do you store passwords securely?**
> NEVER store plain text. Use bcrypt with a cost factor of 10-12. bcrypt automatically generates a salt and includes it in the hash. One-way — cannot be reversed, only verified with `bcrypt.compare()`.

---
