========================
SQLAlchemy asyncio demo
========================

This is an attempt to demonstrate how SQLAlchemy uses asyncio and greenlet together
to context switch between asyncio and blocking-IO coding paradigms.

It's basically a tiny SQLAlchemy program hooked into a very custom harness
which tracks it with sys.settrace() and displays a curated set of function
calls in context within a two-column layout.

Directions:

1. checkout

    $ git clone https://github.com/zzzeek/async_demo.git

2. install in a venv

    $ cd async_demo
    $ virtualenv .venv
    $ .venv/bin/pip install .

3. run

    $ .venv/bin/python demo.py



