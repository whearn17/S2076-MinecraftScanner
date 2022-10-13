# Very Fast Minecraft Server Scanner

A Multi-Threaded Minecraft Server scanner optimized for scanning a large range of IPs.

## Requirements

```
pip install mcstatus
```

## Disclaimer

You should only scan IPs that you are permitted to scan. Unauthorized
scanning can get you in trouble and I am not liable for what you choose 
to scan.

## Scanning speeds and optimization

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
server (which is why we use so many threads).

I have set a default number of threads that I feel will work best for most computers. 
You can change that number with the -n switch. It is a good idea to scan a sample list
(maybe 1k-5k hosts) and try some different options to see how it affects your speed and
the number of servers found (this may change just from people shutting their servers down
or booting them up).

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

## Postgres
The Postgres feature is still in testing but should be done relatively soon. It is available, 
however, nonetheless. It may contain bugs.

To use it, use the -pg or --postgres switches and when the program is run it will prompt for
database info.

To avoid giving myself a major headache I automatically delete the table and create it for you
every time the program is run (if you already have a table called "minecraft" make sure to change
the query in the code. It contains queries that I created and are not configurable without changing
the code.