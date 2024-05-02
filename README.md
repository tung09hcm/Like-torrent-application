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
    pip install -r requirements.txt
## Design considerations
• A centralized server keeps track of which clients are connected and storing what pieces of files.

• Through tracker protocol, a client informs the server as to what files are contained in its local 
  repository but does not actually transmit file data to the server.

• When a client requires a file that does not belong to its repository, a request is sent to the server.

• Multiple clients could be downloading different files from a target client at a given point in 
  time. This requires the client code to be multithreaded
## References
There is plenty of information on how to write a BitTorrent client
available on the Internet. These two articles were the real enablers
for my implementation:

* http://www.kristenwidman.com/blog/33/how-to-write-a-bittorrent-client-part-1/

* https://wiki.theory.org/BitTorrentSpecification

