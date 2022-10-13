-- Creat the minecraft table
CREATE TABLE IF NOT EXISTS minecraft (
    ip_address inet PRIMARY KEY,
    version VARCHAR (500),
    protocol VARCHAR (500),
    description VARCHAR (2000),
    p_online int,
    p_max int
);

-- Delete the minecraft table
DROP TABLE minecraft;