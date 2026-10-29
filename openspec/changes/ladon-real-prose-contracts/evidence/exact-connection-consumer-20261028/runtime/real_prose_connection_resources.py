"""Stop the whole connection when any bounded child exhausts its allowance."""

from ladon.resource_limits import memory_limit_message


def stop_on_limits(receipts,job):
    if any(row.get('memory_limited',row.get('memoryLimited',False)) for row in receipts):
        peak = max((row.get('peak_rss_bytes',row.get('peakRssBytes',0)) for row in receipts),default=0)
        raise ValueError(memory_limit_message(job['maxRssBytes'],peak))
    if any(row.get('timed_out',row.get('timedOut',False)) for row in receipts):
        raise TimeoutError('Stop progress and report back to user: the shared connection deadline was insufficient.')
    if any(row.get('output_limited',row.get('outputLimited',False)) for row in receipts):
        raise ValueError('Stop progress and report back to user: the connection output limit was insufficient.')
