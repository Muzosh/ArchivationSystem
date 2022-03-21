-- Create Database and user
CREATE DATABASE IF NOT EXISTS archivingsystem;
CREATE USER IF NOT EXISTS 'ncadmin'@'localhost' IDENTIFIED BY 'ncadmin';
GRANT ALL PRIVILEGES ON archivingsystem.* TO 'ncadmin'@'localhost';
FLUSH PRIVILEGES;