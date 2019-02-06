import pika
import json
import time
import functools
import os
import logging
from deap import base
from .fitness import TSPInstance, EvalTSPSolution, EvalTSPSolutionFragment
from .mutation import TwoOptMutate
from .crossover import edge_recombination
from .messaging import declare_topology, ack_message, TASK_QUEUE, MATE, MUTATE, FIRST, SECOND, TYPE, GEN, \
    TERM_SIG_EXCHANGE
from .population import individual_from
from .utils import async_func

Log = logging.getLogger(__name__)


def _connect(broker_url):
    connection = pika.BlockingConnection(pika.URLParameters(broker_url))
    channel = connection.channel()
    declare_topology(channel)
    term_sig_queue = channel.queue_declare(exclusive=True)
    channel.queue_bind(exchange=TERM_SIG_EXCHANGE, queue=term_sig_queue.method.queue)
    return connection, channel, term_sig_queue.method.queue


def _process_task(task, toolbox):
    if task[TYPE] == MATE:
        ind1, ind2 = task[FIRST], task[SECOND]
        off1, off2 = toolbox.mate(individual_from(ind1), individual_from(ind2))
        return {FIRST: list(off1), SECOND: list(off2)}
    elif task[TYPE] == MUTATE:
        ind = task[FIRST]
        off, = toolbox.mutate(individual_from(ind))
        return {FIRST: list(off)}
    else:
        Log.error('Invalid task type ' + task[TYPE])
        raise Exception('Invalid task type')


def _on_request_func(connection, toolbox):

    @async_func
    def on_request(ch, method, props, body):
        task = json.loads(body.decode('utf-8'))

        st = time.time()
        Log.info(" [.] Received '%s' task, generation: %d. Processing..." % (task[TYPE], task[GEN]))
        response = _process_task(task, toolbox)
        et = time.time()
        Log.info(" [...] Finished processing, elapsed time: %f. Publishing response" % (et - st))
        # publish the response
        publish_callback = functools.partial(ch.basic_publish,
                                             exchange='',
                                             routing_key=props.reply_to,
                                             properties=pika.BasicProperties(correlation_id=props.correlation_id,
                                                                             delivery_mode=1),
                                             body=json.dumps(response))
        if ch.is_open:
            connection.add_callback_threadsafe(publish_callback)
        # acknowledge original message
        ack_callback = functools.partial(ack_message, ch, method.delivery_tag)
        connection.add_callback_threadsafe(ack_callback)

    return on_request


def _on_term_signal_receive_func(connection):
    def on_term_signal_receive(ch, method, props, body):
        Log.info('Received termination signal. Finishing...')
        ch.stop_consuming()
        connection.close()

    return on_term_signal_receive


def _consume(broker_url, toolbox):
    Log.info(" [x] Connecting to RabbitMQ...")
    connection, channel, term_sig_queue = _connect(broker_url)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(_on_request_func(connection, toolbox), queue=TASK_QUEUE)
    channel.basic_consume(_on_term_signal_receive_func(connection), queue=term_sig_queue, no_ack=True)
    Log.info(" [x] Awaiting requests")
    channel.start_consuming()


LSEARCH_NBOUR_SIZE = int(os.getenv('LSEARCH_NBOUR_SIZE', 100))
RAND_SEARCH_PROB = float(os.getenv('RAND_SEARCH_PROB', 0.5))


def run(cities_file, broker_url):
    Log.info('Starting worker...')
    toolbox = base.Toolbox()
    tsp_instance = TSPInstance(cities_file)
    toolbox.register('evaluate', EvalTSPSolution(tsp_instance))
    toolbox.register('evaluate_fragment', EvalTSPSolutionFragment(tsp_instance))
    toolbox.register('mate', edge_recombination)
    toolbox.register('mutate', TwoOptMutate(tsp_instance.distance, toolbox.evaluate, toolbox.evaluate_fragment),
                     k=LSEARCH_NBOUR_SIZE, rmp=RAND_SEARCH_PROB)
    _consume(broker_url, toolbox)



