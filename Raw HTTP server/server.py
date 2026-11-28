import socket
import time

# Documentation to refer to: https://docs.python.org/3/library/socket.html#socket-families
# Note that the documentation mentioned above is quite detailed and as such, I'll be using Gemini as an external assistant to skim past the content
# We're trying to open a socket here: a socket is a program's phone line to the network
# AF_INET is Address Family- AF_INET is for IPv4 while AF_INET6 is for IPv6
# The second argument is for picking the type of socket- SOCK_STREAM would be for TCP (because TCP is streams of data and packets arrive in order. Nothing marks where a TCP send ends.) while UDP is SOCK_DGRAM (packets are using a datagram and not in order and each datagram is received as a whole).
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# We want to reuse the server address immediately after the socket is closed by the server when we do conn.close().
# We flip a socket option to 1.
# The 1st argument (Socket Layer - Socket) tells us which Socket level's socket options we'll be using.
# The 2nd argument is the option whose flag we will flip- in this case being the reuse-address flag- and we're setting it to 1 in the 3rd argument
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Now bind the socket to a port
# 0.0.0.0 is a wildcard for "Accept all incoming traffic"; you could also use 127.0.0.1 for your own machine
# <socket>.bind() takes one argument so pass the IP and the port in one tuple
s.bind(('0.0.0.0', 8080))

# Now that we have bound a port to the socket, let's allow the socket to listen to incoming traffic using the listen() method
# listen() flips a switch on the Linux OS kernel to passively listen to requests coming on port 8080
s.listen()

# If we end the program here, the kernel listens for only a fraction of a second, so we make the script to wait (sleep) for a while so that we can verify whether the kernel is actually listening on 8080
# We can check this using 'ss -tlnp | grep 8080'
#time.sleep(10)

# The 3-way TCP handshake (SYN, SYN-ACK, ACK) is done in the background by the Linux kernel in the background.
# We'll be using accept() purely for queue-popping and socket-creation b/w the curl (client) and server,py (server).
# conn is a different socket object that is different from s; it is purely for this particular client use-case
# addr stores the IP and ephimeral source port
conn, addr = s.accept()

# Read the client request using conn.recv(bytes) and receive upto (not exactly) <bytes> bytes of data from the request TCP stream.
request=conn.recv(1024)

# Now, we'll parse this request to get it's path and send an appropriate response.
# The parsing logic is already mentioned in NOTES.md
head, sep, body = request.partition(b'\r\n\r\n')
lines=head.split(b'\r\n')
request_line=lines[0].split(b' ')

# For now, a malformed request is any request that doesn't agree with out parsing logic. Actual parsers are way more complicated.
# We will use 'printf 'GARBAGE\r\n\r\n' | nc localhost 8080' for testing.
# Please note that the entire 'HTTP/1.1 200 OK' is the status line.
if len(request_line)!=3:
    status_line = 'HTTP/1.1 400 Bad Request'
    response_body = 'Malformed Request\r\n'
else:
    method, path, ver = request_line[0], request_line[1], request_line[2]
    if path==b'/hello':
        status_line = 'HTTP/1.1 200 OK'
        response_body = 'Body of the response\r\n'
    else:
        status_line = 'HTTP/1.1 404 Not Found'
        response_body = 'This content cannot be found\r\n'

response = f'{status_line}\r\nContent-Length: {len(response_body.encode('utf-8'))}\r\n\r\n{response_body}'
# Finally, send a syntax-strict HTTP response to the client and then close the connection.
# "200 OK" belongs to status line and is not part of the body.
# Content-Length is part of the header.
# An extra \r\n tells the client that the header has ended.
# Anything after the \r\n\r\n is the body of the HTTP response and the number of bytes there reflects the Content-Length. Things like '\r' or '\n' and simple English Letters are 1 byte each. Even a space character (' ') is 1 byte. If you're unsure about the length of the body, just use len(response_body.encode('utf-8)) and make Python do the magic.
# Content-Length is measured over the bytes version of the response body, not the str version.
# Read up NOTES.md for understanding the point of headers in a HTTP response. The b'..' is for 'bytes'.
# We're using utf-8 (Unicode transformation format) to convert the str into bytes for TCP stream
conn.sendall(response.encode('utf-8'))
conn.close()
print("Connection closed from Server side.")

# Read up on TIME_WAIT in NOTES.md and how it works after the socket is closed by the Linux kernel. SO_REUSEADDR socket option flag helps us immediately use the address while we wait for TIME_WAIT to finish. Read this up in NOTES.md.