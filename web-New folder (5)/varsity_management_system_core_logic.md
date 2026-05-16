# Core Logic & Implementation Details: Varsity Management System

The Varsity Management System (VMS) relies on a robust implementation of core web development concepts using core PHP. This document outlines how standard architectural patterns (like MVC components, middleware, and routing) are effectively mirrored in this project.

## 1. Authentication & Session Management
*   **Implementation**: Authentication is handled via a centralized `index.php` login portal. When a user submits their ID and password, the system queries the database using prepared statements.
*   **Password Hashing**: The system uses PHP's native `password_hash()` (during registration) and `password_verify()` (during login) to ensure passwords are cryptographically secure.
*   **Session Initialization**: Upon successful verification, `session_start()` initializes a secure session. User identifiers (`user_id`, `role`, `name`) are stored in the `$_SESSION` superglobal.
*   **Audit Logging**: Upon login, the system captures the user's IP address and User-Agent, storing it in the `session_logs` table for security auditing.

## 2. Middleware Equivalent (Access Control)
Since the project uses Core PHP without a framework like Laravel, "middleware" is implemented as procedural guard blocks at the top of every protected file.
*   **Logic**:
    ```php
    session_start();
    if(!isset($_SESSION['user_id'])) {
        header("Location: ../index.php");
        exit();
    }
    if($_SESSION['role'] !== 'admin') {
        echo "Access Denied.";
        exit();
    }
    ```
*   **Why**: This ensures that even if a user tries to access a URL directly (e.g., `superadmin/create_admin.php`), the script halts execution immediately if the user lacks the correct session or role privileges, preventing unauthorized data access.

## 3. Routing Mechanism (Page Controller Pattern)
*   **Implementation**: Instead of a single `web.php` route file, the system uses the **Page Controller Pattern**. Each `.php` file corresponds to a specific route and handles both the HTTP request (GET/POST) and the response rendering.
*   **Role-Based Redirection**: The root `dashboard.php` acts as a traffic director. It checks the `$_SESSION['role']` and uses `header("Location: ...")` to route Super Admins, Admins, Teachers, and Students to their respective directory domains.

## 4. Models & Database Interaction
*   **Database Schema**: The system relies on a highly normalized relational database schema (3NF) to maintain data integrity. Foreign keys (`ON DELETE CASCADE`, `ON DELETE SET NULL`) enforce relationships between users, departments, courses, enrollments, and marks.
*   **Database Connection**: `includes/db.php` establishes a singleton-like `mysqli` connection object (`$conn`) included across the app.
*   **Query Execution**: Instead of an ORM (like Eloquent), the system uses **Prepared Statements** universally.
    *   **Why**: By using `$stmt->prepare()` and `$stmt->bind_param()`, the application separates SQL code from user-supplied data, neutralizing SQL injection vulnerabilities.

## 5. Controllers (Business Logic)
In this architecture, the business logic (Controller) and the view (HTML) are co-located in the same file, but logically separated.
*   **Logic Flow**: The top half of a file handles POST requests, validates input, performs database operations, and sets success/error messages. The bottom half includes the header, renders the HTML form or table, and outputs the messages.
*   **Complex Logic (Enrollment & Grading)**:
    *   **Grading**: The `course_marks` table uses MySQL virtual generated columns (`total_mark AS (attendance + assignment + ct + midterm + final_exam) STORED`). This pushes calculation logic to the database layer, ensuring consistency and reducing PHP processing overhead.
    *   **Enrollment**: The `enrollments` table has a `UNIQUE KEY` constraint on `(student_id, section_id, course_id)` to prevent duplicate enrollments at the database level, serving as a failsafe against race conditions.

## 6. Utilities & Reusable Components (Hooks/Includes)
*   **Implementation**: The `includes/` directory contains `header.php`, `navbar.php`, `sidebar.php`, and `footer.php`.
*   **Why**: This modularizes the UI. Any change to the navigation menu or CSS/JS dependencies (like Bootstrap or jQuery) is done in one place, instantly reflecting across all panels. This mimics the component-based approach seen in modern front-end frameworks.
