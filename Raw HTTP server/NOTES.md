After reaching line 22 in `server.py`, where we do `time.sleep(10)`, we also tried to curl the socket and got the following output:

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
conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK\r\n')
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