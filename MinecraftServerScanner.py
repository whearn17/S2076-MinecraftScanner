# Author: Will
# Program: MinecraftServerScanner

import os

import dns.resolver
from minecraft_server import MinecraftServer
from database_connection import DatabaseConnection
import json
import time
import random
import socket
import logging
import argparse
import ipaddress
import threading
import multiprocessing
import mcstatus

VERSION = "5.0.0"

minecraft_server_list = []
minecraft_server_scan_timeout = 10
threads = []
processes = []
pg = False

database_hostname = ""
database_name = ""
database_username = ""
database_password = ""
database_table = ""
database_ssl_mode = ""

ip_scan_list_thread_lock = threading.Lock()


def parse_args() -> dict:
    parser = argparse.ArgumentParser(prog="MinecraftServerScanner.py")
    parser.add_argument("-i", "--input-file", type=str, help="Scan a list of IPs from a file")
    parser.add_argument("-o", "--output-file", type=str, help="Output scan to a file")
    parser.add_argument("-e", "--exclude-file", type=str, help="Exclude a list of IPs from a file")
    parser.add_argument("-n", "--num-threads", type=int, default=50, help="Number of threads for scanning")
    parser.add_argument("-p", "--processes", type=int, default=multiprocessing.cpu_count() - 2,
                        help="Number of processes")
    parser.add_argument("ip_range", type=str, nargs="?", help="Range of IPs to scan")
    parser.add_argument("-t", "--host-timeout", type=int, default=10,
                        help="Number of seconds to wait for host to respond")
    parser.add_argument("-pg", "--postgres", action="store_true", help="Enable export of server list to PostgreSQL")
    args = parser.parse_args()

    options = {
        "number_of_processes": args.processes,
        "ip_range": args.ip_range,
        "input_file": args.input_file,
        "output_file": args.output_file,
        "exclude_file": args.exclude_file,
        "number_of_threads": args.num_threads,
        "timeout": args.host_timeout,
        "pg": args.postgres,
    }

    if not (args.ip_range or args.input_file):
        parser.error('ip range or input file required')

    if args.postgres:
        try:
            config = read_database_config_from_file()

            options["database_connection_configuration"] = config

            database_connection = connect_to_database(options["database_connection_configuration"])

            database_connection.create_table()

        except FileNotFoundError:
            logging.warning("No config file found")

    return options


def connect_to_database(config: dict) -> DatabaseConnection:
    return DatabaseConnection(
        config['host'],
        config['database'],
        config['user'],
        config['password'],
        config['table'],
        config['sslmode']
    )


def read_database_config_from_command_line() -> dict:
    return {
        "host": input("Enter database hostname or ip: "),
        "database": input("Enter database name: "),
        "user": input("Enter database username: "),
        "password": input("Enter password: "),
        "table": input("Enter table name: "),
        "sslmode": input("Enter SSL mode: "),
    }


def read_database_config_from_file() -> dict:
    with open("psql.json", "r") as f:
        config: dict = json.load(f)

    for value in config.values():
        if not value:
            logging.error("Config file missing information")
            exit(1)

    return config


# Read in a list of IPs from a text file into a list
def read_ips(input_file: str):
    ip_list = []
    with open(input_file, "r") as f:
        for line in f:
            ip_list.append(line.rstrip())
    random.shuffle(ip_list)
    return ip_list


def create_ip_list_from_range(ip_range: str) -> list:
    ip_list: list = []
    for ip in ipaddress.IPv4Network(ip_range):
        ip_list.append(str(ip))

    return ip_list


# Read a list of IPs already found and remove from list
def clean_ips(ip_list: list, exclude_file: str) -> list:
    try:
        with open(exclude_file, 'r') as f:

            logging.info("Removing excluded IPs")

            number_of_excluded_ips = 0

            for line in f:
                if line.rstrip() in ip_list:
                    ip_list.remove(line.rstrip())
                    number_of_excluded_ips += 1
            logging.info(f"{number_of_excluded_ips} IPs being ignored")
    except FileNotFoundError:
        logging.error("IP Exclusion file was not found")
        time.sleep(.5)

    return ip_list


def display_found_servers(process_options: dict):
    with process_options["display_found_servers_lock"]:
        for server in minecraft_server_list:
            logging.info(server.__repr__())


def write_servers_to_file(process_options: dict):
    with process_options["write_servers_to_file_lock"]:
        with open(process_options["output_file"], "w", encoding='utf-8') as f:  # HUGE BUG HERE
            for server in minecraft_server_list:
                f.write(server.__repr__())
                f.write("\n")


def scan_ip_addresses(ip_addresses_to_scan: list, process_options: dict) -> None:
    logger = process_options["logger"]

    logger.debug(f"Thread started")

    while ip_addresses_to_scan:

        with process_options["ip_scan_list_process_lock"]:
            with ip_scan_list_thread_lock:
                if len(ip_addresses_to_scan) > 0:
                    ip = ip_addresses_to_scan.pop()
                else:
                    logger.warning(f"List empty")
                    return

        logger.debug(f"Scanning {ip}")

        try:

            server_information = mcstatus.JavaServer.lookup(ip, process_options["timeout"]).status()
            minecraft_server = MinecraftServer(ip, server_information)

            if server_information:
                logger.info(f"Hit {ip}")
                minecraft_server_list.append(minecraft_server)

                if process_options["pg"] and minecraft_server:
                    process_options["database_connection"].add_server(minecraft_server)

        except socket.timeout:
            logger.debug(f"Socket timed out")
        except (ConnectionRefusedError, ConnectionResetError, OSError):
            logger.debug("Server is offline or unreachable")
        except IndexError:
            logger.debug("Server sent malformed reponse")
        except dns.resolver.LifetimeTimeout:
            logger.debug("IP Address not found")
        except Exception as e:
            logger.error(e)

    logger.debug(f"Thread done")


def configure_logger_for_processes(logger):
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(threadName)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


# Create threads and start working
def start_threads(ip_addresses_to_scan, process_options: dict):
    for thread_id in range(process_options["number_of_threads"]):
        t = threading.Thread(target=scan_ip_addresses,
                             args=(ip_addresses_to_scan, process_options))
        t.daemon = True
        threads.append(t)
        t.start()
        time.sleep(.05)


def process_main(ip_addresses_to_scan: list, process_options: dict):
    logger: logging.Logger = configure_logger_for_processes(process_options["logger"])

    logger.debug(f"Process started")

    try:
        process_options['database_connection'] = connect_to_database(
            process_options['database_connection_configuration'])
    except Exception as e:
        logger.error(e)

    logger.debug("Database connection success")

    start_threads(ip_addresses_to_scan, process_options)

    for thread in threads:
        thread.join()

    logger.debug(f"All threads done")

    if process_options["output_file"]:
        write_servers_to_file(process_options)
    else:
        display_found_servers(process_options)


def start_processes(ip_addresses_to_scan: list, process_options: dict):
    for process_id in range(process_options["number_of_processes"]):
        p = multiprocessing.Process(target=process_main, args=(ip_addresses_to_scan, process_options))
        p.daemon = True
        processes.append(p)
        p.start()
        time.sleep(.1)

    for process in processes:
        process.join()


if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(processName)s - %(threadName)s - %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')

    logging.debug("Main process start")

    process_options = parse_args()

    process_options["logger"] = logging.getLogger()
    process_options["ip_scan_list_process_lock"] = multiprocessing.Lock()
    process_options["display_found_servers_lock"] = multiprocessing.Lock()
    process_options["write_servers_to_file_lock"] = multiprocessing.Lock()

    manager = multiprocessing.Manager()

    if process_options["ip_range"]:
        ip_addresses_to_scan: list = manager.list(create_ip_list_from_range(process_options["ip_range"]))
    elif process_options["input_file"]:
        ip_addresses_to_scan: list = manager.list(read_ips(process_options["input_file"]))

    if not ip_addresses_to_scan:
        logging.critical("No IPs to scan")
        exit(1)

    # if process_options["exclude_file"]:
    #     clean_ips(process_options["exclude_file"])

    start_processes(ip_addresses_to_scan, process_options)
