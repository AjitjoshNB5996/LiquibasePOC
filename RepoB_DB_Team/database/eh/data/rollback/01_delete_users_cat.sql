-- Rollback for 01_insert_into_users_cat.sql
DELETE FROM users
WHERE email = 'cat@example.com' AND name = 'Cat';