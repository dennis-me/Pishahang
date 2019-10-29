# Low-latency Edge Stack - SDP/ICE/DTLS/SRTP/SCTP

## SDP - Session Description Protocol
SDP is the standard describing a peer-to-peer connection. SDP contains the codec, source address, and timing information of media and data.

## ICE - Interactive UDP connectivity establishment
ICE is useful for applications that want to establish peer-to-peer UDP data streams. It automates the process of traversing NATs and provides security against some attacks. It also allows applications to create reliable streams using a TCP over UDP layer.

## DTLS - Datagram Transport Layer Security
DTLS is a communications protocol that provides security for datagram-based applications by allowing them to communicate in a way that is designed to prevent eavesdropping, tampering, or message forgery. The DTLS protocol is based on the stream-oriented Transport Layer Security (TLS) protocol and is intended to provide similar security guarantees. The DTLS protocol datagram preserves the semantics of the underlying transport—the application does not suffer from the delays associated with stream protocols, but because it uses UDP, the application has to deal with packet reordering, loss of datagram and data larger than the size of a datagram network packet.

## SRTP - Secure Real-time transport protocol
RTP is a protocol to enable real-time connectivity for exchanging data that needs real-time priority. RTP is a data transport protocol, whose mission is to move data between two endpoints as efficiently as possible under current conditions. Those conditions may be affected by everything from the underlying layers of the network stack to the physical network connection, the intervening networks, the performance of the remote endpoint, noise levels, traffic levels, and so forth. SRTP extends RTP to bring upgraded security features.

## SCTP - Stream Control Transmission Protocol
SCTP is a transport protocol, similar to TCP and UDP, which can run directly on top of the IP protocol. However, in this case, SCTP is tunneled over a secure DTLS tunnel, which itself runs on top of UDP. The message-oriented transport supports multiplexing of multiple independent channels. Each channel supports in-order or out-of-order delivery, reliable or unreliable delivery and a priority level defined by the application. Also provides flow and congestion control mechanisms.


## Configurable Architecture
### Staking up and down

This family of network components, SDP/ICE/DTLS/SRTP/SCTP, when strictly implemented, form a powerful low-level, low-latency, end-to-end encrypted, peer-to-peer communication. Fully stacked, serves as industry-standard communications between devices, robots and services. Unstacked, serves as high-performance, low-latency network between system components.

By stacking WebRTC on top, we get low-latency multi-party peer-to-peer communication. With support for all major browsers and mobile devices.

By removing components from the top, we get fast stream-based networking over SRTP and fast message-based networking over SCTP. With optionally disabled authentication and encryption for trusted systems.

This low level stack does not provide signalling. Signalling would be provided by a centralized REST service, WebSockets server and/or a distributed libp2p network; a Reliable Edge Stack.


# Setup

On host, create pulseaudio socket
```
pactl load-module module-native-protocol-unix socket=/tmp/pulseaudio.socket
```
