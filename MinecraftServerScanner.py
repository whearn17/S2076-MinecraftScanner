# Author: Will
# Program: MinecraftServerScanner

import os
import psql
import time
import math
import socket
import random
import getpass
import argparse
import ipaddress
import traceback
import threading
import dns.resolver
from mcstatus import JavaServer

VERSION = "3.1.1"

server_list = []
ip_list = []
threads = []
num_ips = 0
num_threads = 500
timeout = 10
stop = False
pg = False

ip_read_file = ""
ip_exclude_file = ""
server_file = ""

servers_found = 0
servers_scanned = 0

db_host = ""
db_name = ""
db_user = ""
db_pass = ""
db_table = ""
sslmode = ""

file_lock = threading.Lock()
ip_list_lock = threading.Lock()
server_list_lock = threading.Lock()
servers_found_lock = threading.Lock()
servers_scanned_lock = threading.Lock()


# Class to hold Minecraft Servers as objects
class MinecraftServer:
    def __init__(self, ip, version, prot, description, p_online, p_max):
        self.ip = ip
        self.version = version
        self.prot = prot
        self.description = description
        self.p_online = p_online
        self.p_max = p_max

    def to_string(self):
        return (f"Minecraft: {self.version} Protocol ({self.prot}) \nDescription: "
                f"{self.description} \n{self.p_online}/{self.p_max}\n{self.ip}\n\n")


# Create threads and start working
def init_threads():
    for i in range(num_threads):
        thread = threading.Thread(target=cycle)
        threads.append(thread)
        thread.start()

    thread = threading.Thread(target=display_statistics)
    threads.append(thread)
    thread.start()


# Parse each command line argument
def parse_args():
    global ip_read_file
    global ip_exclude_file
    global server_file
    global num_threads
    global timeout
    global db_host
    global db_name
    global db_user
    global db_pass
    global db_table
    global sslmode
    global pg

    args = init_args()

    # Output scan to file argument
    if args.output_file:
        server_file = args.output_file

    # Number of threads argument
    if args.num_threads:
        num_threads = args.num_threads

    # IP range argument
    if args.ip_range:
        try:
            for ip in ipaddress.IPv4Network(args.ip_range):
                ip_list.append(str(ip))
        except ipaddress.AddressValueError:
            print("Invalid IP range")
        except ValueError:
            print("Don't alter host bits")

    # Host timeout argument
    if args.host_timeout:
        timeout = args.host_timeout

    # Postgres argument
    if args.postgres:
        pg = True

        db_host, db_name, db_user, db_pass, db_table, sslmode = psql.read_config(
            "psql.json")

        psql.reset_table(db_host, db_name, db_user,
                         db_pass, db_table, sslmode)

    # Input IP file argument
    if args.input_file:
        ip_read_file = args.input_file
        cls()
        print("Reading IPs from input file...")
        read_ips()

    # Ignore IPs from file argument
    if args.exclude_file:
        ip_exclude_file = args.exclude_file
        cls()
        print("Reading IPs from exclude file...")
        clean_ips()


# Create the command line argument
def init_args():
    parser = argparse.ArgumentParser(prog="MinecraftServerScanner.py")

    # Input IP file argument
    parser.add_argument("-i", "--input-file", type=str,
                        help="Scan a list of IPs from a file")

    # Output scan to file argument
    parser.add_argument("-o", "--output-file", type=str,
                        help="Output scan to a file")

    # Ignore IPs from file argument
    parser.add_argument("-e", "--exclude-file", type=str,
                        help="Exclude a list of IPs from a file")

    # Number of threads argument
    parser.add_argument("-n", "--num-threads", type=int,
                        help="Number of threads for scanning")

    # IP range argument
    parser.add_argument("ip_range", type=str, nargs="?",
                        help="Range of IPs to scan")

    # Host timeout argument
    parser.add_argument("-t", "--host-timeout", type=int,
                        help="Number of seconds to wait for host to respond")

    # Postgres argument
    parser.add_argument("-pg", "--postgres", action="store_true",
                        help="Enable export of server list to PostgreSQL")

    return parser.parse_args()


# Send servers found to database
def send_to_db(server, ip):
    psql.send(server, db_host, db_name, db_user,
              db_pass, db_table, sslmode, ip)


# Create server object and add to server list
def add_server(info, ip):
    server = MinecraftServer(ip, info.version.name, info.version.protocol,
                             info.description, info.players.online, info.players.max)
    with server_list_lock:
        server_list.append(server)


# Write scan information when done
def write_output():
    if server_file and servers_found:
        with open(server_file, "a", encoding="utf-8") as file:
            for server in server_list:
                file.write(server.to_string())
        file.close()

    for item in server_list:
        print(item.to_string())

    print(f"--------------------------------------------\n"
          f"MinecraftServerScanner: Done\nElapsed Time: {total_time} seconds\n"
          f"Servers Found: {servers_found}\nServers Scanned: {servers_scanned}\n")


# Clear screen
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


# Quick log to a file
def log(filename, message):
    if not filename:
        return
    with file_lock:
        f = open(filename, "a", encoding="utf-8")
        f.write(message)
        f.close()


# Display scan info as the program runs
def display_statistics():
    while servers_scanned < num_ips and not stop:
        cls()
        percent_done = math.floor((servers_scanned / num_ips) * 100)
        print(f"{percent_done}% Done")
        print(f"Servers Found: {servers_found}")
        print(f"Servers Scanned: {servers_scanned}")
        time.sleep(5)


# Read in a list of IPs from a text file into a list
def read_ips():
    with open(ip_read_file, "r") as f:
        for line in f:
            ip_list.append(line.rstrip())
    f.close()
    random.shuffle(ip_list)


# Read a list of IPs already found and remove from list
def clean_ips():
    try:
        f = open(ip_exclude_file, "r")
        print("Reading IPs to be ignored (this may take a while)")
        skip = 0
        for line in f:
            if line.rstrip() in ip_list:
                ip_list.remove(line.rstrip())
                skip += 1
        print(f"[INFO] {skip} IPs being ignored")
    except FileNotFoundError:
        print("[INFO] No IPs being ignored")
        time.sleep(.5)


# Use the mcstatus lookup method to search for a server
def query(host):
    scan = JavaServer.lookup(host, timeout)
    return scan.status()


# Cycle through the portion of IP list that belongs to current thread
def cycle():
    # Keep track of servers found
    global servers_found
    global servers_scanned

    while len(ip_list) > 0 and not stop:
        try:

            # Pop an item off the ip list to scan
            with ip_list_lock:
                ip = ip_list.pop()

            # Query a server for info
            server = query(ip)

            # Add server object
            add_server(server, ip)

            # Check if postgres is enabled and send to databse if true
            if pg:
                send_to_db(server, ip)

            # If we made it here mark server as found
            with servers_found_lock:
                servers_found += 1

        except socket.timeout:
            pass
        except ConnectionResetError:
            pass
        except ConnectionRefusedError:
            pass
        except OSError:
            pass
        except dns.resolver.LifetimeTimeout:
            pass
        except IndexError:
            pass
        except Exception as e:
            log("log.txt", f"[ERROR] An unkown error occured... Scanning will continue\n\n"
                f"{traceback.format_exc()}\n\n")
            print(e)

        # Increment count for scanned IPs
        with servers_scanned_lock:
            servers_scanned += 1


if __name__ == '__main__':

    # Clear screen
    cls()

    # Parse command lind arguments
    parse_args()

    # Get total number of IPs
    num_ips = len(ip_list)

    # Make sure there aren't more threads than IPs to scan
    if num_ips < num_threads:
        num_threads = num_ips

    # Begin scan timing
    time_start = time.time()

    # Start threads
    init_threads()

    try:
        # Wait for threads to finish
        for worker in threads:
            while worker.is_alive():
                worker.join(3)
    except KeyboardInterrupt:
        stop = True
        print("Stopping scan (This may take a minute)")
        for worker in threads:
            worker.join()

    # End scan timing
    time_end = time.time()

    # Calculate scan timing
    total_time = math.floor(time_end - time_start)

    cls()

    write_output()
