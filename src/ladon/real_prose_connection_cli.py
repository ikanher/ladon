"""Opt-in connection, explicitly historical reporting, and exact-input replay."""

from pathlib import Path

from ladon.proof_contract_io import load_bounded_plans
from ladon.resource_limits import DEFAULT_MAX_RSS_MIB

OPERATIONS = ('connect-real-prose-bound','report-real-prose-connection','replay-real-prose-connection')


def add_parsers(sub):
    for name in OPERATIONS:
        parser = sub.add_parser(name,help='Check or inspect an exact conditional Real prose connection')
        parser.add_argument('--output',type=Path)
        if name != 'connect-real-prose-bound':
            parser.add_argument('--input',type=Path,required=True)
        if name == 'report-real-prose-connection':
            continue
        parser.add_argument('--formal',type=Path,required=True)
        parser.add_argument('--authored',type=Path,required=True)
        parser.add_argument('--formal-root',type=Path,required=True)
        parser.add_argument('--prose-root',type=Path,required=True)
        parser.add_argument('--timeout-seconds',type=float,default=600)
        parser.add_argument('--max-rss-mib',type=int,default=DEFAULT_MAX_RSS_MIB)
        if name == 'connect-real-prose-bound':
            parser.add_argument('--request',type=Path,required=True)


def command(args):
    from ladon.real_prose_connection import (
        connect_real_prose_bound,
        inspect_real_prose_connection,
        replay_real_prose_connection,
    )

    if args.operation == 'report-real-prose-connection':
        snapshot, = load_bounded_plans([args.input],max_bytes=32*1024**2)
        return inspect_real_prose_connection(snapshot)
    last = args.request if args.operation == 'connect-real-prose-bound' else args.input
    formal,authored,value = load_bounded_plans([args.formal,args.authored,last],max_bytes=32*1024**2)
    limits = {'timeout_seconds':args.timeout_seconds,'max_rss_bytes':args.max_rss_mib*1024**2}
    if args.operation == 'connect-real-prose-bound':
        return connect_real_prose_bound(formal,authored,args.formal_root,args.prose_root,value,**limits)
    return replay_real_prose_connection(value,formal,authored,args.formal_root,args.prose_root,**limits)
