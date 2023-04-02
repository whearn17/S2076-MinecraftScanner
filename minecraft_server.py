class MinecraftServer:
    def __init__(self, ip_address: str, server_information):
        self.ip_address = ip_address
        self.version = server_information.version.name
        self.protocol = server_information.version.protocol
        self.description = server_information.description
        self.players_online = server_information.players.online
        self.max_players = server_information.players.max

    def __repr__(self):
        return f"Server IP: {self.ip_address}\n" \
               f"Server Version: {self.version}\n" \
               f"Server protocol: {self.protocol}\n" \
               f"Server description: {self.description}\n" \
               f"Server players online: {self.players_online}\n" \
               f"Server max players: {self.max_players}\n"
