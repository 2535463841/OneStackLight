import json
import unittest
import pika
import socket

from common import config

CONF = config.CONF


class TestAMQPInstall(unittest.TestCase):
    """Test Keystone Functions With Openstack CLI
    """

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self) -> None:
        self.transport_url = 'rabbit://{0}:${1}@{2}'.format(
            CONF.amqp.openstack_user, CONF.amqp.openstack_pass,
            socket.gethostname())
        self.queue = self.__class__.__name__

    def test_producer_and_consumer(self):
        test_body = json.dumps({'test': 1111})
        credentials = pika.PlainCredentials(
            CONF.amqp.openstack_user, CONF.amqp.openstack_pass)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=socket.gethostname(),
                                      port=5672,
                                      virtual_host='/',
                                      credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue=self.queue)
        channel.basic_publish(exchange='',
                              routing_key=self.queue,
                              body=test_body)

        def callback(ch, method, properties, body):
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.assertEqual(body.decode(), test_body)
            channel.stop_consuming()

        channel.basic_consume(self.queue, callback)
        channel.start_consuming()
