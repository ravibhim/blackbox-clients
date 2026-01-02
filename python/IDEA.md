# Beyond Evals: A Function-First Approach to AI Product Development

*A whitepaper exploring the gaps between traditional evaluation frameworks and the practical needs of AI product builders*

---

## Introduction

Building production-grade AI systems is fundamentally different from prototyping with LLMs. A chatbot demo that works well in your IDE becomes unreliable when deployed at scale. A prompt that generates impressive outputs for cherry-picked examples fails unpredictably with real user inputs. The path from prototype to production is littered with AI products that seemed promising but couldn't maintain quality, couldn't be iterated on confidently, or couldn't scale to handle the complexity of real-world usage.

The challenge isn't the underlying models—LLMs have remarkable capabilities. The challenge is **engineering discipline**: how do you systematically build, evaluate, and improve AI systems so they work reliably in production?

Traditional software engineering solved this with rigorous testing frameworks, continuous integration, and well-defined interfaces. But AI systems introduce non-determinism that breaks these paradigms. The same input can produce different outputs. "Correctness" is often fuzzy and context-dependent. Edge cases emerge from the infinite space of natural language rather than discrete code paths.

Most teams reach for **evaluation frameworks (evals)** as the solution. While evals represent progress toward systematic development, they introduce their own brittleness: custom evaluator functions that must be written, maintained, and kept in sync with evolving prompts. The result is often a complex evaluation apparatus that slows iteration rather than enabling it.

This whitepaper presents an alternative approach—**Example-Driven Evaluation**—designed specifically for the realities of building production AI systems. It's grounded in three core principles:

1. **Think in functions, not prompts**: Structure AI systems with clear input/output contracts, treating LLM calls as implementation details inside black box functions.

2. **Build quality through datasets**: Curate datasets of real outputs labeled by quality, letting the data reveal what works rather than trying to codify rules.

3. **Use semantic similarity as a universal evaluator**: Replace custom evaluator code with correlation analysis between semantic similarity and quality labels.

This approach emerged from the practical need to iterate quickly on AI products while maintaining quality at scale. It prioritizes clarity on function design over evaluation sophistication, recognizes that production usage provides the most valuable signal, and embraces the non-deterministic nature of LLMs rather than fighting it.

Whether you're building chatbots, document processing pipelines, code generation tools, or agentic systems, the principles in this whitepaper provide a foundation for moving from prototype to production with confidence.

---

## 1. The AI Product Builder's Needs

### 1.1 The Black Box Function: A New Abstraction for AI Products

#### The Core Shift in AI Product Development

The fundamental building block of AI products is not a prompt, a workflow, or an agent—it is a **function**. This may seem obvious to software engineers, but the nature of these functions has fundamentally changed with the advent of large language models.

#### From White Box to Black Box

Traditionally, functions in software engineering are **white boxes**: deterministic execution of logic where the same inputs always produce the same outputs. The implementation is transparent, debuggable, and predictable. You write code that follows a clear logical path from input to output.

With AI systems, we must embrace a new reality: **functions are now black boxes**. Inside that black box might be:
- A single LLM prompt
- A sequence of chained prompts
- An agent executing tool calls
- A combination of deterministic logic and AI calls
- Multiple models working in concert

The logic is **non-deterministic**. The same input may produce different outputs. The internal reasoning is opaque. This is not a limitation to be solved—it is the fundamental nature of AI-powered functions.

#### What Remains Constant: Inputs and Outputs

Despite this shift from determinism to non-determinism, one critical aspect remains unchanged: **every function has inputs and outputs, and these are data structures**.

Whether white box or black box:
- **Inputs** are structured data that define what the function needs to operate
- **Outputs** are structured data that define what the function produces
- Both can be designed, specified, and reasoned about

This is the anchor point for AI product builders. You cannot control or fully predict what happens inside the black box, but you **can** design the interface—the contract between the function and the rest of your system.

#### Function Design as the Central Activity

If you accept that functions are black boxes, then **function design becomes the primary lever for building good AI products**. This means:

1. **Designing input data structures** that capture the right information for the problem
2. **Designing output data structures** that deliver value in the format your product needs
3. **Iterating on these signatures** as you learn more about the problem space

The quality of your AI product is directly proportional to how well you design these function boundaries. A well-designed function with clear inputs and outputs can accommodate many different implementations inside the black box—from simple prompts to complex agentic systems.

The shift from thinking in "prompts" to thinking in "black box functions with data structure contracts" is the foundational mental model for effective AI product building.

### 1.2 Dataset Building as a Complementary Activity

While function design provides the structural foundation for AI products, **dataset building** is the complementary activity that brings clarity to the black box. These two activities must go hand-in-hand—you cannot design functions in a vacuum, and datasets without clear function boundaries are meaningless.

#### Capturing Non-Deterministic Reality

Because black box functions produce non-deterministic outputs, your dataset must reflect this reality. Unlike traditional software testing where you might check for exact matches, AI function datasets should **capture various examples of varying quality**.

A well-built dataset for a black box function includes:
- Edge cases and typical cases
- Good outputs and poor outputs
- Unexpected variations that the function produces
- Different styles or approaches that might all be acceptable

This is not a bug—it's a feature. The dataset becomes a map of the possibility space your function operates within.

#### The Iterative Clarity Loop

Here's the powerful insight: **even without a formal evaluation framework, the act of capturing data points in a dataset provides immense clarity**. As you build your dataset, you are forced to:

1. **Run your function with real inputs**
2. **Observe actual outputs**
3. **Develop opinions on quality**

This simple loop is where the real work of AI product building happens. Each data point becomes a forcing function for critical thinking about your black box function.

#### What Emerges from Dataset Building

As the builder develops opinions on the data points in the dataset, multiple areas of improvement naturally emerge:

**Quality Intuition**: You begin to recognize patterns in what makes outputs good or bad. You develop a sense for the function's failure modes and success patterns.

**Function Signature Enhancements**: You realize that certain inputs are missing or poorly structured. You discover that outputs need additional fields or different structures to be truly useful.

**Architectural Insights**: You might realize the black box function is trying to do too much and should be broken into smaller functions. Or conversely, you might see that multiple functions should be combined into one.

**Implementation Improvements**: You gain insight into how to better utilize the AI within the black box—whether through prompt refinement, different model choices, or changed reasoning strategies.

#### Dataset Building Enables Function Clarity

The core value proposition is this: **dataset building is the primary mechanism through which builders gain clarity on their black box functions**. 

You don't start with perfect function design and then build a dataset to validate it. Instead, you co-evolve the function design and the dataset together. Each data point you capture informs the next iteration of your function signature. Each function signature change prompts you to gather new data points.

This iterative process of capturing real inputs and outputs, developing opinions on them, and refining your function design is the path to building effective AI products. The dataset is not just a testing artifact—it is the laboratory where understanding emerges.

### 1.3 Continuous Dataset Enhancement: Real-World Usage Observations

The final piece of achieving clarity on your black box function comes from **actual product usage**. While initial dataset building happens in the development phase, true understanding only emerges when your function meets real users and real problems.

#### The Ground Reality Gap

No matter how thoughtfully you design your initial dataset, you cannot fully anticipate:
- The edge cases users will discover
- The creative ways users will interact with your function
- The distribution of real-world inputs
- The contextual variations that matter in practice

Your initial dataset is a hypothesis about what matters. Real-world usage is the experiment that tests that hypothesis.

#### Continuous Dataset Enhancement

A mature approach to AI product building recognizes that **dataset expansion is ongoing**, not a one-time activity. As your product runs in the real world, you should systematically capture:

- Novel inputs that weren't represented in your initial dataset
- Failure modes that only appear at scale or in specific contexts
- Successful patterns that emerge from actual usage
- User feedback that reveals quality dimensions you hadn't considered

This real-world data provides **coverage and variety** that reflects the actual ground reality of problems being solved, not just the problems you imagined during design.

#### Framework Requirements

Any thinking model or framework for AI product development must accommodate this reality. It should make it easy to:

1. **Capture production data** in the same format as your development dataset
2. **Integrate new examples** without disrupting your existing workflow
3. **Track the evolution** of your dataset over time
4. **Connect usage patterns** back to function design decisions

The framework should treat dataset expansion as a first-class activity, not an afterthought.

#### Achieving Complete Clarity

This three-phase journey—function design, initial dataset building, and continuous enhancement from real usage—is what truly completes the clarity one can obtain for a black box function.

You move from:
- **Theoretical understanding** (function design)
- To **empirical validation** (dataset building)
- To **ground truth alignment** (real-world observations)

Only when all three are working together do you have complete clarity on what your black box function does, how it performs, and where it needs improvement. This is the foundation upon which effective AI products are built.

---

## 2. The Current State of Evals

### 2.1 The Eval Paradigm

Traditional evaluation frameworks (evals) share a similar starting point with the function-first approach: they recognize the need to improve LLM workflows through the use of datasets. On the surface, this seems aligned with the needs outlined in Section 1.

However, the eval paradigm introduces a critical requirement: **for each black box function, the builder must provide evaluator functions or critiquing functions**. These evaluators are meant to programmatically assess whether outputs are correct, high-quality, or meet certain criteria.

In theory, this sounds reasonable. In practice, it introduces fundamental brittleness into the development process.

### 2.2 The Brittleness of Custom Evaluators

A good eval setup requires the builder to **custom design evaluator functions** for each black box function they create. This means:

- Writing code that can judge the quality of non-deterministic outputs
- Anticipating all the ways outputs might vary while still being acceptable
- Creating scoring or grading logic that captures nuanced quality dimensions
- Maintaining these evaluators as requirements evolve

This creates a **second design problem** on top of the already-challenging task of designing the black box function itself. Now you're not just designing inputs and outputs—you're also designing the judge of those outputs.

The brittleness emerges because:
- Evaluator functions are themselves code that can be wrong or incomplete
- They require the builder to formalize intuitions that may still be developing
- They add another layer that must be maintained and debugged
- They can give false confidence when they pass or false alarms when they fail

### 2.3 Tight Coupling to Prompts

Perhaps the more fundamental issue is that **in practice, evals have become tightly coupled to prompts**, not to structured function outputs.

The dominant pattern in eval frameworks is:
1. Write a prompt
2. Generate some outputs from that prompt
3. Write evaluators to judge those specific outputs
4. Iterate on the prompt
5. Re-run evaluations

This reveals a critical misalignment: **the eval paradigm never really conceptualized LLM workflows as black box functions** with well-defined input and output data structures.

Instead, evals operate at the prompt level, treating the prompt as the unit of iteration. The outputs are often unstructured text that must be parsed, interpreted, or pattern-matched by evaluators. There's no clean separation between the interface (function signature) and the implementation (what happens in the black box).

### 2.4 The Co-Evolution Problem

This tight coupling creates a pernicious co-evolution problem: **as the prompt evolves, the evaluator functions must also evolve**.

Consider what happens in practice:
- You change your prompt to fix one issue
- The output format changes slightly
- Now your evaluators break or become less accurate
- You update the evaluators to match the new output format
- You change the prompt again
- The cycle repeats

The evaluators become coupled to the implementation details inside the black box, not to the stable interface of the function. This is the opposite of good software engineering practice, where interfaces remain stable while implementations vary.

### 2.5 The Fundamental Gripe

Here's the core issue: **traditional evals create a brittle, tightly-coupled system that makes iteration harder, not easier**.

Instead of helping builders gain clarity on their black box functions, evals demand that builders:
1. Design the function
2. Design the evaluator
3. Keep both in sync as things evolve
4. Debug failures that could be in either the function or the evaluator

This doubles the cognitive load and creates a maintenance burden that slows down the very iteration that evals are meant to accelerate.

For the AI product builder trying to gain clarity on function design, this is backwards. The framework should reduce complexity and support rapid iteration, not introduce additional layers of fragile abstraction.

---

## 3. Example-Driven Evaluation

### 3.1 The Core Principle: Quality-Labeled Datasets

The alternative to traditional evals starts with the same foundation outlined in Section 1: **building a dataset for your black box function**. However, instead of requiring custom evaluator functions, this approach adds one critical element: **quality labels**.

As the builder captures data points (input-output pairs) for their function, they should label them according to quality:

1. **High quality** - outputs that exemplify what the function should produce
2. **Average quality** - outputs that are acceptable but not ideal
3. **Poor quality** - outputs that are wrong, incomplete, or problematic

These quality judgments can be mapped to a scale between 0 and 1, where:
- High quality ≈ 0.8 - 1.0
- Average quality ≈ 0.4 - 0.7  
- Poor quality ≈ 0.0 - 0.3

This labeling doesn't require formalization into code—it's simply the builder developing and recording their opinions on the data, which they would do naturally anyway (as described in Section 1.2).

### 3.2 The Builder Experience: Review, Don't Write

A critical aspect of Example-Driven Evaluation is the **workflow it enables for builders**. The builder should not be painstakingly writing down outputs by hand. Instead, the experience should be one of **review and curation**.

The workflow looks like this:

1. **Run the black box function** with various inputs (real or synthetic)
2. **Review the actual outputs** the function generates
3. **Make a decision** for each output:
   - Add to dataset with a quality label (high/average/poor)
   - Or discard if not useful for the dataset
4. **Build the dataset organically** through this review process

This is fundamentally different from traditional test-driven development where you write expected outputs first. With non-deterministic black box functions, you often don't know what good outputs look like until you see them.

The builder's role is to:
- **Observe** what the function actually produces
- **Judge** the quality based on their understanding of the problem
- **Curate** a collection of examples that span the quality spectrum

This review-based workflow is much faster and more natural than manually crafting outputs. It also ensures that your dataset contains realistic outputs that the function can actually produce, rather than idealized outputs that may never occur in practice.

The dataset grows organically as the builder encounters interesting, edge-case, or representative examples—not through upfront specification of all possible scenarios.

### 3.3 The Universal Evaluator: Semantic Similarity

Here's where this approach diverges fundamentally from traditional evals: **instead of requiring custom evaluator functions, we leverage semantic similarity via embeddings as a universal evaluator**.

The insight is simple but powerful:
- If your function produces structured outputs, you can compute embeddings of those outputs
- You can measure semantic similarity between any two outputs
- This similarity metric is universal—it works for any output structure without custom code

Semantic similarity becomes the lens through which we understand function behavior, replacing brittle, custom-coded evaluators with a general-purpose measurement tool.

#### Example: Customer Support Response Function

Consider a black box function that generates customer support responses:

**Input structure:**
```json
{
  "customer_query": "I can't log into my account",
  "context": "Premium subscriber, last login 3 days ago"
}
```

**Output structure:**
```json
{
  "response": "I understand you're having trouble logging in...",
  "tone": "empathetic",
  "next_steps": ["Reset password link sent", "Check spam folder"]
}
```

**Quality-labeled examples in your dataset:**

**High quality (0.9):**
```json
{
  "response": "I understand the frustration of being locked out. I've sent a password reset link to your email. If you don't see it in 5 minutes, please check your spam folder.",
  "tone": "empathetic",
  "next_steps": ["Password reset sent", "Check spam if not received"]
}
```

**Average quality (0.5):**
```json
{
  "response": "You need to reset your password. Check your email.",
  "tone": "neutral",
  "next_steps": ["Check email"]
}
```

**Poor quality (0.2):**
```json
{
  "response": "Login problems happen. Try again later.",
  "tone": "dismissive",
  "next_steps": []
}
```

**How semantic similarity works:**

When your function generates a new output, you:
1. **Serialize the structured output** into a format suitable for embedding (e.g., concatenate fields)
2. **Compute embedding** using a model like `text-embedding-3-large` or `all-mpnet-base-v2`
3. **Calculate cosine similarity** between the new output and each labeled example

**New output from your function:**
```json
{
  "response": "I see you're unable to access your account. I've immediately sent a password reset to your registered email. Please allow 5 minutes for delivery, and check your spam folder if needed.",
  "tone": "empathetic", 
  "next_steps": ["Password reset sent", "Check spam folder"]
}
```

**Semantic similarity scores:**
- Similarity to high-quality example: **0.94** (very close semantically)
- Similarity to average-quality example: **0.67** (shares some content but less detail)
- Similarity to poor-quality example: **0.31** (different tone and helpfulness)

The new output is semantically most similar to the high-quality example—it has the same empathetic tone, provides clear next steps, and addresses the customer's frustration. This similarity emerges **automatically from embeddings**, without writing any custom logic to check for "empathetic language" or "clear next steps."

**Another new output (poor quality):**
```json
{
  "response": "Reset your password.",
  "tone": "curt",
  "next_steps": ["Reset password"]
}
```

**Semantic similarity scores:**
- Similarity to high-quality example: **0.42** (different semantic content)
- Similarity to average-quality example: **0.71** (closer match)
- Similarity to poor-quality example: **0.89** (very similar brevity and tone)

This output is semantically closest to poor-quality examples—terse, lacking empathy, minimal guidance. Again, **no custom evaluator needed**. The embeddings capture the semantic essence of "good" vs "poor" responses.

**The universal property:**

The same semantic similarity approach works for:
- Email drafts with different writing styles
- Product descriptions with varying detail levels
- Code comments with different clarity
- Meeting summaries with different comprehensiveness

You design how to embed your specific output structure once, then semantic similarity serves as your universal quality signal across all examples.

### 3.4 The Correlation Metric

The key innovation is using **correlation between semantic similarity and quality labels** as the primary signal for function performance.

Here's how it works:

1. **Build your quality-labeled dataset** with examples spanning high, average, and poor quality
2. **Run your black box function** on new inputs to generate outputs
3. **Compute semantic similarity** between each new output and each labeled example in your dataset
4. **Find the correlation** between the similarity scores and the quality labels

The hypothesis: **If semantic similarity correlates strongly with quality, then your function is producing outputs that align with your understanding of good vs. poor performance**.

A correlation close to 1 means:
- Outputs similar to high-quality examples are indeed high quality
- Outputs similar to poor-quality examples are indeed poor quality
- The semantic space meaningfully captures your quality dimension

### 3.5 Iteration Without Evaluator Maintenance

As you iterate on your black box function—whether by changing prompts, adjusting models, or modifying the implementation—you simply:

1. **Generate new outputs** with the updated function
2. **Recompute correlation** between similarity and quality labels
3. **Compare correlations** across versions

**Improved correlation = improved function performance**, without ever writing or maintaining an evaluator function.

This approach has several advantages:

- **No custom code**: Semantic similarity is your universal evaluator
- **No tight coupling**: You're not tied to specific prompt formats or output structures
- **Stable interface**: The labeled dataset anchors evaluation, not implementation details
- **Progressive refinement**: As you gather more labeled examples, your evaluation becomes more robust

### 3.6 The Semantic Similarity Function

A critical piece is designing a **semantic similarity function for your output structure**. Since black box functions produce structured outputs (data structures, as established in Section 1.1), you need a way to:

- Convert structured outputs into embeddings
- Compute meaningful similarity scores between outputs

This might involve:
- Serializing structured data into text for embedding
- Using specialized embedding models for structured data
- Combining embeddings of different fields in the output structure
- Weighting different aspects of the output based on importance

The beauty is that **this similarity function is designed once for your output structure** and then works universally across all your labeled examples and future outputs. You're not writing evaluators for specific correctness criteria—you're defining how to measure "sameness" in your output space.

### 3.7 Black Box Functions with List Outputs

Many practical black box functions return not a single structure, but a **list of structures**. Consider these common scenarios:

- Extracting named entities from text (list of entities)
- Retrieving relevant documents (list of documents)
- Generating multiple recommendations (list of items)
- Identifying features in an image (list of features)

When your function returns a list, you need to extend your similarity function to handle this output type while maintaining the universal evaluator principle.

#### The Order Problem

A critical consideration is whether order matters in your output lists. For many use cases, **order is irrelevant or non-deterministic**:

**Example: City Name Extraction**

Your function extracts and normalizes city names from text:

Input:
```
{
  "text": "I traveled from Mumbai to Dubai, then to London"
}
```

Output:
```
[
  {"city": "Mumbai", "country": "India"},
  {"city": "Dubai", "country": "UAE"},
  {"city": "London", "country": "UK"}
]
```

In practice, especially with parallel LLM calls, the order of results is **non-deterministic**:

```python
# Parallel processing - unpredictable response order
results = await asyncio.gather(
    extract_cities_chunk_1(text),
    extract_cities_chunk_2(text),
    extract_cities_chunk_3(text)
)
all_cities = flatten(results)  # Order not guaranteed
```

Two runs might return `[Mumbai, Dubai, London]` and `[London, Dubai, Mumbai]` - these should be considered identical outputs.

#### Set-Based Similarity Without Thresholds

For unordered lists, you need **order-agnostic similarity**. The challenge is comparing sets of items where:
- Order doesn't matter
- Sizes might differ (missing or extra items)
- Items should match semantically, not just exactly

The solution is **optimal bipartite matching** using the Hungarian algorithm:

```python
def unordered_list_similarity(list_a, list_b):
    # Embed each item in both lists
    embeddings_a = [embed(item) for item in list_a]
    embeddings_b = [embed(item) for item in list_b]
    
    # Build similarity matrix between all pairs
    n, m = len(embeddings_a), len(embeddings_b)
    similarity_matrix = np.zeros((n, m))
    for i, emb_a in enumerate(embeddings_a):
        for j, emb_b in enumerate(embeddings_b):
            similarity_matrix[i, j] = cosine_similarity(emb_a, emb_b)
    
    # Pad to square matrix to handle size mismatch
    max_size = max(n, m)
    padded_matrix = np.zeros((max_size, max_size))
    padded_matrix[:n, :m] = similarity_matrix
    
    # Find optimal one-to-one matching
    row_ind, col_ind = linear_sum_assignment(-padded_matrix)
    
    # Sum of matched similarities, normalized by max size
    matched_sum = sum(padded_matrix[i, j] 
                     for i, j in zip(row_ind, col_ind))
    return matched_sum / max_size
```

#### Why This Works

**Scenario 1: Same items, different order**
- List A: `[Mumbai, Dubai, London]`
- List B: `[London, Dubai, Mumbai]`
- Optimal matching pairs each city perfectly
- Similarity: 1.0

**Scenario 2: One wrong item**
- List A: `[Mumbai, Dubai, London]`
- List B: `[Mumbai, Dubai, Paris]`
- Two perfect matches, one poor match (London-Paris ~ 0.45)
- Similarity: (1.0 + 1.0 + 0.45) / 3 = 0.82

**Scenario 3: Missing item**
- List A: `[Mumbai, Dubai, London]`
- List B: `[Mumbai, Dubai]`
- Two matches, one item paired with padding (similarity 0)
- Similarity: (1.0 + 1.0 + 0.0) / 3 = 0.67

**Scenario 4: Completely different**
- List A: `[Mumbai, Dubai]`
- List B: `[Paris, Tokyo]`
- All pairings have low similarity (~0.3-0.4)
- Similarity: ~0.35

The normalization by the larger list size automatically penalizes size mismatches, and the optimal matching ensures order doesn't affect the result.

#### No Thresholds Required

A critical advantage of this approach: **no threshold parameter needed**. You don't need to decide "what similarity counts as a match"—the optimal matching algorithm finds the best overall pairing, and the resulting similarity score directly reflects output quality.

This maintains the universal evaluator principle. You're not tuning hyperparameters; you're simply defining how to compare lists in a mathematically principled way.

#### The Correlation Framework Still Applies

Once you have an order-agnostic list similarity function:

1. **Build quality-labeled dataset** with list outputs (high/average/poor quality)
2. **Compute list similarity** between new outputs and labeled examples
3. **Measure correlation** between similarity and quality labels
4. **High correlation = good function performance**

The example-driven evaluation framework remains intact—you've simply extended the similarity function to handle a different output structure.

#### Design Considerations for Lists

When working with list outputs, you design your similarity function based on:

**Item embedding**: How do you represent each item in the list?
- For cities: Embed the combined `{city, country}` structure
- For documents: Embed title + snippet
- For entities: Embed entity text + type

**Handling size variation**: The optimal matching with padding handles this automatically
- Missing items get paired with zeros (penalty)
- Extra items get paired with zeros (penalty)
- Natural trade-off emerges through the data

**Order sensitivity**: If order matters (e.g., ranked search results), use a different similarity function that weights position. But for many practical cases—parallel extraction, entity recognition, multi-label classification—order is irrelevant, and set-based matching is the right choice.

The key principle remains: **design the similarity function once for your output structure, then let correlation with quality labels drive evaluation**.

### 3.8 Why This Works

This approach aligns with how AI product builders actually work:

- **Builders develop quality intuitions** through exposure to examples (captured in labels)
- **Semantic similarity captures proximity in meaning space** (what embeddings do well)
- **High correlation validates** that your quality intuitions are reflected in semantic structure
- **Low correlation surfaces problems** either in the function or in how you're measuring similarity

Rather than forcing builders to codify quality judgments into evaluator code, this approach lets builders **express quality through examples** and uses correlation to validate that the black box function aligns with those examples.

It's evaluation through exemplars, not through rules.

---

## 4. Limitations: Production Quality Monitoring

Example-Driven Evaluation is a **development methodology**, not a production monitoring system. It excels at helping builders iterate, compare versions, and improve functions before deployment. However, it does not solve real-time production quality assessment.

### What It Does Not Address

**Real-time quality prediction**: The approach is built on correlation analysis across many examples. It cannot assess the quality of individual outputs as they're generated in production.

**Novel production cases**: When production encounters scenarios not represented in your labeled dataset, the evaluation framework cannot provide meaningful quality signals for those cases.

**Individual go/no-go decisions**: Correlation is a population-level metric. It tells you whether your function is performing well overall, not whether a specific output should be shown to the user.

### What to Use Instead

For production quality monitoring, use standard approaches:

- **User feedback**: Thumbs up/down, usage signals, satisfaction tracking
- **Automated checks**: Format validation, length checks, safety filters
- **Standard metrics**: Error rates, latency, throughput

### The Integration Point

Example-Driven Evaluation and production monitoring connect through a feedback loop: deploy with standard monitoring, collect production data and user feedback, review interesting cases to expand your dataset, then re-run correlation analysis to validate and iterate on your function.

The value proposition is clear: **build better functions through rigorous development practices, then monitor them in production with simple, reliable tools**.

---

## Conclusion

*[Section to be developed]*
