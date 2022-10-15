# Reading in configuration files for Postgres

import json
import getpass


def read_config(file):
    db_host = ""
    db_name = ""
    db_user = ""
    db_pass = ""
    db_table = ""
    sslmode = ""

    keycount = 0
    valuecount = 0

    try:
        with open(file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Configuration file can't be found")
        db_host, db_name, db_user, db_pass, db_table, sslmode = read_input()
        return db_host, db_name, db_user, db_pass, db_table, sslmode

    for key, value in data.items():

        if key:
            keycount += 1

        if value:
            valuecount += 1

        if valuecount > 0 and not value:
            print(f"[CONFIG] {key} has no value")

        if key == "db_host":
            db_host = value
        elif key == "db_name":
            db_name = value
        elif key == "db_user":
            db_user = value
        elif key == "db_pass":
            db_pass = value
        elif key == "db_table":
            db_table = value
        elif key == "ssl_mode":
            sslmode = value

    if valuecount < 6:
        db_host, db_name, db_user, db_pass, db_table, sslmode = read_input()

    return db_host, db_name, db_user, db_pass, db_table, sslmode


def read_input():
    db_host = input("Enter server hostname or IP: ")
    db_name = input("Enter Database name: ")
    db_user = input("Enter Database username: ")
    db_pass = getpass.getpass("Enter Database password: ")
    db_table = input("Enter table name: ")
    sslmode = input("SSL Mode (Disable/Allow/Prefer/Require): ").lower()

    return db_host, db_name, db_user, db_pass, db_table, sslmode
