import psycopg2
from minecraft_server import MinecraftServer


class DatabaseConnection:
    def __init__(self, hostname, dbname, username, password, table, sslmode):
        self.conn = psycopg2.connect(
            host=hostname,
            dbname=dbname,
            user=username,
            password=password,
            sslmode=sslmode
        )
        self.cur = self.conn.cursor()
        self.table = table

    def add_server(self, server: MinecraftServer) -> None:
        query = f"""
                INSERT INTO {self.table} (ip_address, version, protocol, description, 
                players_online, max_players, created_at)
                VALUES (CAST(%s AS INET), %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (ip_address) DO UPDATE
                SET version = EXCLUDED.version,
                    protocol = EXCLUDED.protocol,
                    description = EXCLUDED.description,
                    players_online = EXCLUDED.players_online,
                    max_players = EXCLUDED.max_players,
                    created_at = NOW();
            """
        values = (server.ip_address, server.version, server.protocol, server.description, server.players_online,
                  server.max_players)

        self.cur.execute(query, values)
        self.conn.commit()

    def create_table(self) -> None:
        """
        This is really just here to show the structure of the table.
        :return: None
        """
        query = f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    ip_address INET PRIMARY KEY,
                    version VARCHAR(1000) NOT NULL,
                    protocol VARCHAR(1000) NOT NULL,
                    description TEXT NOT NULL,
                    players_online INTEGER NOT NULL,
                    max_players INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW() NOT NULL
                );
            """
        self.cur.execute(query)
        self.conn.commit()
