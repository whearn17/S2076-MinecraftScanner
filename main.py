# Author: Will
# Program: MinecraftServerScanner

import os
import time
import math
import socket
import threading
import datetime
from mcstatus import JavaServer

PORT = 25565
ip_list = []
threads = []
num_ips = 0
num_threads = 0
work_per_thread = 0
timeout = 10

ip_read_file = "potential_servers.txt"
ip_hit_file = "ip-hit.txt"
log_file = "log.txt"
server_file = "server-list.txt"


global servers_found
servers_found = 0

global servers_scanned
servers_scanned = 0


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def log(filename, message):
    f = open(filename, "a", encoding="utf-8")
    f.write(message)
    f.close()


def display_statistics():
    while servers_scanned < num_ips:
        cls()
        percent_done = math.floor((servers_scanned / num_ips) * 100)
        print(f"{percent_done}% Done")
        print(f"Servers Found: {servers_found}")
        print(f"Servers Scanned: {servers_scanned}")
        time.sleep(3)


# Read in a list of IPs from a text file into a list
def read_ips():
    with open(ip_read_file, "r") as f:
        for line in f:
            ip_list.append(line.rstrip())
    f.close()


# Read a list of IPs already found and remove from list
def clean_ips():
    try:
        f = open(ip_hit_file, "r")
        print("Reading IPs to be ignored (this may take a while)")
        skip = 0
        for line in f:
            if line.rstrip() in ip_list:
                ip_list.remove(line.rstrip())
                skip += 1
        print(f"[INFO] {skip} IPs being ignored")
    except FileNotFoundError:
        print("[INFO] No IPs being ignored")


# Use the mcstatus lookup method to search for a server
def query(host):
    scan = JavaServer.lookup(host, timeout)
    status = scan.status()
    return(f"Minecraft: {status.version.name} Protocol ({status.version.protocol}) \nDescription: "
           f"{status.description} \n{status.players.online}/{status.players.max}\n{host}\n\n")


# Cycle through the portion of IP list that belongs to current thread
def cycle(start, end):
    # Keep track of number of IPs scanned
    count = 0

    # Keep track of servers found
    global servers_found
    global servers_scanned

    for ip in ip_list[start:end]:
        try:
            # Increment count for scanned IPs
            count += 1
            servers_scanned += 1

            # Query a server for info
            server = query(ip)
            servers_found += 1

            # If server is found write its information to file
            log(server_file, server)

            """ If server is found write its IP to a file
                This is so I can scan with the same list
                multiple times and avoid duplicates
            """
            log(ip_hit_file, f"{ip}\n")

        except socket.timeout:
            pass
        except ConnectionResetError:
            pass
        except ConnectionRefusedError:
            pass
        except OSError:
            pass

    # Threads log to a file when they are done
    log(log_file, f"[INFO] {threading.get_ident()} -> done ({datetime.datetime.now()})\n"
        f"[INFO] IPs scanned: {count}\n\n")


if __name__ == '__main__':
    read_ips()
    clean_ips()

    # Set number of threads
    num_threads = input("Enter number of threads: ")
    num_threads = int(num_threads)

    # Clear screen
    cls()

    # Get total number of IPs
    num_ips = len(ip_list)

    # Calculate how many IPs each thread should scan
    work_per_thread = math.floor(num_ips / num_threads)
    leftover = (num_ips - (work_per_thread * num_threads))

    # Logging info for the start of scan
    log(log_file, f"[INFO] IPs to be scanned: {num_ips}\n"
        f"[INFO] Number of threads selected: {num_threads}\n"
        f"[INFO] Work per thread: {work_per_thread}\n"
        f"[INFO] Leftover work for main thread: {leftover}\n\n")

    # Create each thread and assign a chunk of work to it
    for i in range(num_threads):
        thread = threading.Thread(
            target=cycle, args=(work_per_thread * i, work_per_thread * i + work_per_thread,))
        threads.append(thread)
        thread.start()

    thread = threading.Thread(target=display_statistics)
    threads.append(thread)
    thread.start()

    # If number of IPs / number of threads has leftover work main thread takes care of it
    if leftover > 0:
        cycle(num_ips - leftover - 1, num_ips - 1)

    # Wait for threads to finish
    for thread in threads:
        thread.join()

    # End of scan
    log(log_file, "-------------------------------------------------------------------------\n\n")
