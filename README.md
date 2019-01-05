# micropython-aiosentry

Here is a class for sending an exception with stacktrace from 
your micropython instance to Sentry.

```
    client = SentryClient(SENTRY_ID, SENTRY_KEY)

    try:
        x = 1/0
    except Exception as e:
        await client.send_exception(e)
        raise
```
