# Very Fast Minecraft Server Scanner

A high-performance Minecraft Server scanner capable of scanning over 5 million IPs per hour, utilizing multi-processing 
and multi-threading techniques for blazing-fast results. Developed and tested on an i9-10900K overclocked to 5.2GHz 
all-core.

## Requirements

For the main module, install the following dependencies:

```
pip install mcstatus psycopg2
```

## Disclaimer

Please ensure that you only scan IPs that you have permission to scan. Unauthorized scanning can lead to legal issues, 
and I am not liable for any consequences resulting from your scanning activities.

## Technical Breakdown

This powerful scanner leverages the capabilities of modern hardware by implementing a combination of multi-processing 
and multi-threading, ensuring maximum utilization of available resources.

### Multi-threading

The program employs multiple threads to scan hosts concurrently, allowing for faster scanning without being limited by a
single-threaded approach. However, it's essential to strike a balance between the number of threads and accuracy, as too
many threads can lead to missed hosts or errors in the mcstatus module.

### Multi-processing

To further enhance performance, the scanner uses multiple processes, taking advantage of all available CPU cores. This 
approach effectively eliminates the bottleneck caused by using only a single process, significantly boosting the 
scanning speed.

### Scanning Speeds and Optimization
The default number of threads has been set to deliver optimal performance for most systems. However, you can fine-tune 
the scanner by adjusting the number of threads with the -n switch or the number of processes with the -p switch. 
Experimenting with different configurations on a sample list of 1k-5k hosts can help you find the most efficient setup 
for your hardware.

## Usage

```
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

## PostgreSQL Integration 

This scanner supports seamless integration with PostgreSQL, allowing you to export server lists directly to a database.
IP addresses are the primary key of the database and every time the scanner finds a server which already exists in the
database, it updates the record to reflect the new results. This means that you can run the scanner without worrying
about having to shut your computer down because the scanner will continue collecting servers and adding them.

#### To Do

- Encryption on Postgres config file
- Time formatting for scan time
- Version argument
