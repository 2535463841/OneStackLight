import argparse
import pika


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('queue', help='queue name')
    parser.add_argument('--host', help='rabbitmq host', required=True)
    parser.add_argument('-u', '--user', help='user', required=True)
    parser.add_argument('-p', '--password', help='password', required=True)
    parser.add_argument('-r', '--repeat', type=int, default=1,
                        help='repeat times, -1 means forever')

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

    while True:
        input_str = input(">>> ")
        if not input_str:
            continue
        if args.repeat < 0:
            while True:
                channel.basic_publish(exchange='',
                                      routing_key=args.queue,
                                      body=input_str)
        else:
            for i in range(args.repeat):
                channel.basic_publish(exchange='',
                                      routing_key=args.queue,
                                      body=input_str)


if __name__ == '__main__':
    main()
