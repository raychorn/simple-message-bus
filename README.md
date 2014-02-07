simple-message-bus
==================

Simple Message Bus

Version 1.0.0.0

This is a very simplistic view of a minimalistic message bus that transmits information from one process to another
through the Windows filesystem.

Place a file in message_box1 and the file will be moved into message_box2 and then on to message_box3.

Why is this useful ?

TCP/IP can be a bit problematic expecially when a required listener does not exist.  REST Web Service communications
between processes can fail when a listener is not available.

Simple Message Bus can resolve issues when a process may not be available all the time. Messages in the form of
small files will collect in a directory until the process that's supposed to handle them comes alive.

This version is minimally functional with the following features:

** TCP/IP Bridge is functional - designed to handle JSON-based or ASCII based data however with
some additional work it could handle binary data with CRC32 however CRC32 does tend to detract
from the current performance profile.

** Publisher/Subscriber is built-in.  Each instance of the Simple Message Bus becomes a separate
publisher/subscriber where the topic is the Simple Message Bus instance - subscrivers are left
to figure themselves out in relation to how they choose to handle messages from the bus.

** Bidirectional Communications is functional now however some additional work would have to be 
done to make the Simple Message Bus operate in a reverse direction - all you have to do is deploy
yet another instance to facilitate communications in a reverse direction but you probably
already knew this, right ?

Give this demo a try and look at the source code.

Enjoy.
