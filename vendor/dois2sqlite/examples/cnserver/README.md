# Example Content Negotiation server

This code demonstrates a simple content negotiation server that handles client requests and responds with the appropriate content based on the requested media type.

If the requested media type is not supported, the server responds with a 406 Not Acceptable status code. If the requested media type is supported, the server generates the content for that media type and sends it back in the response with the appropriate Content-Type header.

The server also supports content negotiation based on the `Accept-Language` header. If the client specifies a preferred language, the server can respond with content in that language if available.

Note: This is just an example code and may not be suitable for production use. It is intended to demonstrate the concept of content negotiation in a simple server implementation.

## To run the server

```
python app.py PATH_TO_SQLITE_DB
```

## To test the server

```
python cn-quick-test.py 100-random-dois.txt
```
