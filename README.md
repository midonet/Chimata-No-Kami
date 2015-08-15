# 岐の神 Chimata-No-Kami

This project will show you how to build a distributed architecture for a cache farm.

The MidoNet agents in this project are not running in a typical gateway configuration.

Instead we will use local veth pairs on the varnish nodes to 'uplift' the backend traffic into a midonet overlay.

The overlay itself will consist of docker containers being wired to MidoNet.

These containers run nginx webservers.

