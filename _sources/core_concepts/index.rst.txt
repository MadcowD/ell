Core Concepts in ell
====================

Welcome to the Core Concepts section of the ell documentation. This section covers the fundamental ideas and components that form the backbone of ell. Understanding these concepts is crucial for effectively using ell in your projects.

In this section:
----------------

1. :doc:`Language Model Programs (LMPs) <language_model_programs>`
   
   - What are Language Model Programs?
   - The philosophy behind treating prompts as programs

2. :doc:`Decorators <decorators>`
   
   - The @ell.simple decorator
   - The @ell.complex decorator
   - Choosing between simple and complex LMPs

3. :doc:`Messages and Content Blocks <messages_and_content_blocks>`
   
   - Understanding the Message system
   - Working with different types of ContentBlocks

4. :doc:`Tools <tools>`
   
   - Defining and using tools in ell
   - Integrating tools with Language Model Programs

.. 5. :doc:`Structured Outputs <structured_outputs>`
   
..    - Using Pydantic models for structured data
..    - Benefits of working with structured outputs in LLM interactions

By mastering these core concepts, you'll have a solid foundation for building sophisticated applications with ell. Each concept builds upon the others, so we recommend going through them in order.

Let's start by exploring Language Model Programs, the fundamental building blocks of ell!

.. toctree::
   :maxdepth: 1
   :caption: Core Concepts:
   
   language_model_programs
   decorators
   messages_and_content_blocks
   tools