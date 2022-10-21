# Author: Will
# Program: MinecraftServerScanner

import os
import psql
import time
import math
import numpy
import ctypes
import socket
import random
import getpass
import psycopg2
import datetime
import argparse
import ipaddress
import traceback
import threading
import dns.resolver
import multiprocessing
from mcstatus import JavaServer

VERSION = "4.0.0"

cpu_cores = multiprocessing.cpu_count()

server_list = []
ip_list = []
ip_lists = []
threads = []
processes = []
num_ips = 0
num_threads = 400
timeout = 10
stop = False
pg = False

# File names
ip_read_file = ""
ip_exclude_file = ""
server_file = ""

servers_found = 0
servers_scanned = 0
local_servers_scanned = 0

# Database creds
db_host = ""
db_name = ""
db_user = ""
db_pass = ""
db_table = ""
sslmode = ""

# Threading locks
t_logfile_lock = threading.Lock()
t_ip_list_lock = threading.Lock()
t_server_list_lock = threading.Lock()
t_servers_found_lock = threading.Lock()
t_servers_scanned_lock = threading.Lock()

# Process locks
mp_lock = multiprocessing.Lock()
mp_done_lock = multiprocessing.Lock()
mp_logfile_lock = multiprocessing.Lock()

# Process shared variables
mp_servers_scanned = multiprocessing.Value(ctypes.c_int, 0)
mp_servers_found = multiprocessing.Value(ctypes.c_int, 0)
mp_done = multiprocessing.Value(ctypes.c_int, 0)


class MPShared:
    def __init__(self, ctype_servers_scanned, ctype_servers_found, ctype_done, ctype_done_lock,
     ctype_lock, server_file, threads, cores, pg, db_host, db_name, db_user, db_pass, db_table, sslmode):

        self.mp_scanned = ctype_servers_scanned
        self.mp_found = ctype_servers_found
        self.mp_done = ctype_done

        self.mp_done_lock = ctype_done_lock
        self.lock = ctype_lock

        self.server_file = server_file

        self.threads = threads
        self.cores = cores

        self.pg = pg
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_table = db_table
        self.sslmode = sslmode


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


def init_mp_globals(local_ip_list, mp_shared):
    global ip_list
    global num_ips
    global mp_servers_scanned
    global mp_servers_found
    global mp_done
    global mp_done_lock
    global mp_lock
    global server_file
    global num_threads
    global cpu_cores
    global pg
    global db_host
    global db_name
    global db_user
    global db_pass
    global sslmode

    ip_list = local_ip_list
    num_ips = len(ip_list)

    mp_servers_scanned = mp_shared.mp_scanned
    mp_servers_found = mp_shared.mp_found

    mp_done = mp_shared.mp_done

    mp_lock = mp_shared.mp_done_lock
    mp_lock = mp_shared.lock

    server_file = mp_shared.server_file

    num_threads = mp_shared.threads
    cpu_cores = mp_shared.cores

    pg = mp_shared.pg
    db_host = mp_shared.db_host
    db_name = mp_shared.db_name
    db_user = mp_shared.db_user
    db_pass = mp_shared.db_pass
    sslmode = mp_shared.sslmode


def mp_main(local_ip_list, mp_shared):
    global stop

    init_mp_globals(local_ip_list, mp_shared)

    init_threads()

    try:
        for thread in threads:
            while thread.is_alive():
                thread.join(3)
    except KeyboardInterrupt:
        stop = True
        for thread in threads:
            thread.join()

    with mp_done_lock:
        mp_done.value += 1

    while mp_done.value < cpu_cores:
        time.sleep(10)

    mp_write_output()


def init_processes():
    global ip_lists

    mp_shared = MPShared(mp_servers_scanned, mp_servers_found, mp_done, 
                        mp_done_lock, mp_lock, server_file, num_threads, cpu_cores,
                        pg, db_host, db_name, db_user, db_pass, db_table, sslmode)

    for i in range(cpu_cores):
        ip_list = ip_lists[i].tolist()
        p = multiprocessing.Process(target=mp_main, args=(ip_list, mp_shared))
        p.start()
        processes.append(p)


# Create threads and start working
def init_threads():
    for i in range(num_threads):
        thread = threading.Thread(target=cycle)
        threads.append(thread)
        thread.start()

    thread = threading.Thread(target=shared_manager)
    thread.start()
    threads.append(thread)


def init_display_manager():
    thread = threading.Thread(target=display_manager)
    threads.append(thread)
    thread.start()


def shared_manager():
    global mp_servers_scanned
    global mp_servers_found
    global servers_scanned
    global servers_found
    global local_servers_scanned

    while local_servers_scanned < num_ips and not stop:
        with mp_lock:
            with t_servers_scanned_lock:
                with t_servers_found_lock:
                    mp_servers_scanned.value += servers_scanned
                    mp_servers_found.value += servers_found
                    local_servers_scanned += servers_scanned
                    servers_scanned = servers_found = 0
        time.sleep(10)

    with mp_lock:
        with t_servers_scanned_lock:
            with t_servers_found_lock:
                mp_servers_scanned.value += servers_scanned
                mp_servers_found.value += servers_found
                servers_scanned = servers_found = 0


# Parse each command line argument
def parse_args():
    global cpu_cores
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

    if args.processes:
        cpu_cores = args.processes

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

        try:
            psql.reset_table(db_host, db_name, db_user,
                            db_pass, db_table, sslmode)
        except psycopg2.OperationalError as e:
            print(e)
            exit(0)

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
                    
    parser.add_argument("-p", "--processes", type=int, help="Number of processes")

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
    with t_server_list_lock:
        server_list.append(server)


# Write scan information when done
def mp_write_output():
    if server_file and mp_servers_found.value > 0:
        with open(server_file, "a", encoding="utf-8") as file:
            for server in server_list:
                file.write(server.to_string())
        file.close()

    for item in server_list:
        print(item.to_string())


# Clear screen
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


# Quick log to a file
def log(filename, message):
    if not filename:
        return
    with mp_logfile_lock:
        with t_logfile_lock:
            f = open(filename, "a", encoding="utf-8")
            f.write(message)
            f.close()


# Display scan info as the program runs
def display_manager():
    global mp_servers_scanned
    global mp_servers_found

    while mp_servers_scanned.value < num_ips and not stop:
        cls()
        percent_done = math.floor((mp_servers_scanned.value / num_ips) * 100)
        print(f"{percent_done}% Done")
        print(f"Servers Scanned: {mp_servers_scanned.value}")
        print(f"Servers Found: {mp_servers_found.value}")
        time.sleep(10)


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
    global t_ip_list_lock
    global t_servers_scanned_lock
    global t_servers_found_lock

    while len(ip_list) > 0 and not stop:
        try:
            # Pop an item off the ip list to scan
            with t_ip_list_lock:
                ip = ip_list.pop()

            # Query a server for info
            server = query(ip)

            # Add server object
            add_server(server, ip)

            # Check if postgres is enabled and send to databse if true
            if pg:
                send_to_db(server, ip)

            # If we made it here mark server as found
            with t_servers_found_lock:
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
            log("log.txt",
                f"---------------------------------------------------------------------\n\n"
                f"[ERROR] An unkown error occured... Scanning will continue\n\n"
                f"Worker currently working on -> {ip}\n\n"
                f"{traceback.format_exc()}\n\n{e}\n\n{datetime.datetime.now()}\n\n"
                f"---------------------------------------------------------------------\n\n")

        # Increment count for scanned IPs
        with t_servers_scanned_lock:
            servers_scanned += 1


if __name__ == '__main__':

    # Clear screen
    cls()

    # Parse command lind arguments
    parse_args()

    # Get total number of IPs
    num_ips = len(ip_list)
    global_num_ips = num_ips

    # Make sure there aren't more than 1000 threads
    if num_threads > 1000:
        num_threads = 1000

    # Begin scan timing
    time_start = time.time()

    ip_lists = numpy.array_split(ip_list, cpu_cores)

    # Start processes
    init_processes()

    init_display_manager()

    try:
        # Wait for threads to finish
        for thread in threads:
            while thread.is_alive():
                thread.join(3)
    except KeyboardInterrupt:
        stop = True
        print("Stopping scan (This may take a minute)")
        for thread in threads:
            thread.join()

    for worker in processes:
        worker.join()

    # End scan timing
    time_end = time.time()

    # Calculate scan timing
    total_time = math.floor(time_end - time_start)
    
    print(f"--------------------------------------------\n"
          f"MinecraftServerScanner: Done\nElapsed Time: {total_time} seconds\n"
          f"Servers Found: {mp_servers_found.value}\nServers Scanned: {mp_servers_scanned.value}\n")
