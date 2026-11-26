After readching line 22 in `server.py`, where we do `time.sleep(10)`, we also tried to curl the socket and got the following output:

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