# 💻 Code Interview Q&A — Full Stack JavaScript Developer (Xponent, Chattogram)
> Prepared for: **Anik Paul** | Covers: React · Node.js/Express · MongoDB · MySQL · PHP/Laravel · Auth · Docker
> ⚠️ These are the most likely live-coding scenarios. Practice explaining WHILE writing.

---

## 🟡 PART A: JavaScript Fundamentals (Could ask these warm-ups)

---

### A1. Reverse a string

```js
function reverseString(str) {
  return str.split('').reverse().join('');
}
console.log(reverseString('hello')); // "olleh"
```
**Explain:** Split into array → reverse array → join back to string.

---

### A2. Check if a string is a palindrome

```js
function isPalindrome(str) {
  const clean = str.toLowerCase().replace(/[^a-z0-9]/g, '');
  return clean === clean.split('').reverse().join('');
}
console.log(isPalindrome('racecar')); // true
console.log(isPalindrome('hello'));   // false
```

---

### A3. Find duplicates in an array

```js
function findDuplicates(arr) {
  const seen = {};
  const duplicates = [];
  arr.forEach(item => {
    if (seen[item]) duplicates.push(item);
    else seen[item] = true;
  });
  return duplicates;
}
console.log(findDuplicates([1, 2, 3, 2, 4, 1])); // [2, 1]
```

---

### A4. Filter objects from an array (like filtering issues by status)

```js
const issues = [
  { id: 1, title: 'Broken road', status: 'open' },
  { id: 2, title: 'Street light', status: 'resolved' },
  { id: 3, title: 'Water leak', status: 'open' },
];

const openIssues = issues.filter(issue => issue.status === 'open');
console.log(openIssues);
// [{ id:1, ... }, { id:3, ... }]
```

---

### A5. Async/Await with error handling

```js
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) throw new Error('User not found');
    const user = await response.json();
    return user;
  } catch (error) {
    console.error('Error:', error.message);
    return null;
  }
}
```
**Explain:** async/await makes async code readable. try/catch handles both network errors and non-OK HTTP responses.

---

### A6. Debounce function (commonly asked)

```js
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// Usage: search input that only fires after 500ms of no typing
const handleSearch = debounce((query) => {
  console.log('Searching for:', query);
}, 500);
```
**Explain:** Debounce delays execution until user stops typing. Useful for search inputs to avoid firing an API call on every keystroke.

---

## ⚛️ PART B: React Code (Most Likely Live Coding)

---

### B1. Simple Login Form (React — Controlled Component)

```jsx
import { useState } from 'react';

export default function LoginForm() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.email || !form.password) {
      setError('All fields are required');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      // Redirect or update auth state
      console.log('Logged in:', data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <input
        type="email"
        name="email"
        placeholder="Email"
        value={form.email}
        onChange={handleChange}
      />
      <input
        type="password"
        name="password"
        placeholder="Password"
        value={form.password}
        onChange={handleChange}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

**What to explain:**
- Controlled component — input values driven by state
- `handleChange` uses computed property `[e.target.name]` to handle all fields with one function
- Validation before API call
- Loading state prevents double submission
- Error handled from both validation and API response

---

### B2. Register Form (React)

```jsx
import { useState } from 'react';

export default function RegisterForm() {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!form.name || !form.email || !form.password) {
      return setError('All fields are required');
    }
    if (form.password !== form.confirm) {
      return setError('Passwords do not match');
    }
    if (form.password.length < 6) {
      return setError('Password must be at least 6 characters');
    }

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.name, email: form.email, password: form.password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      setSuccess('Account created! Please login.');
      setForm({ name: '', email: '', password: '', confirm: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Register</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}

      <input name="name" placeholder="Full Name" value={form.name} onChange={handleChange} />
      <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} />
      <input name="password" type="password" placeholder="Password" value={form.password} onChange={handleChange} />
      <input name="confirm" type="password" placeholder="Confirm Password" value={form.confirm} onChange={handleChange} />
      <button type="submit">Register</button>
    </form>
  );
}
```

---

### B3. Add User Form (React — CRUD Frontend)

```jsx
import { useState, useEffect } from 'react';

export default function UserManager() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ name: '', email: '', role: 'user' });
  const [error, setError] = useState('');

  // Fetch users on load
  useEffect(() => {
    fetch('/api/users')
      .then(r => r.json())
      .then(data => setUsers(data.users || []));
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.name || !form.email) return setError('Name and email required');

    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      setUsers([...users, data.user]);   // update list without re-fetch
      setForm({ name: '', email: '', role: 'user' });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    await fetch(`/api/users/${id}`, { method: 'DELETE' });
    setUsers(users.filter(u => u._id !== id));
  };

  return (
    <div>
      <h2>Users</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <form onSubmit={handleAdd}>
        <input name="name" placeholder="Name" value={form.name} onChange={handleChange} />
        <input name="email" placeholder="Email" value={form.email} onChange={handleChange} />
        <select name="role" value={form.role} onChange={handleChange}>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit">Add User</button>
      </form>

      <ul>
        {users.map(user => (
          <li key={user._id}>
            {user.name} — {user.email} ({user.role})
            <button onClick={() => handleDelete(user._id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**What to explain:**
- useEffect runs once on mount to load users
- On successful add, update local state without refetching (optimistic UI)
- On delete, filter the local array
- All operations are tied to API endpoints

---

### B4. Custom useAuth Hook (React)

```jsx
// hooks/useAuth.js
import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in (e.g., token in cookie)
    fetch('/api/auth/me')
      .then(r => r.ok ? r.json() : null)
      .then(data => setUser(data?.user || null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message);
    setUser(data.user);
  };

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

**Usage:**
```jsx
const { user, login, logout } = useAuth();
```

**Explain:** AuthContext provides user state globally. Any component can call `useAuth()` without prop drilling. The `login` and `logout` functions handle API calls and update the shared state.

---

## 🟢 PART C: Node.js / Express Backend Code

---

### C1. Express Server Setup

```js
// server.js
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// Middleware
app.use(cors({ origin: process.env.CLIENT_URL, credentials: true }));
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);

// Error Handler (must be last)
app.use(errorHandler);

// DB + Start
mongoose.connect(process.env.MONGO_URI)
  .then(() => {
    console.log('MongoDB connected');
    app.listen(process.env.PORT || 5000, () => console.log('Server running'));
  })
  .catch(err => console.error(err));
```

---

### C2. User Model (Mongoose)

```js
// models/User.js
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  name:     { type: String, required: true, trim: true },
  email:    { type: String, required: true, unique: true, lowercase: true },
  password: { type: String, required: true, select: false }, // hidden by default
  role:     { type: String, enum: ['user', 'admin'], default: 'user' },
}, { timestamps: true });

// Hash password before saving
userSchema.pre('save', async function (next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 10);
  next();
});

module.exports = mongoose.model('User', userSchema);
```

**Explain:**
- `select: false` hides password from all queries by default
- `pre('save')` hook auto-hashes password — you never store plain text
- `isModified('password')` check prevents re-hashing on unrelated updates

---

### C3. Auth Routes + Controller (Register & Login)

```js
// routes/auth.js
const express = require('express');
const router = express.Router();
const { register, login, getMe, logout } = require('../controllers/authController');
const protect = require('../middleware/protect');

router.post('/register', register);
router.post('/login', login);
router.get('/me', protect, getMe);
router.post('/logout', logout);

module.exports = router;
```

```js
// controllers/authController.js
const User = require('../models/User');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const signToken = (userId) =>
  jwt.sign({ id: userId }, process.env.JWT_SECRET, { expiresIn: '7d' });

const sendToken = (res, user, statusCode) => {
  const token = signToken(user._id);
  res.cookie('token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
  });
  res.status(statusCode).json({
    success: true,
    user: { _id: user._id, name: user.name, email: user.email, role: user.role },
  });
};

exports.register = async (req, res, next) => {
  try {
    const { name, email, password } = req.body;
    if (!name || !email || !password) {
      return res.status(400).json({ success: false, message: 'All fields required' });
    }
    const existing = await User.findOne({ email });
    if (existing) return res.status(400).json({ success: false, message: 'Email already in use' });

    const user = await User.create({ name, email, password });
    sendToken(res, user, 201);
  } catch (err) {
    next(err);
  }
};

exports.login = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    if (!email || !password)
      return res.status(400).json({ success: false, message: 'Email and password required' });

    const user = await User.findOne({ email }).select('+password');
    if (!user || !(await bcrypt.compare(password, user.password)))
      return res.status(401).json({ success: false, message: 'Invalid credentials' });

    sendToken(res, user, 200);
  } catch (err) {
    next(err);
  }
};

exports.getMe = async (req, res) => {
  const user = await User.findById(req.user.id);
  res.json({ success: true, user });
};

exports.logout = (req, res) => {
  res.clearCookie('token');
  res.json({ success: true, message: 'Logged out' });
};
```

---

### C4. Auth Middleware (protect route)

```js
// middleware/protect.js
const jwt = require('jsonwebtoken');
const User = require('../models/User');

module.exports = async (req, res, next) => {
  try {
    // Get token from httpOnly cookie or Authorization header
    let token = req.cookies.token;
    if (!token && req.headers.authorization?.startsWith('Bearer ')) {
      token = req.headers.authorization.split(' ')[1];
    }

    if (!token) return res.status(401).json({ message: 'Not authorized' });

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = await User.findById(decoded.id);
    if (!req.user) return res.status(401).json({ message: 'User not found' });

    next();
  } catch (err) {
    return res.status(401).json({ message: 'Token invalid or expired' });
  }
};
```

---

### C5. Role-Based Middleware (admin only)

```js
// middleware/authorize.js
module.exports = (...roles) => (req, res, next) => {
  if (!roles.includes(req.user.role)) {
    return res.status(403).json({ message: 'Access denied' });
  }
  next();
};

// Usage in route:
// router.delete('/:id', protect, authorize('admin'), deleteUser);
```

---

### C6. User CRUD Routes + Controller

```js
// routes/users.js
const express = require('express');
const router = express.Router();
const { getUsers, addUser, deleteUser } = require('../controllers/userController');
const protect = require('../middleware/protect');
const authorize = require('../middleware/authorize');

router.get('/', protect, authorize('admin'), getUsers);
router.post('/', protect, authorize('admin'), addUser);
router.delete('/:id', protect, authorize('admin'), deleteUser);

module.exports = router;
```

```js
// controllers/userController.js
const User = require('../models/User');

exports.getUsers = async (req, res, next) => {
  try {
    const users = await User.find().select('-password');
    res.json({ success: true, users });
  } catch (err) { next(err); }
};

exports.addUser = async (req, res, next) => {
  try {
    const { name, email, password, role } = req.body;
    const user = await User.create({ name, email, password, role });
    res.status(201).json({ success: true, user });
  } catch (err) { next(err); }
};

exports.deleteUser = async (req, res, next) => {
  try {
    await User.findByIdAndDelete(req.params.id);
    res.json({ success: true, message: 'User deleted' });
  } catch (err) { next(err); }
};
```

---

### C7. Centralized Error Handler

```js
// middleware/errorHandler.js
module.exports = (err, req, res, next) => {
  console.error(err.stack);
  const status = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';

  // Mongoose duplicate key error
  if (err.code === 11000) {
    return res.status(400).json({ success: false, message: 'Duplicate field value' });
  }
  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const msg = Object.values(err.errors).map(e => e.message).join(', ');
    return res.status(400).json({ success: false, message: msg });
  }

  res.status(status).json({ success: false, message });
};
```

---

## 🐬 PART D: MySQL / SQL Queries (If they ask SQL)

---

### D1. Create Users Table

```sql
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role ENUM('user', 'admin') DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### D2. Insert a User

```sql
INSERT INTO users (name, email, password, role)
VALUES ('Anik Paul', 'anik@example.com', 'hashed_password', 'admin');
```

---

### D3. Get Users with JOIN (orders example)

```sql
SELECT u.name, u.email, COUNT(o.id) AS total_orders
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id
ORDER BY total_orders DESC;
```

---

### D4. Update a Record

```sql
UPDATE users SET role = 'admin' WHERE email = 'anik@example.com';
```

---

### D5. Delete a Record

```sql
DELETE FROM users WHERE id = 5;
```

---

## 🐘 PART E: PHP / Laravel Code (If they test Laravel)

---

### E1. Laravel Route + Controller (User CRUD)

```php
// routes/api.php
Route::middleware('auth:sanctum')->group(function () {
    Route::get('/users', [UserController::class, 'index']);
    Route::post('/users', [UserController::class, 'store']);
    Route::delete('/users/{id}', [UserController::class, 'destroy']);
});
```

```php
// app/Http/Controllers/UserController.php
<?php
namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function index()
    {
        return response()->json(User::all());
    }

    public function store(Request $request)
    {
        $request->validate([
            'name'     => 'required|string|max:100',
            'email'    => 'required|email|unique:users',
            'password' => 'required|min:6',
        ]);

        $user = User::create([
            'name'     => $request->name,
            'email'    => $request->email,
            'password' => Hash::make($request->password),
        ]);

        return response()->json($user, 201);
    }

    public function destroy($id)
    {
        User::findOrFail($id)->delete();
        return response()->json(['message' => 'User deleted']);
    }
}
```

---

### E2. Laravel Auth Middleware (Custom Role Check)

```php
// app/Http/Middleware/CheckAdmin.php
<?php
namespace App\Http\Middleware;

use Closure;

class CheckAdmin
{
    public function handle($request, Closure $next)
    {
        if (auth()->check() && auth()->user()->role === 'admin') {
            return $next($request);
        }
        return response()->json(['message' => 'Access denied'], 403);
    }
}
```

---

## 🐳 PART F: Docker (Basic — Show You Know)

---

### F1. Simple Dockerfile for Node.js App

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 5000
CMD ["node", "server.js"]
```

---

### F2. docker-compose.yml (Node + MongoDB)

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MONGO_URI=mongodb://mongo:27017/myapp
      - JWT_SECRET=supersecret
      - NODE_ENV=production
    depends_on:
      - mongo

  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db

volumes:
  mongodata:
```

**Explain:** `depends_on` ensures MongoDB starts before the app. `volumes` persists data so it survives container restarts. The app container connects to MongoDB using the service name `mongo` as the hostname.

---

## 📐 PART G: Next.js Specific Code

---

### G1. Next.js Middleware for Auth (App Router)

```js
// middleware.js (project root)
import { NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

export async function middleware(req) {
  const token = req.cookies.get('token')?.value;

  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET);
    await jwtVerify(token, secret);
    return NextResponse.next();
  } catch {
    return NextResponse.redirect(new URL('/login', req.url));
  }
}

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*'],
};
```

---

### G2. Next.js API Route (App Router)

```js
// app/api/users/route.js
import { NextResponse } from 'next/server';
import connectDB from '@/lib/db';
import User from '@/models/User';

export async function GET() {
  await connectDB();
  const users = await User.find().select('-password');
  return NextResponse.json({ users });
}

export async function POST(req) {
  await connectDB();
  const body = await req.json();
  const { name, email, password } = body;

  if (!name || !email || !password) {
    return NextResponse.json({ message: 'All fields required' }, { status: 400 });
  }

  const existing = await User.findOne({ email });
  if (existing) {
    return NextResponse.json({ message: 'Email already in use' }, { status: 400 });
  }

  const user = await User.create({ name, email, password });
  return NextResponse.json({ user }, { status: 201 });
}
```

---

### G3. Server Component with Data Fetching (Next.js App Router)

```jsx
// app/issues/page.jsx (Server Component — no 'use client')
import connectDB from '@/lib/db';
import Issue from '@/models/Issue';

export default async function IssuesPage() {
  await connectDB();
  const issues = await Issue.find({ status: 'open' }).lean();

  return (
    <div>
      <h1>Open Issues</h1>
      {issues.map(issue => (
        <div key={issue._id.toString()}>
          <h3>{issue.title}</h3>
          <p>{issue.description}</p>
        </div>
      ))}
    </div>
  );
}
```

**Explain:** No API call needed — the server component directly queries the database. This runs on the server, so no sensitive code is exposed to the client.

---

## 📝 PART H: What to Say When Explaining Code in Interview

---

When writing any code live, narrate your thought process:

> **"First I think about the structure — I need a route, a controller, and a model. Let me start with the model to define the data shape..."**

> **"I'm using try/catch here because this is an async operation and I want to handle errors properly instead of crashing the server..."**

> **"I'm validating input before hitting the database — this prevents bad data and gives the user a clear error message..."**

> **"I store the password as a hash using bcrypt — never plain text. The hash is one-way, so even if the database leaks, passwords are safe..."**

> **"This middleware runs before the controller. It checks the JWT, and if it's valid, attaches the user to req.user so any downstream handler knows who made the request..."**

> **"On the frontend, I'm using controlled components — every keystroke updates state, and the input's value is always driven by that state. This gives me full control for validation..."**

---

## ✅ Quick Reference: Architecture You Can Draw/Explain

```
CLIENT (React/Next.js)
    │
    │  HTTP Request (with JWT in httpOnly cookie or Authorization header)
    ▼
EXPRESS SERVER
    │
    ├── CORS middleware
    ├── body-parser
    ├── Auth middleware (verify JWT → attach req.user)
    ├── Role middleware (check req.user.role)
    │
    ▼
CONTROLLER (business logic)
    │
    ▼
MODEL (Mongoose / Sequelize)
    │
    ▼
DATABASE (MongoDB / MySQL)
    │
    ◄── returns data
    │
CONTROLLER builds response
    │
    ▼
CLIENT receives JSON response
    │
React updates state → UI re-renders
```

**Explain this flow for any feature they ask about. It shows system thinking.**

---

*End of Code Q&A | File 2 of 2*
*Good luck tomorrow, Anik! You've built real projects — trust your experience.*
