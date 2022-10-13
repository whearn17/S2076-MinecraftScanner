import psycopg2


def send(serverlist, host, name, user, password):
    conn = psycopg2.connect(host=host, dbname=name,
                            user=user, password=password,
                            sslmode="require")
    cur = conn.cursor()
    for server in serverlist:
        try:
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


def check_pass(host, name, user, password):
    conn = psycopg2.connect(host=host, dbname=name,
                            user=user, password=password,
                            sslmode="require")
    conn.close()
