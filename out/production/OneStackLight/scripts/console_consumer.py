import argparse
import pika


def callback(ch, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(body.decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('queue', help='queue name')
    parser.add_argument('--host', help='rabbitmq host', required=True)
    parser.add_argument('-u', '--user', help='user', required=True)
    parser.add_argument('-p', '--password', help='password', required=True)

    args = parser.parse_args()

    credentials = pika.PlainCredentials(args.user, args.password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=args.host,
                                  port=5672,
                                  virtual_host='/',
                                  credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=args.queue)

    channel.basic_consume(args.queue, callback)
    channel.start_consuming()


if __name__ == '__main__':
    main()
