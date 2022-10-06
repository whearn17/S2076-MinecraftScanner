# Very Fast Minecraft Server Scanner


## Scanning speeds

You can scan 1 Million Minecraft Servers in less than 4 hours

From my testing, using more threads and a smaller host timeout
produces a faster but more innacurate scan, potentially missing IPs. 
I used 1000 threads with a 10 second host timeout and was able to scan 
1 million IPs in a little less than 4 hours.

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
      -t HOST_TIMEOUT, --host-timeout HOST_TIMEOUT
                            Number of seconds to wait for host to respond
```