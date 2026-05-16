# Learn with Anik - Online Learning Platform
**Project Name:** Online Learning (Learn with Anik)
**Role:** Full Stack Developer
**Stack:** PHP (PDO), HTML5, CSS3, Vanilla JavaScript, MySQL, Cloudinary API, PHPMailer

## Project Overview
"Learn with Anik" is a comprehensive, custom-built e-learning platform designed to bridge the gap between educators and learners. Built from the ground up without heavy frameworks, it offers a fast, robust, and highly scalable environment. The platform features a dynamic three-panel architecture (Learner, Tutor, and Superadmin), providing tailored interfaces and permissions for distinct user groups. 

## Core Architecture & Tech Stack
- **Backend:** Vanilla PHP utilizing Procedural & OOP paradigms.
- **Database:** MySQL integrated securely via PHP Data Objects (PDO).
- **Frontend:** Vanilla JS, CSS3 variables for dynamic theming (Dark/Light mode), and FontAwesome.
- **Media Management:** Cloudinary API for offloading and streaming heavy video and image assets, drastically reducing server bandwidth costs.
- **Transactional Emails:** PHPMailer for robust, authenticated SMTP email delivery (password resets, notifications).
- **Environment Management:** `vlucas/phpdotenv` to securely handle API keys and SMTP credentials.

## Panel Breakdown & Features

### 1. User Panel (Learners)
- **Authentication:** Secure registration, login, and robust password recovery via time-sensitive secure tokens.
- **Course Engagement:** 
  - Browse dynamic courses (Playlists) and individual video contents.
  - Granular search mechanism filtering by keywords across content titles.
  - Bookmark favorite courses for quick access.
- **Interactivity:** 
  - Like videos and post comments. 
  - View counts are strictly tracked with rate-limiting to prevent metric inflation.
- **Customization:** Manage personal profile details, avatars (hosted on Cloudinary), and dark/light mode UI preferences.

### 2. Tutor Panel (Instructors)
- **Content Management Pipeline:** 
  - Create, update, and securely delete Playlists and individual Video Content.
  - Media files are automatically uploaded to specific Cloudinary directories during creation and physically deleted from cloud storage when content is removed to save storage space.
- **Audience Interaction:** Review user comments on their videos with the ability to moderate (delete) inappropriate feedback.
- **Analytics Dashboard:** Real-time metrics showing total content published, total playlists, aggregated views, likes, and comments across all their materials.

### 3. Superadmin Panel (Platform Managers)
- **Platform Moderation:**
  - Complete oversight of the entire ecosystem.
  - Ability to forcefully change the status (Active/Deactive) of any User, Tutor, Playlist, or Content.
  - Changing a user's or tutor's status instantly revokes their access capabilities on their next request.
- **Automated Notifications:** When a Superadmin changes the status of a tutor or user, an automated email is triggered via PHPMailer to notify the affected individual.
- **Communication Hub:** Read, reply, and manage direct messages submitted through the public Contact form. Replies are sent directly to the user's email address via SMTP.
- **Data Pruning:** Capabilities to permanently delete accounts. Deleting a tutor cascades down to safely remove all their Cloudinary assets and database records (playlists, videos, likes, comments).

## Key Technical Highlights for Portfolio
- **Stateless Cloud Media:** Decoupled media storage by utilizing Cloudinary API, storing only `public_id`s in MySQL. This makes the database highly portable.
- **Cascading Deletions:** Engineered rigorous server-side cleanup scripts. Deleting a parent entity (like a Playlist) correctly maps and deletes all child content, their associated Cloudinary assets, and user interactions (likes/comments) to prevent database or cloud-storage orphans.
- **Smart View Tracking:** Implemented a temporal SQL logic (`DATE_SUB(NOW(), INTERVAL 1 HOUR)`) to ensure video views are only incremented once per hour per session/IP, preventing artificial inflation of engagement metrics.
- **Security-First Approach:** Implemented custom Unique ID generators to prevent Insecure Direct Object Reference (IDOR) vulnerabilities, utilized `htmlspecialchars` for XSS prevention, and PDO bindings for SQL Injection prevention.
