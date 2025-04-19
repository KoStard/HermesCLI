<%namespace name="xml" file="/macros/xml.mako"/>
${'#'} Deep Research Interface (Static Section)

${'##'} Introduction

${'###'} Interface Structure
The interface has two main parts:
1. **Static Section** - Basic instructions and commands that don't change
2. **Dynamic Sections** - Data that updates as you work on the problem

When you first join a problem, you'll receive all sections of the interface. After that, in each automatic reply, 
you'll only receive the sections that have changed since your last message. This keeps the interface efficient 
and focused on what's new or different. If a section isn't included in an automatic reply, it means that section 
hasn't changed.

${'###'} External Files

The system may contain external files provided by the user at the beginning of the research. These are shown in the artifacts section with special "External File" designation. These files contain important context for your work and are always fully visible. They are stored centrally and accessible from any problem in the hierarchy.
