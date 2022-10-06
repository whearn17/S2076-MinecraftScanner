# Very Fast Minecraft Server Scanner

You can scan 1 Million Minecraft Servers in less than 4 hours

I wouldn't recommend going above 1000 threads.

From my testing, using more threads and a smaller host timeout
produces a faster but more innacurate scan, potentially missing IPs.

##Usage
<sub>

[//]: # (    usage: MinecraftServerScanner.py [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-e EXCLUDE_FILE] [-n NUM_THREADS] [-t HOST_TIMEOUT] [ip_range])

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
      -t HOST_TIMEOUT, --host-timeout HOST_TIMEOUT
                            Number of seconds to wait for host to respond
</sub>