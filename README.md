## Cloudify Swarm Plugin

This project contains a plugin that enables Cloudify to install, configure, and run services on a Docker Swarm Cluster:

Limitations:
+ Only works for Docker 1.12+
+ Only tested on Docker 1.12

### Plugin components

#### cloudify.swarm.Manager

Represents a Swarm manager node.  This simple type is provided just to provide connection info for the `cloudify.swarm.Microservice` type, in the case that the manager is not managed by Cloudify.  It is expected that a Manager managed by Cloudify will be referenced using the DeploymentProxy plugin.

<b>Significant properties</b>
+ ip          the IP address of the manager server
+ port        the port of the server (default 2375)
+ ssh_user    the ssh user to access the host.  Only needed if using Docker Compose for the service
+ ssh_keyfile the ssh key file to access the host.  Only needed if using Docker Compose for the service

#### cloudify.swarm.Microservice node type

Represents a service in a Swarm cluster.  Requires the [`cloudify.swarm.relationships.microservice_contained_in_manager`](#conn-to-manager) relationship to get connection information. A service can be defined either by referencing a docker [Compose](https://docs.docker.com/compose/) descriptor, or by setting properties directly in the node template definition.  If using node properties, refer to the "create a service" section in the Docker remote [REST API](https://docs.docker.com/engine/reference/api/docker_remote_api_v1.24#create-a-service).  The properties of the type are specified by a simple conversion of the native camel case: camel case identifiers in the REST are converted by separating camel case words with underscores, and converting to lower case.  Example: LogDriver == log_driver.  See the example blueprint for more details.

#### cloudify.swarm.relationships.microservice_contained_in_manager relationship <a id="#conn-to-master"></a>

Just retrieves the master ip and port for use by the dependent node.  Can be targeted at either a cloudify.swarm.Manager node or a [cloudify.nodes.DeploymentProxy](https://github.com/cloudify-examples/cloudify-proxy-plugin) instance.

