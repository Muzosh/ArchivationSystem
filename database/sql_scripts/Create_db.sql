-- Create Database and user
CREATE DATABASE ArchivationSystemDB;
CREATE USER 'test_user'@'localhost' IDENTIFIED BY 'Password1';
GRANT ALL PRIVILEGES ON ArchivationSystemDB.* TO 'test_user'@'localhost';
FLUSH PRIVILEGES;


