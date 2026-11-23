# Privacy Policy Analyzer

Tools to crawl, analyze and report on website privacy policies using NLP models and rule-based patterns.

## Features

The main features of the package include:

- A web-scraper to extract privacy policies from websites.
- Functions to analyze privacy policies with NLP machine learning models.
- Functions to train models for privacy policy analysis.
- Utilities to summarize and visualize the analysis results.

## Hierarchy Multi-label Classification

This package uses Hierarchy Multi-label Classification to analyze privacy policies.

The taxonomy can be viewed here: [Taxonomy](./taxonomy.png)

## Using the Package

# Installation

The default installation only includes what's needed to crawl and analyze privacy policies. Two optional extras are available:

- `training` - dependencies needed to fine-tune models (`datasets`, `scikit-learn`, `accelerate`, `bitsandbytes` for GPU quantization).
- `onnx` - `optimum[onnxruntime]` for ONNX Runtime inference.

```bash
privacy_policy_analyzer[training,onnx]
```

Additonally, the correct version of PyTorch must be installed for the specific GPU and CUDA version. Please refer to the [PyTorch installation guide](https://pytorch.org/get-started/locally/) to install the appropriate version.

## Post-Installation

This package uses playwright for web crawling. After installing the package, please run the following command to install the necessary browser binaries:

```bash
python -m playwright install chromium
```

### Crawler

This section demonstrates how to use the crawler to extract privacy policies from a given URL.

```python
from privacy_policy_analyzer import Language
from privacy_policy_analyzer.crawl import CollectedPolicy, CrawlError, crawl
from privacy_policy_analyzer.patterns.en import EN_SPLITTER_CONFIG

url = "https://openai.com/policies/row-privacy-policy/"
name = "OpenAI"

result: CollectedPolicy | CrawlError = crawl(
    name, url, Language.EN, {Language.EN: EN_SPLITTER_CONFIG}, False
)

if isinstance(result, CollectedPolicy):
    print(f"Successfully crawled policy for {name} at {url}")
    print("Extracted Text:")
    print(result.text)
    print(result.structured)


```

### Analysis

This section demonstrates how to analyze a privacy policy using the pipeline.
The pipeline can accept either HTML text, a URL, or an already crawled policy.

```python
from privacy_policy_analyzer import Language
from privacy_policy_analyzer.config import DEFAULT_CONFIGURATIONS
from privacy_policy_analyzer.crawl import CrawlError
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult, UnsupportedLanguage

# Pipeline holds one configuration per registered language
pipeline: Pipeline = Pipeline(
    configs=DEFAULT_CONFIGURATIONS,
    prefer_onnx=False,
)

name = "OpenAI"
url = "https://openai.com/policies/row-privacy-policy/"

# Or analyze directly from URL - pass language=None instead of Language.EN
# to auto-detect the language from the scraped content
result: PolicyResult | CrawlError | UnsupportedLanguage = pipeline.run_with_url(
    name, url, Language.EN
)

if isinstance(result, PolicyResult):
    print("Analysis Results:")
    print(result.text)
    print(result.structured)
    print(result.analyzed)

```

### Results

This section demonstrates how to generate various reports and visualizations from the analysis results.

```python
from privacy_policy_analyzer.pipeline import PolicyResult
from privacy_policy_analyzer.report.detailed import create_detailed_report
from privacy_policy_analyzer.report.flow import generate_topic_map
from privacy_policy_analyzer.report.label import generate_svg_label
from privacy_policy_analyzer.report.score import create_score_report
from privacy_policy_analyzer.report.summary import create_summary_report

# Assuming `policy_result` is an instance of `PolicyResult` obtained from analysis
policy: PolicyResult = ...  # Replace with actual PolicyResult object

include_scopes: list[str] = []
exclude_scopes: list[str] = []

# Generate and print detailed report
detailed = create_detailed_report(
    policy.analyzed, include_scopes, exclude_scopes
)
print(detailed)

# Generate and print summary report
summary = create_summary_report(policy.analyzed, include_scopes, exclude_scopes)
print(summary)

# Generate and print score report
scores = create_score_report(summary)
print(scores)

# Generate and save topic map SVG
topic_map_png = generate_topic_map(policy.analyzed)
with open("topic_map.png", "wb") as f:
    f.write(topic_map_png)
print("Topic map SVG saved as topic_map.svg")

# Generate and save label SVG
label_svg = generate_svg_label(scores, summary, policy.source)
with open("label.svg", "w", encoding="utf-8") as f:
    f.write(label_svg)
print("Label SVG saved as label.svg")

```

### Labeling & Training

The flow to train a new model is typical as follows:

- Crawl Policies and extract raw text segments. This can be done using the crawler module.
- Annotate the extracted segments using the [annotation tool](./annotate.html) provided in the package. (Just open the HTML file in a web browser, and upload the raw text and annotation [schema](./annotation_schema.json).)
- Save the labeled data in a folder. The training module expects each file to be a JSON file containing the labeled segments.
- Load the training data files and annotation schema, and configure the training parameters.
- After training is finished, the trained models will be saved to the specified output directory. They can be used in the analysis pipeline and/or be uploaded to the HuggingFace model hub.

Training is run from the command line (needs the `training` extra: `pip install "privacy-policy-analyzer[training]"`):

```bash
# see how the data is split and how many samples each task gets, train nothing
python -m privacy_policy_analyzer.training --data DATA --schema SCHEMA --out OUT \
    --models distilbert-base-uncased --dry-run

# train scope, topic and one content model per topic
python -m privacy_policy_analyzer.training --data DATA --schema SCHEMA --out OUT \
    --models distilbert-base-uncased roberta-base

# a subset of tasks, other hyperparameters
python -m privacy_policy_analyzer.training --data DATA --schema SCHEMA --out OUT \
    --models distilbert-base-uncased --tasks scope content:Security/Privacy --epochs 5 --lr 3e-5
```

or from Python (see [examples/training.py](./examples/training.py)):

```python
from pathlib import Path

from privacy_policy_analyzer.training import TrainingConfig, run_experiment

run_experiment(
    data_dir=Path("policies/en/labeled/final"),
    schema_file=Path("annotation_schema.json"),
    out_dir=Path("models/en"),
    models=["distilbert-base-uncased"],
    config=TrainingConfig(seed=42),
)
```

**Data split.** By default the data is split by policy (`--split-by policy`, 70/15/15 by default,
`--split`): every real policy goes whole into exactly one of train, eval or test, so near-identical
sentences of one policy never end up on both sides. The synthesized files (file name contains
`synthesized`) and the individual files (file name contains `individual`: real sentences collected
one by one from policies that are not in the corpus otherwise) belong to no policy and are split
sentence by sentence with the same ratios; individual sentences count as real in the metrics.
`--split-by sentence` splits every sentence individually instead; this leaks policy-specific wording
into the test set and gives optimistic scores.

The sentences that are split one by one are distributed label by label (stratified, the default;
`--no-stratify` for a random split): rarest label first, each sentence goes to the partition that is
furthest below its share of that label, counting what the whole policies already put there. So
every label reaches train, eval and test in roughly the split ratios where the data allows; a label
with at least 3 such positives in total is guaranteed in every partition (2: train and test,
1: train). The policies themselves are assigned exactly as without stratification.

The split is computed once and frozen to
`<out>/split.json`: all models and tasks use the same test set, and a rerun with a different seed,
ratios, split mode or stratification (or changed data) stops with an error unless `--resplit` is given.
Changes to fields training does not read (attributes, scope specifics) only log a warning: the split
also stores a fingerprint of the sentences and their scope, topic and content labels. The eval
partition selects the best epoch and the per-label thresholds; the test partition is evaluated once
at the end, on all sentences and on the real ones only.

**Reproducibility.** The data is read in sorted order, the split depends only on the seed, and every
run is re-seeded before the classification head is initialised (so a run does not depend on which
runs came before it). GPU kernels are deterministic unless `--no-deterministic` is given. Each
`<out>/<task>/training_results_<model>.json` stores the hyperparameters, the split, a fingerprint of
the data and the library versions. A run with identical inputs is skipped on a rerun (`--force` to
repeat it).

### Defaults & Configurations

Several default configurations are provided for convenience.

#### **Model Configs**

These configurations define which models to use and what classification thresholds to apply.
The default model configurations can be imported from `privacy_policy_analyzer.config.DEFAULT_MODEL_CONFIGS`.
They use pre-trained models hosted on HuggingFace.

- [Scope Classifier](https://huggingface.co/Wravn/privacy-policy-context)
- [Topic Classifier](https://huggingface.co/Wravn/privacy-policy-topic)
- Content Classifiers for each topic, e.g.:
  - [User Rights Content Classifier](https://huggingface.co/Wravn/privacy-policy-content-userrights)
  - ...

#### **Pattern Configs**

These pattern configurations define regular expressions to identify specific information in the privacy policy text, such as dates, durations and data types.
The default pattern configurations for English can be imported from `privacy_policy_analyzer.patterns.en`.
More languages and configurations can be added in the future or specified by the user.

#### **Splitter Configs**

These pattern configure how to split long text sections into smaller segments for analysis.
The default splitter configurations for English can be imported from `privacy_policy_analyzer.patterns.en.EN_SPLITTER_CONFIG`.
