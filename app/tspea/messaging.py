import pika
import uuid
import json
import threading
import time
import logging
from .utils import print_progress_bar

Log = logging.getLogger(__name__)


TASK_QUEUE = 'task_queue'
TERM_SIG_EXCHANGE = 'term_signal_exchange'
TERM_QUEUE = 'term_queue'
TYPE = 'type'
MATE = 'mate'
MUTATE = 'mutate'
ID = 'id'
FIRST = '_1'
SECOND = '_2'
GEN = 'gen'
TERMINATE = 'terminate'


def declare_topology(channel):
    channel.queue_declare(queue=TASK_QUEUE, durable=True, exclusive=False, auto_delete=False)
    channel.exchange_declare(exchange=TERM_SIG_EXCHANGE, exchange_type='fanout')


def ack_message(channel, delivery_tag):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        channel.basic_ack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass


class _TaskPublisher(object):

    def __init__(self, broker_url, show_feedback=False):
        self.show_feedback = show_feedback
        self.response = []
        self.num_processed_tasks = 0
        self.pending_tasks = dict()
        # setup channel
        self.connection = pika.BlockingConnection(pika.URLParameters(broker_url))
        self.channel = self.connection.channel()
        declare_topology(self.channel)
        result = self.channel.queue_declare(exclusive=True)  # response queue
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.__on_response, no_ack=True, queue=self.callback_queue)
        self.lock = threading.Lock()
        if self.show_feedback:
            self.feedback_thread = threading.Thread(target=self.__print_progress)

    def __print_progress(self):
        while len(self.pending_tasks) > 0:
            time.sleep(0.1)
            self.lock.acquire()
            try:
                iteration = self.num_processed_tasks
                total = self.num_processed_tasks + len(self.pending_tasks);
            finally:
                self.lock.release()
            print_progress_bar(iteration, total, prefix='Progress:', suffix='Complete', bar_length=50)

    def __on_response(self, ch, method, props, body):
        if props.correlation_id in self.pending_tasks:
                task_id = self.pending_tasks[props.correlation_id]
                r = json.loads(body.decode('utf-8'))
                task_result = {ID: task_id}
                if FIRST in r:
                    task_result[FIRST] = r[FIRST]
                if SECOND in r:
                    task_result[SECOND] = r[SECOND]
                self.lock.acquire()
                try:
                    del self.pending_tasks[props.correlation_id]
                    self.num_processed_tasks += 1
                finally:
                    self.lock.release()
                self.response.append(task_result)

    @staticmethod
    def __task_from(task_spec):
        task = {TYPE: task_spec[TYPE]}
        if task_spec[TYPE] in [MATE, MUTATE]:
            task[GEN] = task_spec[GEN]
            task[FIRST] = task_spec[FIRST]
        if task_spec[TYPE] == MATE:
            task[SECOND] = task_spec[SECOND]
        return task

    def __call__(self, tasks_specs):
        for task_spec in tasks_specs:
            corr_id = str(uuid.uuid4())
            task = self.__task_from(task_spec)
            self.channel.basic_publish(exchange='',
                                       routing_key=TASK_QUEUE,
                                       properties=pika.BasicProperties(
                                           reply_to=self.callback_queue,
                                           correlation_id=corr_id,
                                           delivery_mode=2
                                       ),
                                       body=json.dumps(task))
            if task_spec[TYPE] != TERMINATE:
                self.pending_tasks[corr_id] = task_spec[ID]
        if self.show_feedback:
            self.feedback_thread.start()
        while len(self.pending_tasks) != 0:
            self.connection.process_data_events()
        if self.show_feedback:
            self.feedback_thread.join()
        self.connection.close()
        return self.response


def publish_tasks(tasks, broker_url):
    publisher = _TaskPublisher(broker_url)
    return publisher(tasks)


def send_term_signals(broker_url, retries=1):

    def send_term_signal():
        connection = pika.BlockingConnection(pika.URLParameters(broker_url))
        channel = connection.channel()
        declare_topology(channel)
        try:
            channel.basic_publish(exchange=TERM_SIG_EXCHANGE,
                                  routing_key='',
                                  body=TERMINATE)
        finally:
            connection.close()

    for i in range(min(retries, 16)):
        Log.info('Sending termination signal (n=%d)...' % i)
        send_term_signal()
        time_to_sleep = 2 ** i
        Log.info('Sleeping for %d seconds' % time_to_sleep)
        time.sleep(time_to_sleep)


