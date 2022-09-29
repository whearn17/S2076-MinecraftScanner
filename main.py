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
timeout = 20

global servers_found
servers_found = 0

global servers_scanned
servers_scanned = 0


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def display_statistics():
    while len(ip_list) > 0:
        percent_done = servers_scanned / num_ips
        print(f"{percent_done}% Done")
        print(f"Servers Found: {servers_found}")
        time.sleep(10)
        cls()


# Read in a list of IPs from a text file into a list
def read_ips():
    with open("potential_servers.txt", "r") as f:
        for line in f:
            ip_list.append(line.rstrip())
    f.close()


# Read a list of IPs already found and remove from list
def clean_ips():
    try:
        f = open("ip-hit.txt", "r")
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

            # Remove IP from list for statistics
            # ip_list.remove(ip)

            # Query a server for info
            server = query(ip)
            servers_found += 1

            # If server is found write its information to file
            f = open("server-list.txt", "a")
            f.write(server)
            f.close()

            """ If server is found write its IP to a file
                This is so I can scan with the same list
                multiple times and avoid duplicates
            """
            f = open("ip-hit.txt", "a")
            f.write(f"{ip}\n")
            f.close()
        except socket.timeout:
            pass
        except ConnectionResetError:
            pass
        except ConnectionRefusedError:
            pass
        except OSError:
            pass
    # Threads log to a file when they are done
    f = open("log.txt", "a")
    f.write(f"[INFO] {threading.get_ident()} -> done ({datetime.datetime.now()})\n")
    f.write(f"[INFO] IPs scanned: {count}\n\n")
    f.close()


if __name__ == '__main__':
    read_ips()
    clean_ips()

    num_threads = input("Enter number of threads: ")
    num_threads = int(num_threads)

    num_ips = len(ip_list)

    # Calculate how many IPs each thread should scan
    work_per_thread = math.floor(num_ips / num_threads)
    print(f"Work per thread -> {work_per_thread}")
    leftover = (num_ips - (work_per_thread * num_threads))

    file = open("log.txt", "a")
    file.write(f"[INFO] IPs to be scanned: {num_ips}\n")
    file.write(f"[INFO] Number of threads selected: {num_threads}\n")
    file.write(f"[INFO] Work per thread: {work_per_thread}\n")
    file.write(f"[INFO] Leftover work for main thread: {leftover}\n\n")
    file.close()

    # Create each thread and assign a chunk of work to it
    for i in range(num_threads):
        thread = threading.Thread(
            target=cycle, args=(work_per_thread * i, work_per_thread * i + work_per_thread,))
        threads.append(thread)
        thread.start()

    thread = threading.Thread(target=display_statistics).start()
    threads.append(thread)

    # If number of IPs / number of threads has leftover work main thread takes care of it
    if leftover > 0:
        cycle(num_ips - leftover - 1, num_ips - 1)

    # Wait for threads to finish
    for thread in threads:
        thread.join()

    file = open("log.txt", "a")
    file.write("-------------------------------------------------------------------------\n\n")
    file.close()
