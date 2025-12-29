# 🤝 Related Work & Acknowledgments

SuperOpt builds on and extends foundational work in agent optimization. We acknowledge the inspiration and methodologies from related approaches while highlighting how SuperOpt provides a more comprehensive framework.

## 📚 Key Research Papers

<div class="papers-grid">
  <div class="paper-card">
    <div class="paper-header">
      <div class="paper-icon">🧬</div>
      <h3>GEPA</h3>
      <span class="paper-year">2025</span>
    </div>
    <div class="paper-content">
      <p class="paper-subtitle">Generative Evolutionary Prompt Optimization</p>
      <p class="paper-description">Evolutionary algorithms for prompt optimization that can outperform reinforcement learning with fewer rollouts.</p>
      <div class="paper-authors">Agrawal et al.</div>
      <div class="paper-links">
        <a href="https://arxiv.org/abs/2507.19457" class="paper-link secondary" target="_blank">🔗 arXiv</a>
      </div>
    </div>
  </div>

  <div class="paper-card">
    <div class="paper-header">
      <div class="paper-icon">🧠</div>
      <h3>ACE</h3>
      <span class="paper-year">2025</span>
    </div>
    <div class="paper-content">
      <p class="paper-subtitle">Agentic Context Engineering</p>
      <p class="paper-description">Evolving contexts for self-improving language models through structured accumulation and refinement.</p>
      <div class="paper-authors">Zhang et al.</div>
      <div class="paper-links">
        <a href="https://arxiv.org/abs/2510.04618" class="paper-link secondary" target="_blank">🔗 arXiv</a>
      </div>
    </div>
  </div>

  <div class="paper-card">
    <div class="paper-header">
      <div class="paper-icon">🔧</div>
      <h3>DSPy</h3>
      <span class="paper-year">2023</span>
    </div>
    <div class="paper-content">
      <p class="paper-subtitle">Compiling Declarative Language Model Calls</p>
      <p class="paper-description">Framework for compiling declarative language model calls into self-improving pipelines.</p>
      <div class="paper-authors">Khattab et al.</div>
      <div class="paper-links">
        <a href="https://arxiv.org/abs/2310.03714" class="paper-link secondary" target="_blank">🔗 arXiv</a>
      </div>
    </div>
  </div>
</div>

## 🎯 Building on Established Foundations

### GEPA Integration
SuperOpt incorporates **GEPA's evolutionary prompt optimization** techniques within the SuperPrompt component. We appreciate the foundational work by GEPA that demonstrated how evolutionary algorithms can effectively optimize prompt configurations for better task performance.

```python
# SuperOpt can use GEPA-style optimization for prompts
from superopt import SuperOpt
from superopt.components.superprompt import SuperPrompt

# Configure SuperPrompt with GEPA-inspired parameters
superprompt = SuperPrompt(
    population_size=20,      # GEPA-style population approach
    mutation_rate=0.3,       # Evolutionary parameters
    use_pareto_selection=True
)

optimizer = SuperOpt(
    environment=environment,
    superprompt=superprompt   # Uses GEPA methodology
)
```

### ACE Integration
The SuperMem component draws inspiration from **ACE's context accumulation** approaches, extending them with typed memory hierarchies, exponential decay, and conflict resolution.

```python
# SuperOpt extends ACE with additional memory features
from superopt import SuperOpt
from superopt.components.supermem import SuperMem

# Enhanced memory with ACE-inspired accumulation + more
supermem = SuperMem(
    min_confidence=0.1,
    type_hierarchy_enabled=True,  # Beyond basic ACE
    conflict_resolution=True,     # Additional SuperOpt features
    exponential_decay=True
)

optimizer = SuperOpt(
    environment=environment,
    supermem=supermem
)
```

## 🔄 Complementary Approaches

Rather than competing with these approaches, **SuperOpt is designed to work alongside and extend them**:

<div class="integration-showcase">
  <div class="integration-item">
    <h4>🔄 GEPA + SuperOpt</h4>
    <p>GEPA's evolutionary prompt optimization within SuperOpt's comprehensive framework</p>
    <div class="integration-code">
```python
optimizer = SuperOpt(
    superprompt=SuperPrompt(use_gepa_methodology=True),
    # Plus SuperReflexion, SuperRAG, SuperMem
)
```
    </div>
  </div>

  <div class="integration-item">
    <h4>🔄 ACE + SuperOpt</h4>
    <p>ACE's context engineering enhanced with SuperOpt's memory management</p>
    <div class="integration-code">
```python
optimizer = SuperOpt(
    supermem=SuperMem(use_ace_accumulation=True),
    # Plus SuperPrompt, SuperReflexion, SuperRAG
)
```
    </div>
  </div>

  <div class="integration-item">
    <h4>🔄 DSPy + SuperOpt</h4>
    <p>DSPy's pipeline compilation with SuperOpt's environment optimization</p>
    <div class="integration-code">
```python
# DSPy pipelines optimized by SuperOpt
dspy_pipeline = DSPyPipeline()
optimizer = SuperOpt(
    environment=dspy_pipeline.get_environment()
)
```
    </div>
  </div>
</div>

## 🏗️ Additional Foundations

### TextGrad (Textual Differentiation)
The concept of **Natural Language Gradients** in SuperOpt builds on **TextGrad's textual differentiation** approach, extending it to multi-component environment optimization.

### Meta-ACE Extensions
SuperOpt's meta-reasoning capabilities are informed by **Romero's Meta-ACE** framework, particularly in how we handle hierarchical optimization decisions and stability constraints.

## 🙏 Acknowledgments

We gratefully acknowledge the foundational contributions that inspired SuperOpt:

<div class="acknowledgments-grid">
  <div class="ack-item">
    <strong>GEPA</strong><br>
    <span class="ack-authors">Agrawal, Tan, Soylu, Ziems et al.</span><br>
    <span class="ack-focus">Evolutionary prompt optimization</span>
  </div>

  <div class="ack-item">
    <strong>ACE</strong><br>
    <span class="ack-authors">Zhang, Hu, Upasani, Ma et al.</span><br>
    <span class="ack-focus">Context engineering & memory</span>
  </div>

  <div class="ack-item">
    <strong>DSPy</strong><br>
    <span class="ack-authors">Khattab, Singhvi, Maheshwari et al.</span><br>
    <span class="ack-focus">Pipeline compilation</span>
  </div>

  <div class="ack-item">
    <strong>TextGrad</strong><br>
    <span class="ack-authors">Yuksekgonul et al.</span><br>
    <span class="ack-focus">Textual differentiation</span>
  </div>
</div>

## 🎯 SuperOpt's Unique Contribution

SuperOpt represents an evolution in agent optimization research, moving from **single-component approaches** to **comprehensive environment optimization**:

<div class="comparison-table">
  <div class="comparison-row">
    <div class="approach-cell">GEPA</div>
    <div class="focus-cell">Prompts Only</div>
    <div class="method-cell">Evolutionary Search</div>
    <div class="scope-cell">Single Component</div>
  </div>

  <div class="comparison-row">
    <div class="approach-cell">ACE</div>
    <div class="focus-cell">Memory Only</div>
    <div class="method-cell">Context Accumulation</div>
    <div class="scope-cell">Single Component</div>
  </div>

  <div class="comparison-row highlight">
    <div class="approach-cell">SuperOpt</div>
    <div class="focus-cell">All Environment</div>
    <div class="method-cell">Multi-Component Routing</div>
    <div class="scope-cell">Complete Framework</div>
  </div>
</div>

This collaborative approach allows researchers and practitioners to leverage the best of all methodologies within a unified system.

<style>
.papers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.paper-card {
  background: var(--md-default-fg-color--lightest);
  border: 1px solid var(--md-default-fg-color--lighter);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

[data-md-color-scheme="slate"] .paper-card {
  background: #1e1e1e;
  border-color: #333;
}

.paper-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #f093fb, #ff6b6b);
}

.paper-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

[data-md-color-scheme="slate"] .paper-card:hover {
  box-shadow: 0 20px 40px rgba(0,0,0,0.5);
}

[data-md-color-scheme="slate"] .paper-header h3 {
  color: #ffffff;
}

[data-md-color-scheme="slate"] .paper-subtitle {
  color: #ffffff;
}

[data-md-color-scheme="slate"] .paper-description {
  color: #e0e0e0;
}

[data-md-color-scheme="slate"] .paper-authors {
  color: #90caf9;
}

.paper-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.paper-icon {
  font-size: 2rem;
  opacity: 0.8;
}

.paper-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: var(--md-primary-fg-color);
}

.paper-year {
  background: var(--md-accent-fg-color);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.paper-subtitle {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--md-primary-fg-color);
}

.paper-description {
  font-size: 0.9rem;
  color: var(--md-default-fg-color--light);
  line-height: 1.5;
  margin: 0 0 1rem 0;
}

.paper-authors {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--md-accent-fg-color);
  margin-bottom: 1rem;
}

.paper-links {
  display: flex;
  gap: 0.75rem;
}

.paper-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.paper-link {
  background: var(--md-primary-fg-color);
  color: var(--md-primary-bg-color);
}

.paper-link.secondary {
  background: rgba(102, 126, 234, 0.1);
  color: var(--md-primary-fg-color);
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.paper-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.integration-showcase {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.integration-item {
  background: var(--md-code-bg-color);
  border: 1px solid var(--md-default-fg-color--lighter);
  border-radius: 12px;
  padding: 1.5rem;
}

[data-md-color-scheme="slate"] .integration-item {
  background: rgba(30, 30, 30, 0.5);
  border-color: #333;
}

.integration-item h4 {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 0.75rem 0;
  color: var(--md-primary-fg-color);
}

.integration-item p {
  font-size: 0.9rem;
  color: var(--md-default-fg-color--light);
  margin: 0 0 1rem 0;
  line-height: 1.4;
}

.integration-code {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.8rem;
  overflow-x: auto;
}

[data-md-color-scheme="slate"] .integration-code {
  background: rgba(0, 0, 0, 0.3);
}

[data-md-color-scheme="slate"] .integration-item h4 {
  color: #ffffff;
}

[data-md-color-scheme="slate"] .integration-item p {
  color: #e0e0e0;
}

.acknowledgments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 2rem 0;
}

.ack-item {
  background: var(--md-default-fg-color--lightest);
  border: 1px solid var(--md-default-fg-color--lighter);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

[data-md-color-scheme="slate"] .ack-item {
  background: #1e1e1e;
  border-color: #333;
}

[data-md-color-scheme="slate"] .ack-item strong {
  color: #ffffff;
}

[data-md-color-scheme="slate"] .ack-authors {
  color: #90caf9;
}

[data-md-color-scheme="slate"] .ack-focus {
  color: #e0e0e0;
}

.ack-item strong {
  color: var(--md-primary-fg-color);
  font-size: 1.1rem;
}

.ack-authors {
  font-size: 0.8rem;
  color: var(--md-accent-fg-color);
  font-weight: 600;
  margin: 0.25rem 0;
}

.ack-focus {
  font-size: 0.85rem;
  color: var(--md-default-fg-color--light);
}

.comparison-table {
  background: var(--md-default-fg-color--lightest);
  border: 1px solid var(--md-default-fg-color--lighter);
  border-radius: 12px;
  overflow: hidden;
  margin: 2rem 0;
}

[data-md-color-scheme="slate"] .comparison-table {
  background: #1e1e1e;
  border-color: #333;
}

.comparison-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  border-bottom: 1px solid var(--md-default-fg-color--lighter);
}

.comparison-row:last-child {
  border-bottom: none;
}

.comparison-row.highlight {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(240, 147, 251, 0.1));
}

[data-md-color-scheme="slate"] .comparison-row.highlight {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(240, 147, 251, 0.2));
}

[data-md-color-scheme="slate"] .comparison-row div {
  color: #e0e0e0;
}

[data-md-color-scheme="slate"] .approach-cell {
  background: #1e3a8a;
  color: #ffffff;
}

.comparison-row div {
  padding: 1rem;
  text-align: center;
  font-size: 0.9rem;
  font-weight: 600;
}

.approach-cell {
  background: var(--md-primary-fg-color);
  color: var(--md-primary-bg-color);
  font-weight: 700;
}

.focus-cell, .method-cell, .scope-cell {
  color: var(--md-default-fg-color);
}

@media (max-width: 768px) {
  .papers-grid {
    grid-template-columns: 1fr;
  }

  .integration-showcase {
    grid-template-columns: 1fr;
  }

  .comparison-table {
    font-size: 0.8rem;
  }

  .comparison-row {
    grid-template-columns: 1fr;
  }

  .comparison-row div {
    padding: 0.75rem 0.5rem;
  }

  .approach-cell {
    border-bottom: 2px solid var(--md-accent-fg-color);
  }
}
</style>
