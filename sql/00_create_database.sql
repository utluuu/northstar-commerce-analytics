/* Northstar Commerce | 00_create_database.sql
   Rebuilds the portfolio database. Run only in a development environment. */
USE master;
GO

IF DB_ID(N'NorthstarCommerce') IS NOT NULL
BEGIN
    ALTER DATABASE NorthstarCommerce SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE NorthstarCommerce;
END;
GO

CREATE DATABASE NorthstarCommerce;
GO

ALTER DATABASE NorthstarCommerce SET RECOVERY SIMPLE;
ALTER DATABASE NorthstarCommerce SET COMPATIBILITY_LEVEL = 150;
GO

USE NorthstarCommerce;
GO

CREATE SCHEMA ecommerce AUTHORIZATION dbo;
GO
CREATE SCHEMA analytics AUTHORIZATION dbo;
GO
