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

The default installation does not include all the dependencies nessary for analysis and training on GPUs. To install the package with all optional dependencies, please run:

```bash
privacy_policy_analyzer[gpu]
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
    name, url, Language.EN, EN_SPLITTER_CONFIG
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
from privacy_policy_analyzer.analysis import DEFAULT_MODEL_CONFIGS
from privacy_policy_analyzer.crawl import CrawlError
from privacy_policy_analyzer.patterns.en import (
    EN_DATE_PATTERN_CONFIG,
    EN_DURATION_PATTERN_CONFIG,
    EN_PATTERN_CONFIG,
    EN_SPLITTER_CONFIG,
)
from privacy_policy_analyzer.pipeline import Pipeline, PolicyResult

pipeline: Pipeline = Pipeline(
    language=Language.EN,
    model_configs=DEFAULT_MODEL_CONFIGS,
    splitter_configs=EN_SPLITTER_CONFIG,
    pattern_configs=EN_PATTERN_CONFIG,
    duration_pattern_configs=EN_DURATION_PATTERN_CONFIG,
    date_pattern_config=EN_DATE_PATTERN_CONFIG,
    onnx=False,
)

name = "OpenAI"
url = "https://openai.com/policies/row-privacy-policy/"

# Or analyze directly from URL
result: PolicyResult | CrawlError = pipeline.run_with_url(name, url, Language.EN)

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

include_contexts: list[str] = []
exclude_contexts: list[str] = []

# Generate and print detailed report
detailed = create_detailed_report(
    policy.analyzed, include_contexts, exclude_contexts
)
print(detailed)

# Generate and print summary report
summary = create_summary_report(policy.analyzed, include_contexts, exclude_contexts)
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

```python
import logging
from pathlib import Path

from privacy_policy_analyzer.shared.annotation import (
    RawEntry,
    read_training_data,
)
from privacy_policy_analyzer.shared.logging import set_logging
from privacy_policy_analyzer.training import ModelTrainingConfig
from privacy_policy_analyzer.training.data import (
    LabelSchema,
    read_annotation_schema,
)
from privacy_policy_analyzer.training.util import (
    disable_logging,
    set_global_seed,
)

SEED: int = 42
set_global_seed(SEED)

# disable logging from other modules
disable_logging()
set_logging("training.log", level=logging.INFO)

model_name = "distilbert-base-uncased"

# input and output paths
training_folder: Path = Path("../../policies/en/labeled")
annotation_schema_file: Path = Path("../../annotation_schema.json")
output_dir: Path = Path("../../models/en")

# read training data and annotation schema
training_files: list[list[RawEntry]] = read_training_data(training_folder)
schema: LabelSchema = read_annotation_schema(annotation_schema_file)

# define training configurations
configs = [
    ModelTrainingConfig(
        model_name=model_name,
        output_dir=output_dir / Path("context"),
        training_files=training_files,
        labels=schema.context,
        scope="context",
        content_topic=None,
        test_eval_split=0.2,
        oversampling_ratio=0.5,
        seed=SEED,
    ),
    ModelTrainingConfig(
        model_name=model_name,
        output_dir=output_dir / Path("topic"),
        training_files=training_files,
        labels=schema.topics,
        scope="topic",
        content_topic=None,
        test_eval_split=0.2,
        oversampling_ratio=0.5,
        seed=SEED,
    ),
    ModelTrainingConfig(
        model_name=model_name,
        output_dir=output_dir / Path("content") / Path("UserRights"),
        training_files=training_files,
        labels=schema.topicContents["UserRights"],
        scope="content",
        content_topic="UserRights",
        test_eval_split=0.2,
        oversampling_ratio=0.7,
        seed=SEED,
    ),
    # ....
]

# execute training for each configuration
for config in configs:
    config.execute_training()

```

### Defaults & Configurations

Several default configurations are provided for convenience.

#### **Model Configs**

These configurations define which models to use and what classification thresholds to apply.
The default model configurations can be imported from `privacy_policy_analyzer.analysis.DEFAULT_MODEL_CONFIGS`.
They use pre-trained models hosted on HuggingFace.

- [Context Classifier](https://huggingface.co/Wutterfly/roberta-privacy-policy-context)
- [Topic Classifier](https://huggingface.co/Wutterfly/privbert-privacy-policy-topic)
- Content Classifiers for each topic, e.g.:
  - [User Rights Content Classifier](https://huggingface.co/Wutterfly/privbert-privacy-policy-content-userrights)
  - ...

#### **Pattern Configs**

These pattern configurations define regular expressions to identify specific information in the privacy policy text, such as dates, durations and data types.
The default pattern configurations for English can be imported from `privacy_policy_analyzer.patterns.en`.
More languages and configurations can be added in the future or specified by the user.

#### **Splitter Configs**

These pattern configure how to split long text sections into smaller segments for analysis.
The default splitter configurations for English can be imported from `privacy_policy_analyzer.patterns.en.EN_SPLITTER_CONFIG`.
