rm output.md
cp input.md_original output.md
hermes --prefill notebook --append output.md --once
