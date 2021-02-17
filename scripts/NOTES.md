# Notes for Development

## Threading

- always join the thread. Setting no timeout means the calling thread's execution will block until the thread is terminated (https://docs.python.org/3/library/threading.html)