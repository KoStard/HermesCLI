from typing import List, Optional
from collections import namedtuple

HermesConfig = namedtuple('HermesConfig', [
    'model',
    'prompt',
    'prompt_file',
    'append',
    'update',
    'pretty',
    'workflow',
    'files',
    'text',
    'url',
    'image'
], defaults=(None,) * 11)

def create_config_from_args(args):
    return HermesConfig(
        model=args.model,
        prompt=args.prompt,
        prompt_file=args.prompt_file,
        append=args.append,
        update=args.update,
        pretty=args.pretty,
        workflow=args.workflow,
        files=args.files if hasattr(args, 'files') else None,
        text=args.text if hasattr(args, 'text') else None,
        url=args.url if hasattr(args, 'url') else None,
        image=args.image if hasattr(args, 'image') else None
    )
