# File system provides us with an abstraction of nodes, which should also save things to the file system
# But it currently also handles status management, which should move out of it
#
# Engine currently holds information about the current task, handles the execution directly.
# This blocks the future migration to parallelism.
#
# History currently handles the per-node separate history management.
# This could be simplified so that each task has a separate history.
#
# So the task is to resolve the current node. It can be revived if new information came.
# The task maybe should also have some relation with the file system to track its context.
#
# To support future parallel execution, first we should move to a proper task-based design
# The engine should have a reference to a task and a method "execute" of the task.
# Internally, the task will use the interface and other resources to make an LLM call for its node
# The assistant will use the necessary commands to create artifacts, add/update criteria, add subtasks,
# as well as to navigate.
#
# When navigating, it will either create new tasks or activate other ones.
# When a task finishes and wants to "focus_up", it should call a method in the parent task
# (which should exist) to mark this dependency as done. Then, if the parent task has no other dependencies,
# it will get parked as pending. Then the engine will activate it.
#
# How will the engine "activate" tasks?
# If we want to have parallelism, we should have "threads" as well, where we assign a given task to
# the available thread. We then could have messages queue from the tasks to the engine asking it to check the status
# again. Then the engine thread should block-read from the queue with timeout to check what's happening,
# if something has failed, if there are threads free to pick up new tasks, or if the overall task is finished.
