# 🔧 SuperReflexion

SuperReflexion is the self-healing tool schema repair engine in SuperOpt. It fixes tool definitions when agents misuse or misunderstand tools, rather than just telling the agent what went wrong.

## 🎯 Core Function

SuperReflexion addresses tool-related failures by repairing the environment:

- Tool schemas are ambiguous or incomplete
- Required parameters aren't clearly specified
- Error conditions aren't documented
- Examples don't cover edge cases

Instead of scolding the agent through prompts, SuperReflexion fixes the root cause by improving tool definitions.

## 🔍 Tool Failure Analysis

### Common Tool Problems
- **Ambiguous Descriptions**: Tool purpose isn't clear
- **Missing Parameters**: Required fields aren't specified
- **Type Confusion**: Parameter types aren't documented
- **Error Handling**: Exception cases aren't covered
- **Example Gaps**: Edge cases aren't demonstrated

### Failure Detection
SuperReflexion analyzes execution traces for:
- Invalid argument errors
- Schema violation exceptions
- Runtime tool failures
- Parameter validation errors

## 🛠️ Schema Repair Process

### Step 1: Error Extraction
```python
def patch_schema(self, schema: ToolSchema, trace: ExecutionTrace) -> ToolSchema:
    # Find tool-specific errors
    tool_errors = [error for error in trace.tool_errors
                  if error.tool_name == schema.name]
```

### Step 2: Clarification Generation
For each error, SuperReflexion generates:
- **Description Improvements**: Clearer explanations of tool purpose
- **Parameter Clarifications**: Detailed parameter requirements
- **Constraint Additions**: Explicit rules and limitations
- **Example Additions**: Usage examples for edge cases

### Step 3: Schema Updates
```python
# Append clarifications to description
schema.description += "\n\nClarification: " + clarification

# Add new constraints
schema.constraints.extend(new_constraints)

# Include usage examples
schema.examples.append(usage_example)
```

## 📋 Tool Schema Structure

SuperReflexion works with comprehensive tool schemas:

```python
@dataclass
class ToolSchema:
    name: str                           # Tool identifier
    description: str                    # Tool purpose and usage
    arguments: dict[str, Any]           # Parameter definitions
    required_fields: list[str]          # Mandatory parameters
    constraints: list[str]              # Usage rules and limitations
    examples: list[dict[str, Any]]      # Usage examples
```

## 🎨 Types of Schema Patches

### Description Enhancements
- **Purpose Clarification**: Make tool purpose unambiguous
- **Scope Definition**: Specify what the tool can/cannot do
- **Context Addition**: Explain when to use the tool

### Parameter Documentation
- **Type Specifications**: Clear data types for each parameter
- **Format Requirements**: Expected formats and patterns
- **Validation Rules**: Acceptable value ranges

### Constraint Addition
- **Preconditions**: Requirements before tool can be used
- **Postconditions**: Expected outcomes
- **Error Conditions**: When the tool might fail

### Example Provision
- **Success Cases**: Normal usage examples
- **Edge Cases**: Unusual but valid usage
- **Error Examples**: What not to do

## 🔄 Integration with SuperOpt

### Trigger Conditions
SuperReflexion activates for:
- `FailureType.TOOL` diagnoses from SuperController
- Tool call validation errors
- Schema violation exceptions
- Parameter mismatch errors

### Patch Generation
```python
# SuperReflexion receives tool failures
def optimize(self, trace: ExecutionTrace, environment: AgenticEnvironment):
    # Identify problematic tools
    # Generate schema patches
    # Apply clarifications and constraints
    # Return updated tool schemas
```

### Environment Updates
Updates are applied to the tool environment:
```python
# Original tool schema
tool = ToolSchema(
    name="edit_file",
    description="Edit a file",
    arguments={"file": "str", "line": "int"}
)

# After SuperReflexion patch
tool.description += "\nNote: Line numbers must be 1-indexed, not 0-indexed"
tool.constraints.append("Line numbers start from 1, not 0")
```

## ⚙️ Configuration Options

### Basic Configuration
```python
superreflexion = SuperReflexion(
    llm_client=my_llm_client  # Optional, for advanced patch generation
)
```

### Advanced Configuration
```python
superreflexion = SuperReflexion(
    llm_client=my_llm_client,
    max_patches_per_tool=3,    # Limit patches per optimization cycle
    patch_confidence_threshold=0.7,  # Minimum confidence for patches
    enable_example_generation=True   # Generate usage examples
)
```

## 📊 Patch Quality Assurance

### Confidence Scoring
- **Error Specificity**: How directly patch addresses the error
- **Completeness**: How comprehensive the clarification is
- **Non-Redundancy**: Avoiding duplicate constraints

### Validation Checks
- **Schema Consistency**: Patches don't conflict with existing schema
- **Backward Compatibility**: Existing valid usage still works
- **Clarity Improvement**: Patches actually make schema clearer

## 🔬 Research Foundation

SuperReflexion implements **environment-level repair** rather than agent-level correction:

- **Root Cause Fixing**: Addresses why tools are misused
- **Preventive Maintenance**: Stops future occurrences of same errors
- **Scalable Improvement**: Benefits all agents using the tool

Unlike prompt-based approaches that tell agents what to do, SuperReflexion modifies the tool definitions themselves, creating lasting improvements that work for any agent.

## 📈 Effectiveness Metrics

### Success Indicators
- **Error Reduction**: Fewer tool-related failures over time
- **Usage Clarity**: Agents make fewer invalid tool calls
- **Schema Completeness**: Tool definitions become more comprehensive

### Quality Measures
- **Patch Relevance**: How well patches address actual errors
- **Schema Improvement**: Increased clarity and completeness
- **Maintenance Overhead**: Effort required to apply patches

SuperReflexion provides the intelligent tool repair that makes SuperOpt's comprehensive optimization possible by fixing the environment rather than retraining agents.