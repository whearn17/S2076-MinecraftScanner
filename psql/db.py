import psycopg2
import psycopg2.errors
import traceback


# Send the servers to the database
def send(server, host, name, user, password, table, ssl, ip):
    try:
        conn = psycopg2.connect(host=host, dbname=name,
                                user=user, password=password,
                                sslmode=ssl)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO {table}"
                    f"(ip_address, version, protocol, "
                    f"description, p_online, p_max) "
                    f"VALUES(%s, %s, %s, %s, %s, %s);",
                    (ip, server.version.name, server.version.protocol,
                     server.description, server.players.online,
                     server.players.max))
        cur.close()
        conn.commit()
        conn.close()
    except Exception as e:
        f = open("log.txt", "a")
        f.write(f"{e}\n\n{traceback.format_exc()}\n\n")
        f.close()


# Clear the old minecraft table and reset
def reset_table(host, name, user, password, table, ssl):
    try:
        conn = psycopg2.connect(host=host, dbname=name,
                                user=user, password=password,
                                sslmode=ssl)
        cur = conn.cursor()
        cur.execute(f"DROP TABLE {table};")
        cur.execute(f"CREATE TABLE {table}"
                    "(ip_address inet PRIMARY KEY,"
                    "version VARCHAR (800),"
                    "protocol VARCHAR (500),"
                    "description VARCHAR (5000),"
                    "p_online int,"
                    "p_max int);")
        cur.close()
        conn.commit()
        conn.close()
    except psycopg2.errors.UndefinedTable:
        conn = psycopg2.connect(host=host, dbname=name,
                                user=user, password=password,
                                sslmode=ssl)
        cur = conn.cursor()
        cur.execute(f"CREATE TABLE {table}"
                    "(ip_address inet PRIMARY KEY,"
                    "version VARCHAR (800),"
                    "protocol VARCHAR (500),"
                    "description VARCHAR (5000),"
                    "p_online int,"
                    "p_max int);")
        cur.close()
        conn.commit()
        conn.close()
    except Exception as e:
        f = open("log.txt", "a")
        f.write(f"{e}\n\n{traceback.format_exc()}\n\n")
        f.close()
