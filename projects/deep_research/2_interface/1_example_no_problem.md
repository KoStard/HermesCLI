# Deep Research Interface

## Introduction

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Please check this section if your commands don't seem to be working as expected.

To begin, you need to define the problem you'll be researching. Please follow these standards and best practices:
- Make the problem statement clear and specific
- Include any constraints or requirements
- Consider what a successful outcome would look like
- Don't expand from the scope of the provided instructions from the user. The smaller the scope of the problem the faster the user will receive the answer.
- Include expectations on the depth of the results. On average be frugal, not making the problems scope explode.

Note: This is a temporary state. After defining the problem, this chat will be discarded and you'll start working on the problem with a fresh interface.

Any attachments provided will be copied to the root problem after creation and won't be lost.

Any context provided to you in the context section will be permanent and accessible in the future while working on the problem, so you can refer to it if needed.

Please note that only one problem definition is allowed. Problem definition is the only action you should take at this point and finish the response message.

Make sure to include closing tags for command blocks, otherwise it will break the parsing and cause syntax errors.

======================
# Attachments

<attachments>
<attachment name="quantum_mechanics_intro.pdf">
Content would be displayed here...
</attachment>
<attachment name="https://en.wikipedia.org/wiki/Quantum_mechanics">
Content would be displayed here...
</attachment>
</attachments>

======================
# Context
<contextAttachments>
<contextAttachment>
...
</contextAttachment>
...
</contextAttachments>

======================
# Instruction
Please research and organize the fundamental concepts of quantum mechanics. I need a comprehensive understanding of the core principles that form the foundation of this field.

======================
# How to define a problem
Define the problem using this command:
```
<<< define_problem
///title
title goes here
///content
Content of the problem definition.
>>>
```