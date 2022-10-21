# Very Fast Minecraft Server Scanner

A Multi-Processed and Multi-Threaded Minecraft Server scanner that is capable of scanning 5 Million IPs
per hour.

This was tested on an i9-10900K overclocked to 5.2GHz all core.

## Requirements

Required for the main module

```
pip install mcstatus psycopg2 numpy
```

## Disclaimer

You should only scan IPs that you are permitted to scan. Unauthorized
scanning can get you in trouble and I am not liable for what you choose
to scan.

## Scanning speeds and optimization

From my testing, using more threads produces a faster but more innacurate scan, potentially missing hosts. Too many threads can also stop the mcstatus module from working correctly and can throw errors.
In versions below 4.0 this was a severe limit to the speed, but the program is now multi-processed as well and doesnt suffer from this problem anymore.

I have set a default number of threads that I feel will work best for most computers.
You can change that number with the -n switch. It is a good idea to scan a sample list
(maybe 1k-5k hosts) and try some different options to see how it affects your speed and
the number of servers found (this may change just from people shutting their servers down
or booting them up). You can also change the number of processes (effectively cpu cores) with
the -p switch (though the program uses all your cores by default). This can be nice if you
want to do a more low profile scan or use less resources on your computer.

## Usage

```
usage: MinecraftServerScanner.py [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-e EXCLUDE_FILE] [-n NUM_THREADS] [-p PROCESSES]
                                 [-t HOST_TIMEOUT] [-pg]
                                 [ip_range]

positional arguments:
  ip_range              Range of IPs to scan

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        Scan a list of IPs from a file
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Output scan to a file
  -e EXCLUDE_FILE, --exclude-file EXCLUDE_FILE
                        Exclude a list of IPs from a file
  -n NUM_THREADS, --num-threads NUM_THREADS
                        Number of threads for scanning
  -p PROCESSES, --processes PROCESSES
                        Number of processes
  -t HOST_TIMEOUT, --host-timeout HOST_TIMEOUT
                        Number of seconds to wait for host to respond
  -pg, --postgres       Enable export of server list to PostgreSQL
```

## Postgres

The Postgres feature is still in testing but should be done relatively soon. It is available,
however, nonetheless. It may contain bugs.

To use it, add the -pg or --postgres switch and when the program is run it will prompt for
database info.

To avoid giving myself a major headache I automatically delete the table and create it for you
every time the program is run. I could implement a system where it queries the database and checks
to see if an IP already exists to avoid duplicates but then I would also have to check whether any
information about that server has changed. I may add this in the future but for now it stays.

The queries that I created are not configurable without changing the code. The reason for this
is because there is a finite amount of information that these minecraft servers actually give so
to create a whole system of configurable queries would be annoying and unnecessary.

### Warning

If you already have a table in your database called "minecraft" and you don't want it to be removed,
then select a different table nam when the program prompts for it.

#### To Do

- Encryption on Postgres config file
- Time formatting for scan time
- Version argument
- Organize and comment
