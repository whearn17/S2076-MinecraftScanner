import psycopg2


# Send the servers to the database
def send(serverlist, host, name, user, password):
    try:
        conn = psycopg2.connect(host=host, dbname=name,
                                user=user, password=password,
                                sslmode="require")
        cur = conn.cursor()
        for server in serverlist:
            cur.execute(f"INSERT INTO minecraft"
                        f"(ip_address, version, protocol, "
                        f"description, p_online, p_max) "
                        f"VALUES(%s, %s, %s, %s, %s, %s);",
                        (server.ip, server.version, server.prot,
                         server.description, server.p_online,
                         server.p_max))
    except Exception as e:
        f = open("log.txt", "a")
        f.write(f"{e}\n\n")
        f.close()
    cur.close()
    conn.commit()
    conn.close()


# Clear the old minecraft table and reset
def reset_table(host, name, user, password):
    try:
        conn = psycopg2.connect(host=host, dbname=name,
                                user=user, password=password,
                                sslmode="require")
        cur = conn.cursor()
        cur.execute("DROP TABLE minecraft;")
        cur.execute("CREATE TABLE IF NOT EXISTS minecraft"
                    "(ip_address inet PRIMARY KEY,"
                    "version VARCHAR (800),"
                    "protocol VARCHAR (500),"
                    "description VARCHAR (5000),"
                    "p_online int,"
                    "p_max int);")
    except Exception as e:
        f = open("log.txt", "a")
        f.write(f"{e}\n\n")
        f.close()
    cur.close()
    conn.commit()
    conn.close()
