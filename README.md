# aioweenect

Asynchronous Python client for the weenect API

[![GitHub Actions](https://github.com/eifinger/aioweenect/workflows/CI/badge.svg)](https://github.com/eifinger/aioweenect/actions?workflow=CI)
[![PyPi](https://img.shields.io/pypi/v/aioweenect.svg)](https://pypi.python.org/pypi/aioweenect)
[![PyPi](https://img.shields.io/pypi/l/aioweenect.svg)](https://github.com/eifinger/aioweenect/blob/master/LICENSE)
[![codecov](https://codecov.io/gh/eifinger/aioweenect/branch/master/graph/badge.svg)](https://codecov.io/gh/eifinger/aioweenect)
[![Downloads](https://pepy.tech/badge/aioweenect)](https://pepy.tech/project/aioweenect)

## Installation

```bash
$ pip install aioweenect
```

## Usage

```python
from aioweenect import AioWeenect

import asyncio

USER = "<YOUR_USER>"
PASSWORD = "<YOUR_PASSWORD>"


async def main():
    """Show example how to get location of your tracker."""
    async with AioWeenect(username=USER, password=PASSWORD) as aioweenect:
        trackers_response = await aioweenect.get_trackers()
        tracker_id = trackers_response["items"][0]["id"]
        tracker_name = trackers_response["items"][0]["name"]

        position_response = await aioweenect.get_position(tracker_id=tracker_id)
        lat = position_response[0]["latitude"]
        lon = position_response[0]["longitude"]
        last_message = position_response[0]["last_message"]
        print(f"Location for {tracker_name}: lat: {lat}, lon: {lon}. Last message received: {last_message}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```
