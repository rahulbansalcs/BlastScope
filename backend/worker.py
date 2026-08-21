import os
from rq import SimpleWorker,Worker
from app.queue.connection import get_redis_connection
def main():
    connection=get_redis_connection()
    worker_class=Worker if os.getenv("ENVIRONMENT")=="production" else SimpleWorker
    worker=worker_class(["analysis"],connection=connection)
    worker.work()
if __name__=="__main__":
    main()