# Like-torrent-application
A simple application that can send data and seed data by Bittorrent Protocol
## Introduction
Current features:
- [x] Download pieces (leeching)
- [x] Contact tracker periodically
- [x] Seed (upload) pieces
- [x] Support multi-file torrents
## Getting started
Install the needed dependencies and run the unit tests with:

    $ pip install -r requirements.txt

## Design considerations
• A centralized server keeps track of which clients are connected and storing what pieces of files.

• Through tracker protocol, a client informs the server as to what files are contained in its local 
  repository but does not actually transmit file data to the server.

• When a client requires a file that does not belong to its repository, a request is sent to the server.

• Multiple clients could be downloading different files from a target client at a given point in 
  time. This requires the client code to be multithreaded

### Tracker HTTP protocol
Tracker request parameters: at start up, you are required to contact the tracker server (the 
global centralized tracker portal), submit all the appropriate support info fields.

### PEER- Downloading
After getting the list of peers from the Tracker, then connect to as many of them as 
possible start downloading from them.
These are simple TCP connections with a 2-way handshake to enter the established state.
After receiving an establish command from the peer, start downloading pieces
The last thing to do is that seeding the downloaded file to tracker

### PEER- Uploading
It wouldn't be possible to download files with your client without seeders. Therefore,peer has to begin 
seeding the file to other peers who are also interested in downloading it after downloading it.

### Command line interface
Available Commands: 
+ seed <file or file_path>               # seed file to tracker
+ download <file_name>                   # download <file_name> to downloads directory
+ end                                    # disconnect from tracker
+ list                                   # list available files
+ number_of_piece <file_name>            # get number of piece in <file_name>
+ peerlist <file_name>                   # get list of seeder for <file_name>
+ clear                                  # clear terminal

## References
There is plenty of information on how to write a BitTorrent client
available on the Internet. These two articles were the real enablers
for my implementation:

* http://www.kristenwidman.com/blog/33/how-to-write-a-bittorrent-client-part-1/

* https://wiki.theory.org/BitTorrentSpecification

