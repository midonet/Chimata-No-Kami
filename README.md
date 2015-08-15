# 岐の神 Chimata-No-Kami

This project will show you how to build a distributed architecture for a cache farm.

The MidoNet agents in this project are not running in a typical gateway configuration with two network cards, one of them being used for BGP or static routing.

Instead we will use local veth pairs on the varnish nodes to 'uplift' the backend traffic into the virtual networking layer of a midonet overlay.

This makes it possible to run part (or all) of this architecture in a public cloud or on servers in a datacenter with one NIC.

The overlay itself will consist of docker containers being wired to MidoNet.

The containers will run nginx webservers.

