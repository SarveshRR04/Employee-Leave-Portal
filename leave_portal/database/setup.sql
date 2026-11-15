

CREATE DATABASE IF NOT EXISTS leave_portal_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'leave_user'@'localhost' IDENTIFIED BY 'leave_pass123';
GRANT ALL PRIVILEGES ON leave_portal_db.* TO 'leave_user'@'localhost';

GRANT ALL PRIVILEGES ON test_leave_portal_db.* TO 'leave_user'@'localhost';
FLUSH PRIVILEGES;
