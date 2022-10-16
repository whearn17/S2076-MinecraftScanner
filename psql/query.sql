-- Creat the minecraft table
CREATE TABLE minecraft (
    ip_address inet PRIMARY KEY,
    version VARCHAR (1000),
    protocol VARCHAR (500),
    description VARCHAR (5000),
    p_online int,
    p_max int
);

-- Delete the minecraft table
DROP TABLE minecraft;