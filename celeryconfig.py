BROKER_URL = 'pyamqp://guest@localhost//'   # RabbitMQ URL
CELERY_RESULT_BACKEND = 'rpc://'            # Backend is needed to save states of tasks and prevent failures. Backend is also RabbitMQ based.
CELERYD_PREFETCH_MULTIPLIER = 1             # How many messages to prefetch (reserve) at a time per worker. Default: 4
CELERYD_CONCURRENCY = 1                     # The number of concurrent worker processes/threads executing tasks. Default: Number of CPU cores.
CELERYD_MAX_TASKS_PER_CHILD = 1             # Maximum number of tasks a pool worker process can execute before it’s replaced with a new one. Default is no limit.
CELERY_ACKS_LATE = True                     # The acks_late setting would be used when you need the task to be executed again if the worker (for some reason) crashes mid-execution.