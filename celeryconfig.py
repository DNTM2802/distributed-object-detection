BROKER_URL = 'pyamqp://guest@localhost//'
CELERY_RESULT_BACKEND = 'rpc://'
CELERYD_PREFETCH_MULTIPLIER = 1     # How many messages to prefetch (reserve) at a time per worker. Default: 4
CELERYD_CONCURRENCY = 1             # The number of concurrent worker processes/threads/green threads executing tasks. Default: Number of CPU cores.
CELERYD_MAX_TASKS_PER_CHILD = 1     # Maximum number of tasks a pool worker process can execute before it’s replaced with a new one. Default is no limit.