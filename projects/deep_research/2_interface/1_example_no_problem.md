> Imagine user requests the assistant to work on figuring out what are the fundamental concepts of quantum mechanics. There is no problem defined yet. What interface will the assistant see to create the problem. The user might have included some attachments as well.

Answer goes below the line:

---

# Deep Research Interface

Welcome to the Deep Research Interface. This interface is designed to help you conduct thorough investigations into complex topics.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

To begin, you need to define the problem you'll be researching. Please follow these standards and best practices:
- Make the problem statement clear and specific
- Include any constraints or requirements
- Consider what a successful outcome would look like

Note: This is a temporary state. After defining the problem, this chat will be discarded and you'll start working on the problem with a fresh interface.

Any attachments the user has provided will be copied to the root problem after creation and won't be lost.

Please note that only one problem definition is allowed. Problem definition is the only action you should take at this point and finish the response message.

Make sure to include closing tags for multiline blocks, otherwise it will break the parsing and cause syntax errors.

======================
# Attachments

<attachments>
<attachment name="quantum_mechanics_intro.pdf">
Introduction to Quantum Mechanics
By Richard Feynman

This document provides an overview of the fundamental principles of quantum mechanics, including wave-particle duality, uncertainty principle, and quantum states.

[Content continues for several pages...]
</attachment>

<attachment name="https://en.wikipedia.org/wiki/Quantum_mechanics">
Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science.

Classical physics, the collection of theories that existed before the advent of quantum mechanics, describes many aspects of nature at an ordinary (macroscopic) scale, but is not sufficient for describing them at small (atomic and subatomic) scales. Most theories in classical physics can be derived from quantum mechanics as an approximation valid at large (macroscopic) scale.

[Content continues with major principles, mathematical formulations, and applications...]
</attachment>
</attachments>

======================
# Instruction
Please research and organize the fundamental concepts of quantum mechanics. I need a comprehensive understanding of the core principles that form the foundation of this field.

======================
# How to define a problem
Define the problem using this command:
```
<<<<< define_problem
///title
title goes here
///content
Content of the problem definition.
>>>>>
```

======================
# How to define a problem
Define the problem using this command:
```
<<<<< define_problem
///title
title goes here
///content
Content of the problem definition.
>>>>>
```
