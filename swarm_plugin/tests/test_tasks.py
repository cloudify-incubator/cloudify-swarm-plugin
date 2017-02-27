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

# Built-in Imports
import testtools
import requests
import fabric

# Third Party Imports

# Cloudify Imports is imported and used in operations
from swarm_plugin import tasks
from mock import patch, mock_open
# from cloudify import manager
from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext, MockContext
from cloudify.exceptions import NonRecoverableError

_test_open = mock_open()


class MockResponse():

    def __init__(self, text='', json='', status_code=0):
        self._text = text
        self._json = json
        self._status_code = status_code

    @property
    def text(self):
        return self._text

    def json(self):
        return self._json

    @property
    def status_code(self):
        return self._status_code


class TestSwarmTasks(testtools.TestCase):

    @patch('swarm_plugin.tasks.requests.get', spec=requests.get)
    def test_connect_manager(self, mock_get):

        ctx = MockCloudifyContext(node_id='test',
                                  properties={
                                      'ip': '1.1.1.1',
                                      'port': 80
                                     },
                                  runtime_properties={
                                     }
                                  )
        current_ctx.set(ctx=ctx)
        test_json = '{"key":"val"}'
        mock_get.return_value = MockResponse("dummy_text", test_json)
        tasks.connect_manager()

        self.assertEquals(mock_get.call_count, 1)
        self.assertEquals(
            test_json,
            ctx.instance.runtime_properties['swarm_info'])

    @patch('swarm_plugin.tasks.sudo', spec=fabric.api.sudo)
    @patch('swarm_plugin.tasks.put', spec=fabric.api.put)
    def test_start_service_compose(self, mock_put, mock_sudo):
        ctx = MockCloudifyContext(node_id='test',
                                  properties={
                                      'compose_file': 'dummy.compose',
                                     },
                                  runtime_properties={
                                      'ip': '1.1.1.1.',
                                      'port': '9999',
                                      'mgr_ssh_user': 'user',
                                      'mgr_ssh_keyfile': 'keyfile',
                                     }
                                  )
        ctx.download_resource = lambda self: "nopath"
        current_ctx.set(ctx=ctx)
        tasks.start_service()
        self.assertEquals(1, mock_sudo.call_count)
        self.assertEquals(1, mock_put.call_count)

    @patch('swarm_plugin.tasks.requests.post', spec=requests.post)
    def test_start_service_props(self, mock_post):

        ctx = MockCloudifyContext(node_id='test',
                                  properties={
                                      'compose_file': '',
                                      'key_one': 'val1',
                                      'key_two': {'key_three': 'val3'}
                                     },
                                  runtime_properties={
                                      'ip': '1.1.1.1.',
                                      'port': '9999'
                                     }
                                  )
        mock_post.return_value = MockResponse(text='{"ID": "1234"}',
                                              status_code=201)
        current_ctx.set(ctx=ctx)
        tasks.start_service()
        self.assertEquals(1, mock_post.call_count)
        self.assertEquals("1234", ctx.instance.runtime_properties['service_id'])
        self.assertEquals({"KeyOne": "val1", "KeyTwo": {"KeyThree": "val3"}},
                          eval(mock_post.mock_calls[0][2]['data']))

    def test_add_microservice_proxy(self):

        ctx = MockCloudifyContext(
            source=MockContext({
                'instance': MockContext({
                    'runtime_properties': {}
                })
            }),
            target=MockContext({
                'node': MockContext({
                    'type': 'cloudify.nodes.DeploymentProxy'
                }),
                'instance': MockContext({
                     'runtime_properties': {
                         'swarm_info': {
                             'manager_ip': '1.1.1.1',
                             'manager_port': '1231'
                         }
                         }
                })
            })
        )
        current_ctx.set(ctx=ctx)
        tasks.add_microservice(proxy_ip_prop='["swarm_info"]["manager_ip"]',
                               proxy_port_prop='["swarm_info"]["manager_port"]'
                               )
        self.assertEquals(
            ctx.source.instance.runtime_properties['ip'],
            '1.1.1.1')
        self.assertEquals(
            ctx.source.instance.runtime_properties['port'], '1231')

    def test_add_microservice_node(self):

        ctx = MockCloudifyContext(
            source=MockContext({
                'instance': MockContext({
                    'runtime_properties': {}
                })
            }),
            target=MockContext({
                'node': MockContext({
                    'type': 'cloudify.swarm.Manager',
                    'properties': {
                        'ip': '1.1.1.1',
                        'port': '1232'
                    }
                }),
                'instance': MockContext({
                })
            })
        )
        current_ctx.set(ctx=ctx)
        tasks.add_microservice()

        self.assertEquals(
            ctx.source.instance.runtime_properties['ip'],
            '1.1.1.1')
        self.assertEquals(
            ctx.source.instance.runtime_properties['port'], '1232')

    @patch('swarm_plugin.tasks.requests.delete', spec=requests.delete)
    def test_rm_microservice(self, mock_delete):

        ctx = MockCloudifyContext(node_id='test',
                                  properties={
                                     },
                                  runtime_properties={
                                      'ip': '1.1.1.1.',
                                      'port': '9999',
                                      'service_id': '123456'
                                     }
                                  )
        mock_delete.return_value = MockResponse(status_code=200)
        current_ctx.set(ctx=ctx)
        tasks.rm_service()

    @patch('swarm_plugin.tasks.requests.delete', spec=requests.delete)
    def test_rm_microservice_fail(self, mock_delete):

        ctx = MockCloudifyContext(node_id='test',
                                  properties={
                                     },
                                  runtime_properties={
                                      'ip': '1.1.1.1.',
                                      'port': '9999',
                                      'service_id': '123456'
                                     }
                                  )
        mock_delete.return_value = MockResponse(status_code=500)
        current_ctx.set(ctx=ctx)
        self.assertRaises(NonRecoverableError,
                          lambda: tasks.rm_service())
