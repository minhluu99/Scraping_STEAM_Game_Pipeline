Create database if not exists Airflowdb;
Use Airflowdb;

Create table if not exists Steam_games
(
    id int primary key,
    Name        nvarchar(100) not null,
    platform    varchar(100),
    vr_supported TINYINT,
    release_date	date,
    url         nvarchar(255),
    price	    decimal(6,2),
    disprice    decimal(6,2),
    review      nvarchar(512)
    
)
