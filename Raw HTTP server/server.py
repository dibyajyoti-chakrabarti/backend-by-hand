import socket

# Documentation to refer to: https://docs.python.org/3/library/socket.html#socket-families
# Note that the documentation mentioned above is quite detailed and as such, I'll be using Gemini as an external assistant to skim past the content
# We're trying to open a socket here: a socket is a program's phone line to the network
# AF_INET is Address Family- AF_INET is for IPv4 while AF_INET6 is for IPv6
# The second arhument is for picking the type of socket- SOCK_STREAM would be for TCP (because TCP is streams of data and packets are preserved in order) while UDP is SOCK_DGRAM (packets are using a datagram and not in order).
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Now bind the socket to a port
# 0.0.0.0 is a wildcard for "Accept all incoming traffic"; you could also use 127.0.0.1 for your own machine
# <socket>.bind() takes one argument so pass the IP and the port in one tuple
s.bind(('0.0.0.0', 8080))