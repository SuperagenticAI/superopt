# 🧩 SuperOpt Components

SuperOpt's optimization engine consists of five specialized components that work together to provide comprehensive environment optimization.

## 🎯 Component Overview

Each component targets a specific aspect of the agent environment, working together to create autonomous, self-improving AI agents.

<div class="components-overview-grid">
  <div class="component-overview-card">
    <div class="component-overview-header">
      <div class="component-overview-icon">🎯</div>
      <h3>SuperController</h3>
    </div>
    <div class="component-overview-content">
      <p><strong>Role:</strong> Diagnostic meta-controller</p>
      <p><strong>Function:</strong> Analyzes execution traces and routes failures to appropriate optimizers</p>
      <p><strong>Target:</strong> Failure classification and routing</p>
      <div class="component-overview-features">
        <span class="feature-tag">Rule-based diagnosis</span>
        <span class="feature-tag">LLM-enhanced analysis</span>
        <span class="feature-tag">Failure statistics</span>
      </div>
    </div>
    <a href="supercontroller/" class="component-overview-link">Learn More →</a>
  </div>

  <div class="component-overview-card">
    <div class="component-overview-header">
      <div class="component-overview-icon">📝</div>
      <h3>SuperPrompt</h3>
    </div>
    <div class="component-overview-content">
      <p><strong>Role:</strong> Evolutionary prompt optimizer</p>
      <p><strong>Function:</strong> Improves system prompts using evolutionary algorithms</p>
      <p><strong>Target:</strong> Instructions, examples, and behavioral constraints</p>
      <div class="component-overview-features">
        <span class="feature-tag">Evolutionary search</span>
        <span class="feature-tag">Pareto optimization</span>
        <span class="feature-tag">GEPA-inspired</span>
      </div>
    </div>
    <a href="superprompt/" class="component-overview-link">Learn More →</a>
  </div>

  <div class="component-overview-card">
    <div class="component-overview-header">
      <div class="component-overview-icon">🔧</div>
      <h3>SuperReflexion</h3>
    </div>
    <div class="component-overview-content">
      <p><strong>Role:</strong> Tool schema repair engine</p>
      <p><strong>Function:</strong> Fixes tool definitions when agents misuse tools</p>
      <p><strong>Target:</strong> Tool schemas, constraints, and documentation</p>
      <div class="component-overview-features">
        <span class="feature-tag">Schema clarification</span>
        <span class="feature-tag">Constraint addition</span>
        <span class="feature-tag">Example generation</span>
      </div>
    </div>
    <a href="superreflexion/" class="component-overview-link">Learn More →</a>
  </div>

  <div class="component-overview-card">
    <div class="component-overview-header">
      <div class="component-overview-icon">🔍</div>
      <h3>SuperRAG</h3>
    </div>
    <div class="component-overview-content">
      <p><strong>Role:</strong> Retrieval optimization engine</p>
      <p><strong>Function:</strong> Tunes retrieval parameters for better information access</p>
      <p><strong>Target:</strong> Search algorithms, chunking, and ranking</p>
      <div class="component-overview-features">
        <span class="feature-tag">Parameter tuning</span>
        <span class="feature-tag">Query optimization</span>
        <span class="feature-tag">Adaptive strategies</span>
      </div>
    </div>
    <a href="superrag/" class="component-overview-link">Learn More →</a>
  </div>

  <div class="component-overview-card">
    <div class="component-overview-header">
      <div class="component-overview-icon">🧠</div>
      <h3>SuperMem</h3>
    </div>
    <div class="component-overview-content">
      <p><strong>Role:</strong> Memory management system</p>
      <p><strong>Function:</strong> Manages learned patterns with decay and conflict resolution</p>
      <p><strong>Target:</strong> Knowledge persistence, freshness, and consistency</p>
      <div class="component-overview-features">
        <span class="feature-tag">Exponential decay</span>
        <span class="feature-tag">Conflict resolution</span>
        <span class="feature-tag">Confidence tracking</span>
      </div>
    </div>
    <a href="supermem/" class="component-overview-link">Learn More →</a>
  </div>
</div>

## 🔄 Component Interactions

```mermaid
graph TD
    SC[SuperController] --> SP[SuperPrompt]
    SC --> SR[SuperReflexion]
    SC --> SAG[SuperRAG]
    SC --> SM[SuperMem]

    SP --> ENV[Environment Update]
    SR --> ENV
    SAG --> ENV
    SM --> ENV

    ENV --> SC

    style SC fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    style ENV fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
```

## 🎯 Component Responsibilities

| Component | Failure Type | Environment Target | Optimization Method |
|-----------|-------------|-------------------|-------------------|
| **SuperController** | All Types | - | Diagnosis & Routing |
| **SuperPrompt** | PROMPT | Prompts & Instructions | Evolutionary Search |
| **SuperReflexion** | TOOL | Tool Schemas | Schema Repair |
| **SuperRAG** | RETRIEVAL | Search & Ranking | Parameter Tuning |
| **SuperMem** | MEMORY | Knowledge Base | Decay & Resolution |

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "SuperOpt Framework"
        subgraph "Outer Loop"
            SC[SuperController]
            subgraph "Specialized Optimizers"
                SP[SuperPrompt]
                SR[SuperReflexion]
                SAG[SuperRAG]
                SM[SuperMem]
            end
        end

        subgraph "Agent Environment Φ"
            P[Prompts]
            T[Tools]
            R[Retrieval]
            M[Memory]
        end
    end

    subgraph "Agent Execution"
        AE[Agent] --> TE[Task Execution]
        TE --> TR[Trace Generation]
    end

    TR --> SC
    SC --> SP
    SC --> SR
    SC --> SAG
    SC --> SM

    SP --> P
    SR --> T
    SAG --> R
    SM --> M

    P --> AE
    T --> AE
    R --> AE
    M --> AE

    style SC fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    style AE fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
```

## 📊 Component Workflow

1. **Failure Detection**: SuperController analyzes execution traces
2. **Routing Decision**: Routes failure to appropriate optimizer
3. **Optimization**: Specialized component improves its environment aspect
4. **Environment Update**: Changes are applied to agent environment
5. **Continuous Learning**: Agent becomes better over time

<style>
.components-overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.component-overview-card {
  background: var(--md-default-fg-color--lightest);
  border: 1px solid var(--md-default-fg-color--lighter);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

[data-md-color-scheme="slate"] .component-overview-card {
  background: #1e1e1e;
  border-color: #333;
}

.component-overview-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #f093fb, #ff6b6b);
}

.component-overview-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

[data-md-color-scheme="slate"] .component-overview-card:hover {
  box-shadow: 0 20px 40px rgba(0,0,0,0.5);
}

[data-md-color-scheme="slate"] .component-overview-header h3 {
  color: #ffffff;
}

[data-md-color-scheme="slate"] .component-overview-content p {
  color: #e0e0e0;
}

[data-md-color-scheme="slate"] .component-overview-content strong {
  color: #ffffff;
}

.component-overview-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.component-overview-icon {
  font-size: 2.5rem;
  opacity: 0.8;
}

.component-overview-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: var(--md-primary-fg-color);
}

.component-overview-content p {
  font-size: 0.9rem;
  color: var(--md-default-fg-color--light);
  margin: 0.5rem 0;
  line-height: 1.5;
}

.component-overview-features {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 1rem 0;
}

.feature-tag {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

[data-md-color-scheme="slate"] .feature-tag {
  background: rgba(102, 126, 234, 0.2);
  color: #90caf9;
  border-color: rgba(102, 126, 234, 0.4);
}

.component-overview-link {
  display: inline-block;
  margin-top: 1rem;
  color: var(--md-primary-fg-color);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: color 0.2s ease;
}

.component-overview-link:hover {
  color: var(--md-accent-fg-color);
}

@media (max-width: 768px) {
  .components-overview-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .component-overview-card {
    padding: 1.5rem;
  }

  .component-overview-header {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }
}
</style>
