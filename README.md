# Very Fast Minecraft Server Scanner

A Multi-Threaded Minecraft Server scanner optimized for scanning a large range of IPs.

## Scanning speeds and optimization

You can scan 1 Million Minecraft Servers in less than 4 hours

From my testing, using more threads and a smaller host timeout
produces a faster but more innacurate scan, potentially missing hosts. 
I used 1000 threads with a 10 second host timeout and was able to scan 
1 million IPs in a little less than 4 hours.

I would not recommend going above 1000 threads as it appears to me that 
the number of hosts discovered per scan starts to drop off as you increase 
past that point. 

My testing was done using an Intel i9-10900k overclocked to 5.2GHz. Given that 
multi-threading in Python actually runs on one processor core due to the global
interpreter lock, your results may be worse with a CPU clocked slower than mine. 
The reason that this program performs so well on one CPU core is because a TCP network 
connection is what is called a blocking operation. This means that while we wait for 
the server to respond, we don't have anything else to do, so we might as well scan another
server.

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