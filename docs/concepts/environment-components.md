# Environment Components

SuperOpt optimizes four main parts of an AI agent's environment:

## Prompts

Instructions and rules that tell the agent how to behave:

```python
prompts = PromptConfig(
    system_prompt="You are a helpful coding assistant.",
    instruction_policy="Always check your work before finishing.",
    few_shot_exemplars=["Example task and solution"],
    behavioral_constraints=["Never delete files without asking"]
)
```

## Tools

Functions and commands the agent can use:

```python
tools = {
    "edit_file": ToolSchema(
        name="edit_file",
        description="Edit a file at a specific line",
        arguments={"file": "str", "line": "int", "content": "str"},
        required_fields=["file", "line", "content"]
    )
}
```

## Retrieval

How the agent finds and uses information:

```python
retrieval = RetrievalConfig(
    top_k=5,           # How many results to get
    chunk_size=512,    # How to break up text
    mode="semantic"    # How to search
)
```

## Memory

What the agent remembers and learns:

```python
memory = [
    MemoryEntry(
        entry_type="TOOL_RULE",
        content="Always use 1-indexed line numbers",
        confidence=0.9
    )
]
```

These components work together to make agents smarter over time.