"""Feature builders, one module per data source.

Planned: ``purchases``, ``calls``, ``sms``, ``app_usage`` and ``device``. Each
takes the events returned by :func:`creditscoring.pit.events_in_window` and
returns one row per ``loan_id``. They get written once the real data schema is
known; the feature ideas are listed in the README.
"""
