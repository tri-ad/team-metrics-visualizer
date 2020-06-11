FAQs
====

1. I have encountered the error `FATAL:  password authentication failed for user "postgres"`

   Environmental variable in Docker are loaded when containers are built (with `docker-compose up -d`). If you added or changed variables in `.env` after the containers were built, then you need to recreate the containers (with `./run_docker-compose.sh`) to load the updated values. You won't lose data unless you explicitly delete the `tmv_db` volume.

2. I have encountered the error `billiard.exceptions.WorkerLostError: Worker exited prematurely: signal 6 (SIGABRT)` while trying to run Celery

   You need to set the following environment variable in your `.bash_profile`: `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`. For more info, check this [stackoverflow answer](https://stackoverflow.com/questions/52671926/rails-may-have-been-in-progress-in-another-thread-when-fork-was-called).

