from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class HermesConfig:
    model: Optional[str] = None
    prompt: Optional[str] = None
    prompt_file: Optional[str] = None
    append: Optional[str] = None
    update: Optional[str] = None
    pretty: bool = False
    workflow: Optional[str] = None
    files: List[str] = field(default_factory=list)
    text: List[str] = field(default_factory=list)
    url: List[str] = field(default_factory=list)
    image: List[str] = field(default_factory=list)

def create_config_from_args(args):
    return HermesConfig(
        model=args.model,
        prompt=args.prompt,
        prompt_file=args.prompt_file,
        append=args.append,
        update=args.update,
        pretty=args.pretty,
        workflow=args.workflow,
        files=args.files if hasattr(args, 'files') else [],
        text=args.text if hasattr(args, 'text') else [],
        url=args.url if hasattr(args, 'url') else [],
        image=args.image if hasattr(args, 'image') else []
    )
