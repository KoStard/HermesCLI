# Deep Research

Currently Hermes supports regular chat interface, where both the user and the assistant are treated similarly, given set of tools and history.
But I want to design a new interface for the assistant when doing deep research.
The idea is this: With regular chat, the length of the history is constantly increasing. This is fine for regular interactions, but when investigating a topic deeply, this doesn't scale. An ambiguous and complicated problem frequently has subproblems. A person reads lots of materials, does some drafting to summarize his current understanding and more. Then after finding the answer to that subproblem, moves to the next one. While doing so, he doesn't keep all the resources that he checked previously. He just keeps the summary of what he found from the previous subproblems, allowing him to more effectively focus on the current subproblem. Especially that big investigations could take days. With this change, we'll add this way of working in Hermes. Constantly break down the problem to subproblems until it becomes manageable in one go. Break down further when finding more information that deserves investiation. Summarise the answers of each subproblem and keep in the context only that and the breakdown structure itself, without keeping in context the detailed steps one takes to reach there.
To make this experience useful for the user, we'll use the file system for this investigation.
We'll have a root directory where all the research happens.
Inside it we'll have folder for subproblems, for the documents found as part of the research, a file for the (sub)problem definition, breakdown structure and when done, report for the overall findings.
Let's imagine this as a tree structure. The main problem and the subproblems are nodes.

Node:
- problem definition
- criteria for definition of done (can be appended if more information is found, each criterion has a status: done or not done)
- subproblems Node[] (each subproblem has its own criteria for definition of done)
- report 3-pager (summarizes all the findings, includes all the important details for the parent subproblem)
- attachments
