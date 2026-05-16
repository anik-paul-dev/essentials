# Varsity Management System (VMS)

## Project Overview
The Varsity Management System (VMS) is a comprehensive university ERP web application designed to streamline academic, administrative, and student-related processes. It provides distinct role-based portals for Super Admins, Admins, Teachers, and Students, creating an integrated ecosystem for managing the entire university workflow—from enrollment and course management to grading and project submissions.

## Technology Stack
*   **Frontend**: HTML5, CSS3, JavaScript, Bootstrap (for responsive design and UI components), jQuery.
*   **Backend**: PHP (Core PHP/Procedural with PDO/MySQLi for database interactions).
*   **Database**: MySQL (Relational Database Management System).
*   **Architecture**: Monolithic Architecture utilizing the Page Controller pattern, Role-Based Access Control (RBAC), and session-based authentication.
*   **Infrastructure/Tools**: Apache/Nginx web server, Docker (containerization), Git (version control).

## System Architecture
The system is built on a structured Monolithic Architecture with a strong focus on separation of concerns within the physical directory structure. 
*   **Role-Based Directory Structure**: Dedicated directories (`superadmin/`, `admin/`, `teacher/`, `student/`) act as modular namespaces. Each directory contains the specific logic and views for that role.
*   **Centralized Assets & Includes**: Reusable components such as headers, footers, navigation bars, and database connection logic are centralized in the `includes/` and `assets/` directories, promoting DRY (Don't Repeat Yourself) principles.
*   **Routing mechanism**: The application uses a physical file-based routing mechanism. The central `dashboard.php` acts as a role-router, redirecting authenticated users to their respective panel dashboards based on their session role.
*   **Security Layers**: The system employs multi-layered security. Every protected endpoint verifies the user session and role. Prepared statements are used universally to prevent SQL Injection, and `htmlspecialchars` is used on outputs to prevent XSS.

## Core Features by Panel

### 1. Super Admin Panel
*   **Core System Setup**: Manage Departments, Semesters, Batches, Sessions, and Academic Years.
*   **User Management**: Create, approve, edit, and delete Admins, Teachers, and Students. Handles user account approval workflows.
*   **Role Assignments**: Appoint Advisors and assign Teachers to specific sections and courses.
*   **System Auditing**: View and monitor session logs (login times, IP addresses, User Agents) for security and auditing purposes.

### 2. Admin Panel
*   **Academic Management**: Create and manage courses, sections, and class routines.
*   **Enrollment & Records**: Manage student enrollments, set student limits per section, and print student academic results.
*   **Operational Control**: Manage day-to-day university operations, view assigned teachers, and monitor appointed advisors.

### 3. Teacher Panel
*   **Course Management**: View assigned courses, sections, and enrolled students.
*   **Grading System**: Dedicated interface to input and manage marks (Attendance, Assignments, Class Tests, Midterms, and Finals) with automated total calculations.
*   **Project Management**: Receive student project ideas, set submission deadlines, review submissions, and provide feedback or approval.
*   **Advising**: Access advisor assignments and monitor advisee progress.
*   **Scheduling**: View customized class routines based on assigned sections.

### 4. Student Panel
*   **Course Enrollment**: Browse available courses and submit enrollment requests for current semesters.
*   **Academic Tracking**: View enrollment status, class routines, and final course marks.
*   **Project Submission**: Submit project ideas (individual or group), track approval status, and view teacher feedback.
*   **Profile Management**: Update personal profile details and handle password changes.
