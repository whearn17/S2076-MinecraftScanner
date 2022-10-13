-- Creat the minecraft table
CREATE TABLE IF NOT EXISTS minecraft (
    ip_address inet PRIMARY KEY,
    version VARCHAR (100),
    protocol VARCHAR (100),
    description VARCHAR (1000),
    p_online smallint,
    p_max smallint
);

-- Delete the minecraft table
DROP TABLE minecraft;