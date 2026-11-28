There exists a line in `server.py`, where we do `time.sleep(10)`, we also tried to curl the socket and got the following output:

The command that we ran:
`curl -v http://localhost:8080/ `

The output we got
``` 
- Host localhost:8080 was resolved.
- IPv6: ::1
- IPv4: 127.0.0.1
- Trying [::1]:8080...
- connect to ::1 port 8080 from ::1 port 33352 failed: Connection refused
- Trying 127.0.0.1:8080...
- Established connection to localhost (127.0.0.1 port 8080) from 127.0.0.1 port 43700
- using HTTP/1.x
> GET / HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/8.18.0
> Accept: */*
>
- Request completely sent off
- Recv failure: Connection reset by peer
- closing connection #0
curl: (56) Recv failure: Connection reset by peer
```

Let's understand this response and why we got this:

1. The `-v` in the curl is for the response to be `verbose`.
2. The DNS resolves to both IPv4 (127.0.0.1) and IPv6 (::1)
2. IPv6 was tried first and refused because we're using AF_INET
3. The TCP handshake for IPv4 was successful (fallback to 127.0.0.1- local computer)
4. curl writes the raw HTTP request bytes into TCP stream in the `GET / HTTP/1.1` part.
5. The failure occurs because the script ends- making the program exit and Linux closes the socket.

To fix this issue, we're going to explicitly `accept()` requests from a clint, `rescv()` the request and finally `sendall()` an appropriate response as seen below.

```
conn, addr = s.accept()
request=conn.recv(1024)
print(request)
conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nOK\r\n')
conn.close()
```

But even after the script has run successfully and exited, a second immediate run gives the following error:

```
python3 server.py
Traceback (most recent call last):
  File "/mnt/d/projects/backend-by-hand/Raw HTTP server/server.py", line 14, in <module>
    s.bind(('0.0.0.0', 8080))
    ~~~~~~^^^^^^^^^^^^^^^^^^^
OSError: [Errno 98] Address already in use
```

When your server closes the connection `conn.close()` before the client, the server `server.py` sends a FIN to the client `curl` to which the client send an ACK packet back acknowledging the FIN from the server and then it's own FIN to stop sending packets from client side. The server sends a final ACK packet back to the client on receiving this and enteres a `TIME_WAIT` state. Thus, the server waits in case the final ACK is lost and the client has to resend its FIN packet. The other reason for this state is to wait for stray packets that are yet to be received.

So what do we do to fix it? The idea is to flip a socket option flag. using the `setsockopt` method, we can flip the flag of `SO_REUSEADDR` to 1 in the `SOL_SOCKET` socket level. This only lets the `bind()` succeed while the connection is still waiting. Remember to do this before the socket object is bound to a port using `bind()`.

Try an exercise:
1. Start the server and curl it in another terminal.
2. Start the server again.
3. Instead of curling this time, run `ss -tan | grep 8080`

You'll see 2 sockets (connections)- the old socket is on `TIME-WAIT` state. Thus, `SO_REUSEADDR` doesn't remove `TIME_WAIT`.

You might be wondering what's the point of a header in a HTTP response in the following line:
```
conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nOK\r\n')
```
Remember that the response is basically raw bytes of data being sent via a TCP stream. How would the client know how to interpret or parse this data? Where to start reading from? That's where the header comes in! The headers tell the client how to read the data. For example, the `Content-Length: 4` tells the client to read exactly `4 bytes` of data from the TCP stream after the `\r\n\r\n` (which is the body of the HTTP response).

But what if the server sends a body that is actually `6 bytes` and the Content-Length is 4? The client trusts the header and reads strictly 4 bytes. The rest of the 2 bytes sits in the Linux kernel's `TCP receive buffer` (Note that this is the client side's buffer).

To understand this, you need to look at the below diagram. A typical full-duplex TCP connection b/w a client and a server looks something like this:
```
Client --- request bytes ---> Server (direction 1)
Client <--- response bytes --- Server (direction 2)
```
The 2 extra bytes are currently in the client's receive buffer. The next time the Client sends a request to the Server, there's no real issue, but when the server sends back a response- what happens? The client is expecting `HTTP/1.1` but instead reads the stale 2 bytes from the front of the `TCP receive buffer`. Thus, resulting into a parse error.

A server reponds to a client request according to what the client has asked for. It should not always respond with `OK`.

Let's first look at what a typical `/hello` HTTP request could look like. For this, we'll simply run the server in one terminal using `python3 server.py` and on another terminal, run `curl -v http://localhost:8080/hello` and look at the raw request bytes returned in the 1st terminal. It will look something like:
```
b'GET /hello HTTP/1.1\r\nHost: localhost:8080\r\nUser-Agent: curl/8.18.0\r\nAccept: */*\r\n\r\n'
```

The `Request Line` end at the first `\r\n`. Stuff after this boundary starts the header part of the request. Also, as already answered before, the `\r\n\r\n` is where the header of the request ends. Any bytes after this point is the request body (content).

The first `' '` separates the `Method` and the `Path` while the second `' '` separates the `Path` and the `HTTP version`.

Now let's try to parse and interpret a HTTP request. A typical parsing strategy could look something like this:

```
# Divide the request into head and body
head, sep, body = request.partition(b'\r\n\r\n')
print(sep)

# Divide the head into different lines
lines = head.split(b'\r\n')

# Get the method, path and version
request_line = lines[0].split(b' ')
```
If the `sep` is read empty by a server, it means that the client hasn't finished sending the header of the request. TCP is a stream of data some one particular `recv()` could possible just return a portion of the request.

But we want the entire request. Our server can't start processing with only a portion of the request. What do we do? The idea is to keep using `recv()` until we have the entire request. But when do we stop? 2 boundary conditions.

1. Boundary 1 ends at the first occurance of `\r\n\r\n`. This is where the header part of the request ends.
2. Now, how much more do we read from here? Read the `Content-Length` header from the head of the request and obey that. If the request doesn't have a `Content-Length` (or a `Transfer-Encoding` header when we cannot say the exact length beforehand) header- it just means that that request doesn't have a body and thus, Boundary 1 will suffice.

If `conn.recv()` return `b''`- it means that the client has closed it's side of the socket and has sent the FIN packet. The server needs to immediately do the following to avoid an infinite loop or burning CPU usage:

1. `break` from the `recv()` loop.
2. Close the server side of the socket.
3. Discard any incomplete/ partial requests being parsed.

What if a client keeps sending the header w/o ever sending the `\r\n\r\n` part? This is a real `DoS` (Denial of Service) attack where a bad actor could sends GBs of header bytes but never try to stop. Modern servers have a strict `Maximum header size block` to mitigate this issue.

In case that the request's header exceeds the server's allocated maximum header length, we return a `431 Request Header Fields Too Large`. Once this response is sent, the connection (socket) with the client is immediately terminated.

Once we have parsed the request and extracted the `path` out of the Request Line, we want to send an appropriate response accoding to the path. This is called routing. 

Depending on the path being asked in the Request Line, we decide on what will be inside the `status_line` and `body` of the response. The routing by itself is just a simple if-else and can be seen implemented in `server.py`.

But what about malformed requests? Requests that are not valid or make no sense? Modern HTTP parsers are quite complicated and have multiple logical checks. For our use-case, we'll just have one single gate to check whether our `Request Line` has the exact 3 parts- the `method`, the `path` and finally, the `HTTP version`. If this gate is violated, we'll return a `400 Bad Request` hinting a malformed request.

What if the request is using a method unsupported by the mentioned path? Return `405 Method Not Allowed` and pass a `Allow: GET` header in the response to let the client know what method to use the next time.

Then suppose a scenario where:

1. The path doesn't exist.
2. The method natually isn't supported for the non-existing path.

Will you return `404 Not Found` or `405 Method Not Allowed`? When it comes to request routing, first check whether the resouce exists and then, what method is allowed over the resource requested. In this case, we return a `404 Not Found`.

```
allow_header = ''
if len(request_line)!=3:
    status_line = 'HTTP/1.1 400 Bad Request'
    response_body = 'Malformed Request\r\n'
else:
    method, path, ver = request_line[0], request_line[1], request_line[2]
    if path==b'/hello':
        allowed_methods = [b'GET']
        if method in allowed_methods:
            status_line = 'HTTP/1.1 200 OK'
            response_body = 'Body of the response\r\n'
        else:
            status_line = 'HTTP/1.1 405 Method Not Allowed'
            allow_header = 'Allow: GET\r\n'
            response_body = 'This method is not allowed on /hello path'
    else:
        status_line = 'HTTP/1.1 404 Not Found'
        response_body = 'This content cannot be found\r\n'

response = f'{status_line}\r\nContent-Length: {len(response_body.encode('utf-8'))}\r\n{allow_header}\r\n{response_body}'
```
You cannot test the `400 Bad Request` using a typical curl command because it will send a good request by default. You'll need to use netcat to send malformed requests forecully into the TCP stream.
```
printf "GARBAGE\r\n\r\n" | nc localhost 8080
```
Again, to test a `DELETE` request on the server, we'll use the following commands using netcat.
```
printf 'DELETE /hello HTTP/1.1\r\n\r\n' | nc localhost 8080
printf 'GET /hello HTTP/1.1\r\n\r\n' | nc localhost 8080
printf 'DELETE /nope HTTP/1.1\r\n\r\n' | nc localhost 8080
```