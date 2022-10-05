# Author: Will
# Program: MinecraftServerScanner

import os
import time
import math
import socket
import argparse
import traceback
import threading
import dns.resolver
from mcstatus import JavaServer

PORT = 25565
ip_list = []
threads = []
num_ips = 0
num_threads = 0
work_per_thread = 0
timeout = 10

ip_read_file = ""
ip_exclude_file = ""
log_file = "log.txt"
server_file = ""

server_list = []

servers_found = 0
servers_scanned = 0

file_lock = threading.Lock()
server_list_lock = threading.Lock()
servers_scanned_lock = threading.Lock()


def init_threads():
    # Create each thread and assign a chunk of work to it
    for i in range(num_threads):
        thread = threading.Thread(
            target=cycle, args=(work_per_thread * i, work_per_thread * i + work_per_thread,))
        threads.append(thread)
        thread.start()

    thread = threading.Thread(target=display_statistics)
    threads.append(thread)
    thread.start()


def parse_args():
    global ip_read_file
    global ip_exclude_file
    global server_file
    global num_threads

    args = init_args()

    # Input IP file argument
    if args.input_file:
        ip_read_file = args.input_file
        read_ips()

    # Output scan to file argument
    if args.output_file:
        server_file = args.output_file

    # Ignore IPs from file argument
    if args.exclude_file:
        ip_exclude_file = args.exclude_file
        clean_ips()

    # Number of threads argument
    if args.threads:
        num_threads = args.threads
    else:
        num_threads = 100


def init_args():
    parser = argparse.ArgumentParser(prog="MinecraftServerScanner.py")

    # Input IP file argument
    parser.add_argument("-i", "--input-file", type=str, help="Scan a list of IPs from a file", dest="input_file")

    # Output scan to file argument
    parser.add_argument("-o", "--output-file", type=str, help="Output scan to a file", dest="output_file")

    # Ignore IPs from file argument
    parser.add_argument("-e", "--exclude-file", type=str, help="Exclude a list of IPs from a file", dest="exclude_file")

    # Number of threads argument
    parser.add_argument("-t", "--threads", type=int, help="Number of threads for scanning", dest="threads")

    return parser.parse_args()


def add_server(addr):
    with server_list_lock:
        server_list.append(addr)


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def log(filename, message):
    if not filename:
        return
    with file_lock:
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


# Use the mcstatus lookup method to search for a server
def query(host):
    scan = JavaServer.lookup(host, timeout)
    status = scan.status()
    return(f"Minecraft: {status.version.name} Protocol ({status.version.protocol}) \nDescription: "
           f"{status.description} \n{status.players.online}/{status.players.max}\n{host}\n\n")


# Cycle through the portion of IP list that belongs to current thread
def cycle(start, end):
    # Keep track of servers found
    global servers_found
    global servers_scanned

    for ip in ip_list[start:end]:
        try:

            # Query a server for info
            server = query(ip)
            add_server(server)
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
        except Exception as e:
            log("fail.txt", f"[ERROR] An unkown error occured... Scanning will continue\n\n"
                            f"traceback.format_exc()\n")
            print(e)

        # Increment count for scanned IPs
        with servers_scanned_lock:
            servers_scanned += 1


if __name__ == '__main__':

    # Clear screen
    cls()

    # Parse command lind arguments
    parse_args()

    print(f"[INFO] IPs to be scanned: {len(ip_list)}")

    # Clear screen
    cls()

    # Get total number of IPs
    num_ips = len(ip_list)

    # Calculate how many IPs each thread should scan
    work_per_thread = math.floor(num_ips / num_threads)
    leftover = (num_ips - (work_per_thread * num_threads))

    # Begin scan timing
    time_start = time.time()

    # Start threads
    init_threads()

    # If number of IPs / number of threads has leftover work main thread takes care of it
    if leftover > 0:
        cycle(num_ips - leftover - 1, num_ips - 1)

    # Wait for threads to finish
    for worker in threads:
        worker.join()

    # End scan timing
    time_end = time.time()

    # Calculate scan timing
    total_time = math.floor(time_end - time_start)

    cls()

    for item in server_list:
        print(item)

    print(f"MinecraftServerScanner: Done\nElapsed Time: {total_time} seconds\n"
          f"Servers Found: {servers_found}\nServers Scanned: {servers_scanned}\n"
          f"--------------------------------------------\n\n")
