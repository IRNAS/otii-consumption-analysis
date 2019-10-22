# Otii automatic testing

The Otti server enables us to write automatic tests for energy consumption.
We meassure energy consumption between 2 messagess sent from the device via UART.

For testing a device, a `json` document must be specified as follows:

```json
{
    "hostname": "IP",
    "port": <PORT>,
    "arc_name": "Arc-name",
    "record_duration": <DURATION>,
    "message_pairs": [
        {
            "from": "message begin",
            "to": "message end",
            "avg_limit_low": <LIMIT LOW>,
            "avg_limit_high": <LIMIT HIGH>,
            "timeout": <TIMEOUT>
        },
        ...
    ]
}
```

- `"hostname"` is the IP of the Otti test client
- `"port"` is the PORT of the Otti test client
- `"arc_name"` is the name of the Arc (check in Otii -> Project -> Project Settings -> Arc -> INFO)
- `"message_pairs"` is an array of objects specifying each segment we want to measure:
  - `"from"` is the message where measuring begins
  - `"to"` is the message where measuring ends
  - `"avg_limit_low"` is the lowest amount of energy (in μWh) that can be used up in the specified duration (on average).
  - `"avg_limit_high"` is the highest amount of energy (in μWh) that can be used up in the specified duration (on average).
  - `"timeout"` is the highest amount of time (in ms) allowed between messages. If timeout is `0`, the limit is infinite.

Example json:

```json
{
    "hostname": "127.0.0.1",
    "port": 1905,
    "arc_name": "Arc",
    "record_duration": 20,
    "message_pairs": [
        {
            "from": "fsm(0, 1, 2)",
            "to": "fsm(1, 3, 7)",
            "avg_limit_low": 10,
            "avg_limit_high": 10.6,
            "timeout": 2000
        },
        {
            "from": "> PING",
            "to": "> PING 2",
            "avg_limit_low": 19.6,
            "avg_limit_high": 19.8,
            "timeout": 1770
        }
    ]
}
```

To run the tests, simply run:

```bash
./test_otii.py -f <JSON FILENAME>
```
