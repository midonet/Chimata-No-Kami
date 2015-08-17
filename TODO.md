The micro segmentation is done, as well as the bridges, routers and routes.

We now need to either run BGP or static routing on the varnish nodes with veth pairs

For this the edge router will get ips from 192.168.253/24

These ips will pair with veth pairs on the varnish boxes.

The varnish servers must either run BGPd from quagga or get static routes inserted.

Due to the number of microsegments it probably makes more sense to run bgp session state.

