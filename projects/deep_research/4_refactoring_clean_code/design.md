# Decisions and principles
- Decided to try to use clean and nice separate classes, and try to pack necessary API with it. For example, the research project has permanent logs. The permanent logs will provide the necessary API to add logs, and when you add them, it will automatically save into a file. This means it will have the necessayr context to be able to do that.
- The files should be updated automatically, without need for calling update files. Only the changed files should be updated. If the right fit, we should use append-write (e.g. permanent log)
- We should break as much as possible, keeping things intuitive, well named, with clear purposes, while aiming to have files with ~<100 lines, including the engine
