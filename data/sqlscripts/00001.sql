-- Create Database and user
CREATE DATABASE archivationsystem;
CREATE USER 'ncadmin'@'localhost' IDENTIFIED BY 'ncadmin';
GRANT ALL PRIVILEGES ON archivationsystem.* TO 'ncadmin'@'localhost';
FLUSH PRIVILEGES;