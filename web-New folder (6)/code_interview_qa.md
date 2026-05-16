# Comprehensive Code Interview & Review Guide

As an AI-First Developer at XPONENT, you are expected to read, understand, and correct code at a senior level. This document contains advanced implementation snippets and complex code review scenarios across your tech stack.

---

## 1. Advanced React: Custom Hooks & State Management

**Task:** Write a robust, production-ready custom hook for fetching data that handles race conditions, abort controllers, and caching logic.

**Implementation:**
```javascript
import { useState, useEffect, useRef } from 'react';

const useFetchAdvanced = (url) => {
  // Use useRef to track cache across renders without triggering re-renders
  const cache = useRef({});
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    // AbortController allows us to cancel pending fetch requests if the component unmounts
    const abortController = new AbortController();
    
    const fetchData = async () => {
      // If data is in cache, return it immediately
      if (cache.current[url]) {
        setState({ data: cache.current[url], loading: false, error: null });
        return;
      }

      setState((prev) => ({ ...prev, loading: true }));

      try {
        const response = await fetch(url, { signal: abortController.signal });
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        
        const result = await response.json();
        
        // Save to cache
        cache.current[url] = result;
        
        // Only update state if the fetch wasn't aborted
        if (!abortController.signal.aborted) {
          setState({ data: result, loading: false, error: null });
        }
      } catch (error) {
        if (error.name !== 'AbortError') {
          setState({ data: null, loading: false, error: error.message });
        }
      }
    };

    fetchData();

    // Cleanup: cancel fetch on unmount or url change
    return () => abortController.abort();
  }, [url]);

  return state;
};

export default useFetchAdvanced;
```
**Why this matters:** AI often generates naive `fetch` calls. Understanding `AbortController` and simple caching mechanisms is crucial for performance and preventing memory leaks in large React applications.

---

## 2. Next.js App Router: Server Components vs Client Components

**Task:** Create a Next.js page that fetches SEO-critical data on the server, but includes an interactive client component.

**Implementation:**
```javascript
// app/products/[id]/page.js (Server Component - Default)
import dbConnect from '@/lib/dbConnect';
import Product from '@/models/Product';
import AddToCartButton from '@/components/AddToCartButton'; // Client Component

// This runs ONLY on the server. Great for SEO and DB access.
export default async function ProductPage({ params }) {
  await dbConnect();
  
  // Mongoose lean() for performance since we don't need Mongoose methods here
  const product = await Product.findById(params.id).lean();

  if (!product) return <div>Product Not Found</div>;

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <p>${product.price}</p>
      
      {/* We pass serializable data to the Client Component */}
      <AddToCartButton productId={product._id.toString()} price={product.price} />
    </div>
  );
}

// components/AddToCartButton.js (Client Component)
'use client'; // This directive makes it a client component

import { useState } from 'react';

export default function AddToCartButton({ productId, price }) {
  const [isAdding, setIsAdding] = useState(false);

  const handleAdd = async () => {
    setIsAdding(true);
    // Client-side API call logic here...
    await fetch('/api/cart', { method: 'POST', body: JSON.stringify({ productId }) });
    setIsAdding(false);
  };

  return (
    <button onClick={handleAdd} disabled={isAdding}>
      {isAdding ? 'Adding...' : 'Add to Cart'}
    </button>
  );
}
```

---

## 3. Advanced Express.js: Error Handling Middleware Architecture

**Task:** Design a robust, centralized error handling architecture for an Express API.

**Implementation:**
```javascript
// 1. Create a Custom Error Class (utils/AppError.js)
class AppError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
    this.isOperational = true; // Distinguish between our errors vs programming bugs
    Error.captureStackTrace(this, this.constructor);
  }
}
module.exports = AppError;

// 2. Async Wrapper to eliminate try/catch blocks in controllers (utils/catchAsync.js)
const catchAsync = (fn) => {
  return (req, res, next) => {
    fn(req, res, next).catch(next);
  };
};

// 3. Controller using the wrapper
exports.getUser = catchAsync(async (req, res, next) => {
  const user = await User.findById(req.params.id);
  if (!user) {
    return next(new AppError('No user found with that ID', 404)); // Triggers error middleware
  }
  res.status(200).json({ success: true, data: user });
});

// 4. Global Error Handling Middleware (middlewares/errorHandler.js)
// Placed at the very bottom of server.js: app.use(globalErrorHandler)
module.exports = (err, req, res, next) => {
  err.statusCode = err.statusCode || 500;
  err.status = err.status || 'error';

  // In production, send clean errors. In dev, send stack trace.
  if (process.env.NODE_ENV === 'development') {
    res.status(err.statusCode).json({
      status: err.status,
      error: err,
      message: err.message,
      stack: err.stack
    });
  } else {
    // Production Mode
    if (err.isOperational) {
      res.status(err.statusCode).json({ status: err.status, message: err.message });
    } else {
      // Programming or unknown error: don't leak details
      console.error('ERROR 💥', err);
      res.status(500).json({ status: 'error', message: 'Something went very wrong!' });
    }
  }
};
```

---

## 4. Advanced MongoDB / Mongoose: Aggregation Pipelines

**Task:** Write a Mongoose query to get the total revenue generated by each user, only including completed orders.

**Implementation:**
```javascript
const userRevenues = await Order.aggregate([
  // Stage 1: Filter only completed orders
  { $match: { status: 'completed' } },
  
  // Stage 2: Group by user_id and sum the totalAmount
  {
    $group: {
      _id: '$user_id', // Group by user
      totalRevenue: { $sum: '$totalAmount' },
      orderCount: { $sum: 1 } // Count how many orders they made
    }
  },
  
  // Stage 3: Lookup (Join) to get user details from the Users collection
  {
    $lookup: {
      from: 'users', // Collection name in MongoDB
      localField: '_id',
      foreignField: '_id',
      as: 'userDetails'
    }
  },
  
  // Stage 4: Deconstruct the userDetails array
  { $unwind: '$userDetails' },
  
  // Stage 5: Project to shape the final output
  {
    $project: {
      _id: 0, // hide the _id
      userId: '$_id',
      name: '$userDetails.name',
      email: '$userDetails.email',
      totalRevenue: 1,
      orderCount: 1
    }
  },
  
  // Stage 6: Sort by highest revenue
  { $sort: { totalRevenue: -1 } }
]);
```

---

## 5. Docker: Production-Ready Multi-Stage Build

**Task:** Write a Dockerfile for a React application that builds the static files and serves them with Nginx.

**Implementation:**
```dockerfile
# STAGE 1: Build Phase
FROM node:18-alpine as builder
WORKDIR /app
COPY package.json package-lock.json ./
# ci installs exactly what is in lockfile, faster and safer for prod
RUN npm ci 
COPY . .
RUN npm run build

# STAGE 2: Production Server Phase
FROM nginx:alpine
# Copy built static files from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html
# Copy custom nginx config if necessary
# COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
# Nginx runs automatically, no CMD needed
```

---

## 6. AI Code Review Scenarios (Critical for XPONENT)

### Scenario A: The Race Condition
**AI Output:**
```javascript
// AI Generated: Decrement inventory when item is purchased
app.post('/buy', async (req, res) => {
  const product = await Product.findById(req.body.productId);
  
  if (product.stock >= req.body.quantity) {
    product.stock -= req.body.quantity;
    await product.save();
    res.send('Success');
  } else {
    res.status(400).send('Out of stock');
  }
});
```
**Your Review:** This code contains a classic Race Condition. If two users buy the last item at the exact same millisecond, they both fetch the `product`, both see `stock == 1`, both pass the `if` check, and both decrement it. Stock becomes `-1`.
**The Fix:** Use atomic operators in MongoDB.
```javascript
const result = await Product.updateOne(
  { _id: req.body.productId, stock: { $gte: req.body.quantity } },
  { $inc: { stock: -req.body.quantity } }
);
if (result.modifiedCount === 0) return res.status(400).send('Out of stock');
```

### Scenario B: Security Flaw (Mass Assignment)
**AI Output:**
```javascript
// AI Generated: Update user profile
app.put('/users/:id', authMiddleware, async (req, res) => {
  const user = await User.findByIdAndUpdate(req.params.id, req.body, { new: true });
  res.json(user);
});
```
**Your Review:** This is highly insecure. The AI passes the entire `req.body` directly to the database update function. A malicious user could send `{"role": "admin"}` in the request body, elevating their privileges, or `{"password": "new"}` without hashing it.
**The Fix:** Explicitly destructure only the allowed fields.
```javascript
const { name, email, bio } = req.body; // Explicitly extract allowed fields
const user = await User.findByIdAndUpdate(
  req.params.id, 
  { name, email, bio }, 
  { new: true, runValidators: true } // Always run validators on update
);
```
