# 💻 COMPLETE CODE IMPLEMENTATIONS — INTERVIEW READY
### Every feature they might ask you to write live

---

# ══════════════════════════════════════
# FEATURE 1: USER REGISTER + LOGIN
# Full Frontend + Backend
# ══════════════════════════════════════

## BACKEND — Express + MongoDB + JWT

```js
// ── models/User.js ──────────────────────────────────────
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  name:     { type: String, required: true, trim: true },
  email:    { type: String, required: true, unique: true, lowercase: true },
  password: { type: String, required: true, minlength: 6 },
  role:     { type: String, enum: ['user', 'admin'], default: 'user' },
}, { timestamps: true });

// Hash password before save
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 12);
  next();
});

// Compare password method
userSchema.methods.matchPassword = function(enteredPassword) {
  return bcrypt.compare(enteredPassword, this.password);
};

module.exports = mongoose.model('User', userSchema);
```

```js
// ── middleware/authMiddleware.js ─────────────────────────
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const protect = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer '))
      return res.status(401).json({ message: 'Not authorized' });

    const token = authHeader.split(' ')[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = await User.findById(decoded.id).select('-password');
    if (!req.user) return res.status(401).json({ message: 'User not found' });
    next();
  } catch {
    res.status(401).json({ message: 'Invalid token' });
  }
};

const adminOnly = (req, res, next) => {
  if (req.user?.role !== 'admin')
    return res.status(403).json({ message: 'Admin access only' });
  next();
};

module.exports = { protect, adminOnly };
```

```js
// ── controllers/authController.js ───────────────────────
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const generateToken = (id) =>
  jwt.sign({ id }, process.env.JWT_SECRET, { expiresIn: '7d' });

// POST /api/auth/register
const register = async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password)
      return res.status(400).json({ message: 'All fields are required' });

    const userExists = await User.findOne({ email });
    if (userExists)
      return res.status(409).json({ message: 'Email already registered' });

    const user = await User.create({ name, email, password });
    const token = generateToken(user._id);

    res.status(201).json({
      token,
      user: { id: user._id, name: user.name, email: user.email, role: user.role },
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// POST /api/auth/login
const login = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password)
      return res.status(400).json({ message: 'Email and password are required' });

    const user = await User.findOne({ email });
    if (!user) return res.status(401).json({ message: 'Invalid credentials' });

    const isMatch = await user.matchPassword(password);
    if (!isMatch) return res.status(401).json({ message: 'Invalid credentials' });

    const token = generateToken(user._id);

    res.json({
      token,
      user: { id: user._id, name: user.name, email: user.email, role: user.role },
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error' });
  }
};

// GET /api/auth/profile  (protected)
const getProfile = async (req, res) => {
  res.json(req.user);
};

module.exports = { register, login, getProfile };
```

```js
// ── routes/authRoutes.js ─────────────────────────────────
const express = require('express');
const router = express.Router();
const { register, login, getProfile } = require('../controllers/authController');
const { protect } = require('../middleware/authMiddleware');

router.post('/register', register);
router.post('/login', login);
router.get('/profile', protect, getProfile);

module.exports = router;
```

```js
// ── server.js ────────────────────────────────────────────
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();

app.use(cors({ origin: process.env.CLIENT_URL, credentials: true }));
app.use(express.json());

app.use('/api/auth', require('./routes/authRoutes'));

// Global error handler
app.use((err, req, res, next) => {
  res.status(err.statusCode || 500).json({ message: err.message || 'Server Error' });
});

mongoose.connect(process.env.MONGO_URI)
  .then(() => {
    console.log('MongoDB connected');
    app.listen(process.env.PORT || 5000, () => console.log('Server running'));
  })
  .catch(err => console.error(err));
```

---

## FRONTEND — Next.js Register + Login Pages

```jsx
// ── context/AuthContext.jsx ──────────────────────────────
'use client';
import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null);
  const [token, setToken] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const storedUser  = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setToken(storedToken);
    }
  }, []);

  const login = (userData, tokenValue) => {
    localStorage.setItem('user',  JSON.stringify(userData));
    localStorage.setItem('token', tokenValue);
    setUser(userData);
    setToken(tokenValue);
  };

  const logout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setUser(null);
    setToken(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

```jsx
// ── app/(auth)/register/page.jsx ────────────────────────
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function RegisterPage() {
  const [form, setForm]     = useState({ name: '', email: '', password: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');
  const { login } = useAuth();
  const router = useRouter();

  const validate = () => {
    const e = {};
    if (!form.name.trim())            e.name     = 'Name is required';
    if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Valid email required';
    if (form.password.length < 6)    e.password = 'Min 6 characters';
    if (form.password !== form.confirm) e.confirm = 'Passwords do not match';
    return e;
  };

  const handleChange = (e) =>
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    try {
      setLoading(true);
      setServerError('');
      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/register`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ name: form.name, email: form.email, password: form.password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      login(data.user, data.token);
      router.push('/dashboard');
    } catch (err) {
      setServerError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '60px auto', padding: 24 }}>
      <h2>Register</h2>
      {serverError && <p style={{ color: 'red' }}>{serverError}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <input name="name" placeholder="Full Name"
            value={form.name} onChange={handleChange} />
          {errors.name && <span style={{ color: 'red' }}>{errors.name}</span>}
        </div>
        <div>
          <input name="email" placeholder="Email"
            value={form.email} onChange={handleChange} />
          {errors.email && <span style={{ color: 'red' }}>{errors.email}</span>}
        </div>
        <div>
          <input name="password" type="password" placeholder="Password"
            value={form.password} onChange={handleChange} />
          {errors.password && <span style={{ color: 'red' }}>{errors.password}</span>}
        </div>
        <div>
          <input name="confirm" type="password" placeholder="Confirm Password"
            value={form.confirm} onChange={handleChange} />
          {errors.confirm && <span style={{ color: 'red' }}>{errors.confirm}</span>}
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <p>Already have an account? <Link href="/login">Login</Link></p>
    </div>
  );
}
```

```jsx
// ── app/(auth)/login/page.jsx ────────────────────────────
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const [form, setForm]       = useState({ email: '', password: '' });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleChange = (e) =>
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) { setError('All fields required'); return; }
    try {
      setLoading(true);
      setError('');
      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      login(data.user, data.token);
      router.push('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '60px auto', padding: 24 }}>
      <h2>Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <input name="email" placeholder="Email"
            value={form.email} onChange={handleChange} />
        </div>
        <div>
          <input name="password" type="password" placeholder="Password"
            value={form.password} onChange={handleChange} />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p>No account? <Link href="/register">Register</Link></p>
    </div>
  );
}
```

```jsx
// ── middleware.js — route protection ────────────────────
import { NextResponse } from 'next/server';

export function middleware(request) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;

  const protectedPaths = ['/dashboard', '/admin', '/profile'];
  const isProtected = protectedPaths.some(p => pathname.startsWith(p));

  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ['/dashboard/:path*', '/admin/:path*', '/profile/:path*'] };
```

---

# ══════════════════════════════════════
# FEATURE 2: ADD TO CART
# Full Frontend + Backend
# ══════════════════════════════════════

## BACKEND — Cart API

```js
// ── models/Cart.js ───────────────────────────────────────
const mongoose = require('mongoose');

const cartItemSchema = new mongoose.Schema({
  product:  { type: mongoose.Schema.Types.ObjectId, ref: 'Product', required: true },
  quantity: { type: Number, required: true, min: 1, default: 1 },
  price:    { type: Number, required: true },
});

const cartSchema = new mongoose.Schema({
  user:  { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, unique: true },
  items: [cartItemSchema],
}, { timestamps: true });

// Virtual: calculate total
cartSchema.virtual('total').get(function() {
  return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
});

module.exports = mongoose.model('Cart', cartSchema);
```

```js
// ── controllers/cartController.js ───────────────────────
const Cart    = require('../models/Cart');
const Product = require('../models/Product');

// GET /api/cart
const getCart = async (req, res) => {
  try {
    const cart = await Cart.findOne({ user: req.user._id }).populate('items.product', 'name image price');
    if (!cart) return res.json({ items: [], total: 0 });

    const total = cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    res.json({ items: cart.items, total });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

// POST /api/cart/add
const addToCart = async (req, res) => {
  try {
    const { productId, quantity = 1 } = req.body;

    const product = await Product.findById(productId);
    if (!product) return res.status(404).json({ message: 'Product not found' });

    let cart = await Cart.findOne({ user: req.user._id });

    if (!cart) {
      // First time — create cart
      cart = await Cart.create({
        user:  req.user._id,
        items: [{ product: productId, quantity, price: product.price }],
      });
    } else {
      const existingItem = cart.items.find(i => i.product.toString() === productId);
      if (existingItem) {
        // Product already in cart — increase quantity
        existingItem.quantity += quantity;
      } else {
        // New product — push to cart
        cart.items.push({ product: productId, quantity, price: product.price });
      }
      await cart.save();
    }

    await cart.populate('items.product', 'name image price');
    const total = cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    res.json({ items: cart.items, total });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

// PUT /api/cart/update
const updateQuantity = async (req, res) => {
  try {
    const { productId, quantity } = req.body;
    const cart = await Cart.findOne({ user: req.user._id });
    if (!cart) return res.status(404).json({ message: 'Cart not found' });

    const item = cart.items.find(i => i.product.toString() === productId);
    if (!item) return res.status(404).json({ message: 'Item not in cart' });

    if (quantity <= 0) {
      cart.items = cart.items.filter(i => i.product.toString() !== productId);
    } else {
      item.quantity = quantity;
    }
    await cart.save();
    res.json(cart);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

// DELETE /api/cart/remove/:productId
const removeFromCart = async (req, res) => {
  try {
    const cart = await Cart.findOne({ user: req.user._id });
    if (!cart) return res.status(404).json({ message: 'Cart not found' });

    cart.items = cart.items.filter(i => i.product.toString() !== req.params.productId);
    await cart.save();
    res.json({ message: 'Item removed', cart });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

// DELETE /api/cart/clear
const clearCart = async (req, res) => {
  try {
    await Cart.findOneAndUpdate({ user: req.user._id }, { items: [] });
    res.json({ message: 'Cart cleared' });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

module.exports = { getCart, addToCart, updateQuantity, removeFromCart, clearCart };
```

```js
// ── routes/cartRoutes.js ─────────────────────────────────
const express = require('express');
const router  = express.Router();
const { getCart, addToCart, updateQuantity, removeFromCart, clearCart } = require('../controllers/cartController');
const { protect } = require('../middleware/authMiddleware');

router.use(protect); // all cart routes require auth

router.get('/',                  getCart);
router.post('/add',              addToCart);
router.put('/update',            updateQuantity);
router.delete('/remove/:productId', removeFromCart);
router.delete('/clear',          clearCart);

module.exports = router;
```

---

## FRONTEND — Cart with Context (React)

```jsx
// ── context/CartContext.jsx ──────────────────────────────
'use client';
import { createContext, useContext, useReducer } from 'react';

// Reducer
function cartReducer(state, action) {
  switch (action.type) {
    case 'SET_CART':
      return { ...state, items: action.payload.items, total: action.payload.total };

    case 'ADD_ITEM': {
      const exists = state.items.find(i => i.product._id === action.payload._id);
      let newItems;
      if (exists) {
        newItems = state.items.map(i =>
          i.product._id === action.payload._id
            ? { ...i, quantity: i.quantity + 1 }
            : i
        );
      } else {
        newItems = [...state.items, { product: action.payload, quantity: 1, price: action.payload.price }];
      }
      const total = newItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
      return { items: newItems, total };
    }

    case 'REMOVE_ITEM': {
      const newItems = state.items.filter(i => i.product._id !== action.payload);
      const total    = newItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
      return { items: newItems, total };
    }

    case 'UPDATE_QTY': {
      const newItems = state.items.map(i =>
        i.product._id === action.payload.id
          ? { ...i, quantity: action.payload.qty }
          : i
      ).filter(i => i.quantity > 0);
      const total = newItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
      return { items: newItems, total };
    }

    case 'CLEAR_CART':
      return { items: [], total: 0 };

    default:
      return state;
  }
}

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cart, dispatch] = useReducer(cartReducer, { items: [], total: 0 });

  const addToCart = async (product, token) => {
    // Optimistic update
    dispatch({ type: 'ADD_ITEM', payload: product });

    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cart/add`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body:    JSON.stringify({ productId: product._id, quantity: 1 }),
      });
    } catch {
      // Rollback if API fails
      dispatch({ type: 'REMOVE_ITEM', payload: product._id });
    }
  };

  const removeFromCart = async (productId, token) => {
    dispatch({ type: 'REMOVE_ITEM', payload: productId });
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/cart/remove/${productId}`, {
      method:  'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
  };

  const clearCart = () => dispatch({ type: 'CLEAR_CART' });

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, clearCart, dispatch }}>
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
```

```jsx
// ── components/ProductCard.jsx ───────────────────────────
'use client';
import { useCart } from '@/context/CartContext';
import { useAuth } from '@/context/AuthContext';

export default function ProductCard({ product }) {
  const { addToCart, cart } = useCart();
  const { token } = useAuth();

  const isInCart = cart.items.some(i => i.product._id === product._id);

  return (
    <div style={{ border: '1px solid #ddd', padding: 16, borderRadius: 8 }}>
      <img src={product.image} alt={product.name} style={{ width: '100%', height: 200, objectFit: 'cover' }} />
      <h3>{product.name}</h3>
      <p>৳{product.price}</p>
      <button
        onClick={() => addToCart(product, token)}
        disabled={isInCart}
        style={{ background: isInCart ? '#888' : '#0070f3', color: '#fff', padding: '8px 16px', border: 'none', borderRadius: 4 }}
      >
        {isInCart ? 'Added ✓' : 'Add to Cart'}
      </button>
    </div>
  );
}
```

```jsx
// ── app/cart/page.jsx ────────────────────────────────────
'use client';
import { useCart } from '@/context/CartContext';
import { useAuth } from '@/context/AuthContext';

export default function CartPage() {
  const { cart, removeFromCart, dispatch } = useCart();
  const { token } = useAuth();

  const handleQtyChange = (productId, qty) => {
    dispatch({ type: 'UPDATE_QTY', payload: { id: productId, qty: Number(qty) } });
  };

  if (cart.items.length === 0)
    return <div style={{ padding: 40 }}><h2>Your cart is empty</h2></div>;

  return (
    <div style={{ maxWidth: 700, margin: '40px auto', padding: 24 }}>
      <h2>Your Cart ({cart.items.length} items)</h2>
      {cart.items.map(item => (
        <div key={item.product._id} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #eee', padding: '12px 0' }}>
          <div>
            <strong>{item.product.name}</strong>
            <p>৳{item.price} each</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <select
              value={item.quantity}
              onChange={e => handleQtyChange(item.product._id, e.target.value)}
            >
              {[1,2,3,4,5,6,7,8,9,10].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
            <span>৳{(item.price * item.quantity).toFixed(2)}</span>
            <button onClick={() => removeFromCart(item.product._id, token)}
              style={{ color: 'red', background: 'none', border: 'none', cursor: 'pointer' }}>
              Remove
            </button>
          </div>
        </div>
      ))}
      <div style={{ textAlign: 'right', marginTop: 16, fontSize: 20 }}>
        <strong>Total: ৳{cart.total.toFixed(2)}</strong>
      </div>
      <button style={{ width: '100%', padding: 14, background: '#0070f3', color: '#fff', border: 'none', borderRadius: 6, marginTop: 16, fontSize: 16 }}>
        Proceed to Checkout
      </button>
    </div>
  );
}
```

---

# ══════════════════════════════════════
# FEATURE 3: PRODUCT CRUD
# Admin — Create, Read, Update, Delete
# ══════════════════════════════════════

## BACKEND

```js
// ── models/Product.js ────────────────────────────────────
const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
  name:        { type: String, required: true, trim: true },
  description: { type: String, required: true },
  price:       { type: Number, required: true, min: 0 },
  image:       { type: String, default: '' },
  category:    { type: String, required: true },
  stock:       { type: Number, default: 0 },
  createdBy:   { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
}, { timestamps: true });

productSchema.index({ name: 'text', description: 'text' }); // for text search

module.exports = mongoose.model('Product', productSchema);
```

```js
// ── controllers/productController.js ────────────────────
const Product = require('../models/Product');

// GET /api/products — with search, filter, pagination
const getProducts = async (req, res) => {
  try {
    const { search, category, minPrice, maxPrice, sort = 'newest', page = 1, limit = 12 } = req.query;

    const query = {};
    if (search)   query.$text = { $search: search };
    if (category) query.category = category;
    if (minPrice || maxPrice) {
      query.price = {};
      if (minPrice) query.price.$gte = Number(minPrice);
      if (maxPrice) query.price.$lte = Number(maxPrice);
    }

    const sortOptions = {
      newest:     { createdAt: -1 },
      oldest:     { createdAt: 1 },
      priceAsc:   { price: 1 },
      priceDesc:  { price: -1 },
    };

    const skip = (Number(page) - 1) * Number(limit);
    const [products, total] = await Promise.all([
      Product.find(query).sort(sortOptions[sort] || sortOptions.newest).skip(skip).limit(Number(limit)),
      Product.countDocuments(query),
    ]);

    res.json({ products, total, pages: Math.ceil(total / Number(limit)), currentPage: Number(page) });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

// GET /api/products/:id
const getProduct = async (req, res) => {
  try {
    const product = await Product.findById(req.params.id);
    if (!product) return res.status(404).json({ message: 'Product not found' });
    res.json(product);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

// POST /api/products  (admin only)
const createProduct = async (req, res) => {
  try {
    const { name, description, price, image, category, stock } = req.body;
    const product = await Product.create({
      name, description, price, image, category, stock,
      createdBy: req.user._id,
    });
    res.status(201).json(product);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

// PUT /api/products/:id  (admin only)
const updateProduct = async (req, res) => {
  try {
    const product = await Product.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true });
    if (!product) return res.status(404).json({ message: 'Product not found' });
    res.json(product);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

// DELETE /api/products/:id  (admin only)
const deleteProduct = async (req, res) => {
  try {
    const product = await Product.findByIdAndDelete(req.params.id);
    if (!product) return res.status(404).json({ message: 'Product not found' });
    res.json({ message: 'Product deleted' });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

module.exports = { getProducts, getProduct, createProduct, updateProduct, deleteProduct };
```

---

## FRONTEND — Product List with Search + Filter

```jsx
// ── app/products/page.jsx ────────────────────────────────
'use client';
import { useState, useEffect, useCallback } from 'react';
import ProductCard from '@/components/ProductCard';

export default function ProductsPage() {
  const [products, setProducts]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState('');
  const [category, setCategory]   = useState('');
  const [sort, setSort]           = useState('newest');
  const [page, setPage]           = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, sort });
      if (search)   params.append('search',   search);
      if (category) params.append('category', category);

      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/products?${params}`);
      const data = await res.json();
      setProducts(data.products);
      setTotalPages(data.pages);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search, category, sort, page]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  // Debounce search
  const [searchInput, setSearchInput] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => { setSearch(searchInput); setPage(1); }, 500);
    return () => clearTimeout(timer);
  }, [searchInput]);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <h1>Products</h1>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <input
          placeholder="Search products..."
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: 4, flex: 1 }}
        />
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(1); }}>
          <option value="">All Categories</option>
          <option value="electronics">Electronics</option>
          <option value="clothing">Clothing</option>
          <option value="food">Food</option>
        </select>
        <select value={sort} onChange={e => setSort(e.target.value)}>
          <option value="newest">Newest</option>
          <option value="priceAsc">Price: Low to High</option>
          <option value="priceDesc">Price: High to Low</option>
        </select>
      </div>

      {/* Product Grid */}
      {loading ? (
        <p>Loading...</p>
      ) : products.length === 0 ? (
        <p>No products found.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 20 }}>
          {products.map(product => <ProductCard key={product._id} product={product} />)}
        </div>
      )}

      {/* Pagination */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32 }}>
        <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>← Prev</button>
        <span>Page {page} of {totalPages}</span>
        <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>Next →</button>
      </div>
    </div>
  );
}
```

---

# ══════════════════════════════════════
# FEATURE 4: CUSTOM HOOKS
# ══════════════════════════════════════

```js
// ── hooks/useFetch.js ────────────────────────────────────
import { useState, useEffect } from 'react';

export function useFetch(url, options = {}) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        const json = await res.json();
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [url]);

  return { data, loading, error };
}

// Usage:
// const { data, loading, error } = useFetch('/api/products');
```

```js
// ── hooks/useDebounce.js ─────────────────────────────────
import { useState, useEffect } from 'react';

export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage:
// const debouncedSearch = useDebounce(searchInput, 500);
// useEffect(() => { fetchResults(debouncedSearch); }, [debouncedSearch]);
```

```js
// ── hooks/useLocalStorage.js ─────────────────────────────
import { useState } from 'react';

export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      setStoredValue(value);
      localStorage.setItem(key, JSON.stringify(value));
    } catch (err) {
      console.error(err);
    }
  };

  return [storedValue, setValue];
}
```

---

# ══════════════════════════════════════
# FEATURE 5: PROTECTED ROUTE COMPONENT
# ══════════════════════════════════════

```jsx
// ── components/ProtectedRoute.jsx ───────────────────────
'use client';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user } = useAuth();
  const router   = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login');
    } else if (adminOnly && user.role !== 'admin') {
      router.push('/unauthorized');
    }
  }, [user, adminOnly, router]);

  if (!user) return <p>Redirecting...</p>;
  if (adminOnly && user.role !== 'admin') return null;

  return children;
}

// Usage:
// <ProtectedRoute><Dashboard /></ProtectedRoute>
// <ProtectedRoute adminOnly><AdminPanel /></ProtectedRoute>
```

---

# ══════════════════════════════════════
# FEATURE 6: PAGINATION COMPONENT
# ══════════════════════════════════════

```jsx
// ── components/Pagination.jsx ────────────────────────────
export default function Pagination({ currentPage, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 24 }}>
      <button onClick={() => onPageChange(1)} disabled={currentPage === 1}>«</button>
      <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}>‹</button>

      {pages.map(page => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          style={{
            padding: '6px 12px',
            background: page === currentPage ? '#0070f3' : '#fff',
            color:      page === currentPage ? '#fff' : '#000',
            border: '1px solid #ddd',
            borderRadius: 4,
            cursor: 'pointer',
          }}
        >
          {page}
        </button>
      ))}

      <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}>›</button>
      <button onClick={() => onPageChange(totalPages)} disabled={currentPage === totalPages}>»</button>
    </div>
  );
}
```

---

# ══════════════════════════════════════
# FEATURE 7: SEARCH WITH DEBOUNCE
# ══════════════════════════════════════

```jsx
// ── components/SearchBar.jsx ─────────────────────────────
'use client';
import { useState, useEffect } from 'react';

export default function SearchBar({ onSearch, placeholder = 'Search...' }) {
  const [input, setInput] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => onSearch(input), 500);
    return () => clearTimeout(timer); // cleanup on every keystroke
  }, [input, onSearch]);

  return (
    <input
      type="text"
      value={input}
      onChange={e => setInput(e.target.value)}
      placeholder={placeholder}
      style={{ padding: '10px 14px', border: '1px solid #ccc', borderRadius: 6, width: '100%' }}
    />
  );
}

// Usage:
// <SearchBar onSearch={(query) => setSearchQuery(query)} />
```

---

# ══════════════════════════════════════
# FEATURE 8: TOAST NOTIFICATION
# ══════════════════════════════════════

```jsx
// ── context/ToastContext.jsx ─────────────────────────────
'use client';
import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      {/* Toast UI */}
      <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {toasts.map(toast => (
          <div key={toast.id} style={{
            padding: '12px 20px',
            borderRadius: 8,
            color: '#fff',
            background: toast.type === 'success' ? '#22c55e' : toast.type === 'error' ? '#ef4444' : '#3b82f6',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

// Usage:
// const { addToast } = useToast();
// addToast('Item added to cart!', 'success');
// addToast('Something went wrong', 'error');
```

---

# ══════════════════════════════════════
# FEATURE 9: FILE UPLOAD — FRONTEND + BACKEND
# ══════════════════════════════════════

## BACKEND

```js
// ── middleware/upload.js ─────────────────────────────────
const multer = require('multer');
const path   = require('path');

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, 'uploads/'),
  filename:    (req, file, cb) => {
    const uniqueName = `${Date.now()}-${Math.round(Math.random() * 1e9)}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  },
});

const fileFilter = (req, file, cb) => {
  const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  allowed.includes(file.mimetype) ? cb(null, true) : cb(new Error('Images only!'), false);
};

const upload = multer({ storage, fileFilter, limits: { fileSize: 5 * 1024 * 1024 } }); // 5MB

module.exports = upload;

// In route:
// router.post('/products', protect, adminOnly, upload.single('image'), createProduct);
// Access: req.file.filename, req.file.path
```

## FRONTEND

```jsx
// ── components/ImageUpload.jsx ───────────────────────────
'use client';
import { useState } from 'react';

export default function ImageUpload({ onUpload }) {
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file)); // local preview
    handleUpload(file);
  };

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('image', file);

    try {
      setUploading(true);
      const token = localStorage.getItem('token');
      const res   = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/upload`, {
        method:  'POST',
        headers: { Authorization: `Bearer ${token}` },
        body:    formData,
        // DO NOT set Content-Type — browser sets multipart boundary automatically
      });
      const data = await res.json();
      onUpload(data.imageUrl); // pass URL back to parent
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      {uploading && <p>Uploading...</p>}
      {preview && <img src={preview} alt="Preview" style={{ width: 200, marginTop: 8, borderRadius: 8 }} />}
    </div>
  );
}
```

---

# ══════════════════════════════════════
# FEATURE 10: MYSQL / LARAVEL — AUTH + CRUD
# ══════════════════════════════════════

## LARAVEL AUTH

```php
<?php
// ── routes/api.php ───────────────────────────────────────
use App\Http\Controllers\AuthController;
use App\Http\Controllers\ProductController;

// Public
Route::post('/register', [AuthController::class, 'register']);
Route::post('/login',    [AuthController::class, 'login']);

// Protected
Route::middleware('auth:sanctum')->group(function () {
    Route::get('/profile', [AuthController::class, 'profile']);
    Route::post('/logout', [AuthController::class, 'logout']);

    // Admin only
    Route::middleware('role:admin')->group(function () {
        Route::apiResource('products', ProductController::class);
    });
});
```

```php
<?php
// ── app/Http/Controllers/AuthController.php ──────────────
namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function register(Request $request)
    {
        $request->validate([
            'name'     => 'required|string|max:255',
            'email'    => 'required|email|unique:users,email',
            'password' => 'required|string|min:6|confirmed', // needs password_confirmation field
        ]);

        $user  = User::create([
            'name'     => $request->name,
            'email'    => $request->email,
            'password' => Hash::make($request->password),
        ]);
        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json(['user' => $user, 'token' => $token], 201);
    }

    public function login(Request $request)
    {
        $request->validate([
            'email'    => 'required|email',
            'password' => 'required',
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            return response()->json(['message' => 'Invalid credentials'], 401);
        }

        $token = $user->createToken('auth_token')->plainTextToken;
        return response()->json(['user' => $user, 'token' => $token]);
    }

    public function profile(Request $request)
    {
        return response()->json($request->user());
    }

    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();
        return response()->json(['message' => 'Logged out']);
    }
}
```

```php
<?php
// ── app/Http/Controllers/ProductController.php ───────────
namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\Request;

class ProductController extends Controller
{
    public function index(Request $request)
    {
        $query = Product::query();

        if ($request->search) {
            $query->where('name', 'like', "%{$request->search}%")
                  ->orWhere('description', 'like', "%{$request->search}%");
        }
        if ($request->category) {
            $query->where('category', $request->category);
        }

        $products = $query->latest()->paginate(12);
        return response()->json($products);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name'        => 'required|string',
            'description' => 'required|string',
            'price'       => 'required|numeric|min:0',
            'category'    => 'required|string',
            'stock'       => 'integer|min:0',
        ]);
        $product = Product::create($validated);
        return response()->json($product, 201);
    }

    public function show(Product $product)   // route model binding
    {
        return response()->json($product);
    }

    public function update(Request $request, Product $product)
    {
        $product->update($request->validated());
        return response()->json($product);
    }

    public function destroy(Product $product)
    {
        $product->delete();
        return response()->json(['message' => 'Product deleted']);
    }
}
```

```php
<?php
// ── app/Http/Middleware/CheckRole.php ─────────────────────
namespace App\Http\Middleware;

use Closure;

class CheckRole
{
    public function handle($request, Closure $next, ...$roles)
    {
        if (!in_array(auth()->user()?->role, $roles)) {
            return response()->json(['message' => 'Forbidden'], 403);
        }
        return $next($request);
    }
}
// Register in Kernel.php: 'role' => CheckRole::class
// Use: Route::middleware('role:admin')
```

---

# ══════════════════════════════════════
# FEATURE 11: MYSQL QUERIES (Common)
# ══════════════════════════════════════

```sql
-- Create users table
CREATE TABLE users (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(100) NOT NULL,
  email      VARCHAR(150) NOT NULL UNIQUE,
  password   VARCHAR(255) NOT NULL,
  role       ENUM('user','admin') DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE products (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(200) NOT NULL,
  description TEXT,
  price       DECIMAL(10,2) NOT NULL,
  category    VARCHAR(100),
  stock       INT DEFAULT 0,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_category (category),   -- index for filter queries
  FULLTEXT  ft_search (name, description) -- for text search
);

-- Create orders table
CREATE TABLE orders (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  total      DECIMAL(10,2),
  status     ENUM('pending','processing','shipped','delivered','cancelled') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE order_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- JOIN: Get orders with user info
SELECT o.id, o.total, o.status, o.created_at,
       u.name AS user_name, u.email
FROM orders o
INNER JOIN users u ON o.user_id = u.id
ORDER BY o.created_at DESC;

-- JOIN: Get order items with product names
SELECT oi.quantity, oi.price, p.name AS product_name, o.status
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN orders   o ON oi.order_id   = o.id
WHERE o.user_id = 5;

-- Aggregation: Revenue by category
SELECT p.category,
       COUNT(DISTINCT o.id) AS total_orders,
       SUM(oi.quantity * oi.price) AS total_revenue,
       ROUND(AVG(oi.price), 2) AS avg_item_price
FROM order_items oi
JOIN products p ON oi.product_id = p.id
JOIN orders   o ON oi.order_id   = o.id
WHERE o.status = 'delivered'
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Pagination
SELECT * FROM products
WHERE category = 'electronics'
ORDER BY created_at DESC
LIMIT 12 OFFSET 24;  -- page 3 (offset = (page-1) * limit)
```

---

# ══════════════════════════════════════
# FEATURE 12: MONGODB — COMMON OPERATIONS
# ══════════════════════════════════════

```js
// ── Mongoose common patterns ─────────────────────────────

// Find with filter, sort, pagination, populate
const products = await Product
  .find({ category: 'electronics', price: { $gte: 100, $lte: 1000 } })
  .sort({ createdAt: -1 })
  .skip((page - 1) * limit)
  .limit(limit)
  .select('name price image category'); // only these fields

// Find one
const user = await User.findOne({ email }).select('+password'); // include hidden field

// Create
const user = await User.create({ name, email, password });

// Update
const updated = await Product.findByIdAndUpdate(
  id,
  { $set: { price: 299, stock: 50 } },
  { new: true, runValidators: true }
);

// Delete
await Product.findByIdAndDelete(id);

// Count
const total = await Product.countDocuments({ category: 'electronics' });

// Exists check
const exists = await User.exists({ email });

// Aggregation — sales report
const report = await Order.aggregate([
  { $match: { status: 'delivered' } },
  { $unwind: '$items' },
  { $group: {
    _id: '$items.product',
    totalSold: { $sum: '$items.quantity' },
    totalRevenue: { $sum: { $multiply: ['$items.price', '$items.quantity'] } },
  }},
  { $lookup: { from: 'products', localField: '_id', foreignField: '_id', as: 'product' } },
  { $unwind: '$product' },
  { $project: { name: '$product.name', totalSold: 1, totalRevenue: 1, _id: 0 } },
  { $sort: { totalRevenue: -1 } },
  { $limit: 10 },
]);
```

---

# ══════════════════════════════════════
# FEATURE 13: GLOBAL ERROR HANDLER + ASYNC WRAPPER
# ══════════════════════════════════════

```js
// ── middleware/errorHandler.js ───────────────────────────

// Wrap async controllers — no try/catch needed in every controller
const asyncHandler = fn => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

// Global error handler — register LAST in server.js
const errorHandler = (err, req, res, next) => {
  let statusCode = err.statusCode || 500;
  let message    = err.message    || 'Server Error';

  if (err.name === 'ValidationError')  { statusCode = 400; message = Object.values(err.errors).map(e => e.message).join(', '); }
  if (err.name === 'CastError')        { statusCode = 400; message = `Invalid ${err.path}`; }
  if (err.code === 11000)              { statusCode = 409; message = `${Object.keys(err.keyValue)} already exists`; }
  if (err.name === 'JsonWebTokenError'){ statusCode = 401; message = 'Invalid token'; }
  if (err.name === 'TokenExpiredError'){ statusCode = 401; message = 'Token expired, please login again'; }

  res.status(statusCode).json({
    success: false,
    message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
};

module.exports = { asyncHandler, errorHandler };

// With asyncHandler, controllers become:
// const getProduct = asyncHandler(async (req, res) => {
//   const product = await Product.findById(req.params.id);
//   if (!product) throw Object.assign(new Error('Product not found'), { statusCode: 404 });
//   res.json(product);
// });
```

---

# ══════════════════════════════════════
# FEATURE 14: DOCKER + docker-compose
# ══════════════════════════════════════

```dockerfile
# ── Dockerfile (Node.js/Express) ─────────────────────────
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 5000

CMD ["node", "server.js"]
```

```yaml
# ── docker-compose.yml ───────────────────────────────────
version: '3.8'

services:
  # Next.js frontend
  client:
    build: ./client
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:5000
    depends_on:
      - server

  # Express backend
  server:
    build: ./server
    ports:
      - "5000:5000"
    environment:
      - MONGO_URI=mongodb://mongo:27017/myapp
      - JWT_SECRET=supersecretkey123
      - NODE_ENV=production
    depends_on:
      - mongo

  # MongoDB
  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db  # persist data

  # MySQL (if using)
  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: myapp
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mongo_data:
  mysql_data:
```

---

# ══════════════════════════════════════
# QUICK REFERENCE — JAVASCRIPT PATTERNS
# ══════════════════════════════════════

```js
// ── Useful patterns you may be asked to write ────────────

// 1. Flatten nested array
const flat = arr => arr.reduce((a, b) => a.concat(Array.isArray(b) ? flat(b) : b), []);

// 2. Remove duplicates
const unique = arr => [...new Set(arr)];
const uniqueBy = (arr, key) => [...new Map(arr.map(item => [item[key], item])).values()];

// 3. Group by
const groupBy = (arr, key) =>
  arr.reduce((result, item) => {
    (result[item[key]] = result[item[key]] || []).push(item);
    return result;
  }, {});

// 4. Deep clone
const deepClone = obj => JSON.parse(JSON.stringify(obj));

// 5. Debounce
const debounce = (fn, delay) => {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
};

// 6. Throttle
const throttle = (fn, limit) => {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last >= limit) { last = now; fn(...args); }
  };
};

// 7. Capitalize
const capitalize = str => str.charAt(0).toUpperCase() + str.slice(1);

// 8. Format currency (BDT)
const formatBDT = amount => `৳${Number(amount).toLocaleString('en-BD')}`;

// 9. Truncate text
const truncate = (str, n) => str.length > n ? str.slice(0, n) + '...' : str;

// 10. Check empty object
const isEmpty = obj => Object.keys(obj).length === 0;
```

---

*End of Code Implementations — 14 Features, all technologies covered*
*For each implementation: explain your approach before writing, then write line by line with explanation*
