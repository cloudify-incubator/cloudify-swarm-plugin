########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

#
# Swarm plugin implementation
#
import requests
import json
from util import camelmap
from cloudify.decorators import operation
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from fabric.api import env, put, sudo


# Called when connecting to master.  Gets ip and port
@operation
def connect_manager(**kwargs):
    ctx.logger.debug("in connect_master")
    info = requests.get(
        'http://{}:{}/swarm'.format(
            ctx.node.properties['ip'],
            ctx.node.properties['port'])).json()
    ctx.instance.runtime_properties['swarm_info'] = info
    ctx.logger.info(
        "info:{}".format(
            ctx.instance.runtime_properties['swarm_info']))


@operation
def start_service(**kwargs):
    ctx.logger.debug("in start_service")

    if ctx.node.properties['compose_file'] != '':
        # get file, transfer to master, and run
        ctx.logger.debug(
            "getting compose file:{}".format(
                ctx.node.properties['compose_file']))
        path = ctx.download_resource(ctx.node.properties['compose_file'])
        if 'mgr_ssh_user' not in ctx.instance.runtime_properties:
            raise NonRecoverableError('ssh user not specified')
        if 'mgr_ssh_keyfile'not in ctx.instance.runtime_properties:
            raise NonRecoverableError('ssh keyfile not specified')
        setfabenv(ctx)
        ctx.logger.debug("putting compose file on manager")
        put(path, "/tmp/compose.in")
        ctx.logger.debug("calling compose")
        sudo("/usr/local/bin/docker-compose  -H localhost:2375 -f\
             /tmp/compose.in up")

    else:
        body = camelmap(ctx.node.properties, ['compose_file'], ['labels'])

        ctx.logger.debug("BODY={}".format(json.dumps(body)))
        resp = requests.post(
            'http://{}:{}/services/create'.format(
                ctx.instance.runtime_properties['ip'],
                ctx.instance.runtime_properties['port']),
            data=json.dumps(body),
            headers={'Content-Type': 'application/json'})

        ctx.logger.debug("RESP={} {}".format(resp.status_code, resp.text))
        if resp.status_code != 201:
            raise NonRecoverableError(resp.text)

        # get service id
        resp = json.loads(resp.text)
        ctx.instance.runtime_properties['service_id'] = resp['ID']


@operation
def add_microservice(**kwargs):
    if ctx.target.node.type == 'cloudify.nodes.DeploymentProxy':
        ctx.source.instance.runtime_properties['ip'] = (
            eval("ctx.target.instance.runtime_properties{}".
                  format(kwargs['proxy_ip_prop'])))
        ctx.source.instance.runtime_properties['port'] = (
            eval("ctx.target.instance.runtime_properties{}".
                  format(kwargs['proxy_port_prop'])))
    else:
        ctx.source.instance.runtime_properties['ip'] = \
            ctx.target.node.properties['ip']
        ctx.source.instance.runtime_properties['port'] = \
            ctx.target.node.properties['port']


@operation
def rm_service(**kwargs):
    ctx.logger.debug("in rm_microservice")
    id = ctx.instance.runtime_properties['service_id']
    resp = requests.delete(
        'http://{}:{}/services/{}'.format(
            ctx.instance.runtime_properties['ip'],
            ctx.instance.runtime_properties['port'],
            id))
    if resp.status_code != 200:
        raise NonRecoverableError(resp.text)

# Construct the fabric environment from the supplied master
# node in kwargs


def setfabenv(ctx):
    fabenv = {}
    fabenv['host_string'] = ctx.instance.runtime_properties[
        'mgr_ssh_user']+'@'+ctx.instance.runtime_properties['ip']
    fabenv['key_filename'] = ctx.instance.runtime_properties['mgr_ssh_keyfile']
    env.update(fabenv)
