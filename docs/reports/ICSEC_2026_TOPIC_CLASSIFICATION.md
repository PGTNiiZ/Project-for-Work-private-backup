# ICSEC 2026 Topic Classification

## Scope and conclusion

This classification applies the revised Phase 11 rules to the implemented identity-resolution project. It uses repository evidence available on 2026-09-01 and distinguishes the pair-scoring model from the downstream genetic-algorithm decision policy.

**Primary Topic:** Evolutionary Computing

**Secondary Topics:** Artificial Intelligence; Machine Learning and Deep Learning; Natural Language Processing; Data and Knowledge Management

These five topics are sufficient to route the manuscript to reviewers who can evaluate its actual contribution. No topic outside the official ICSEC list is proposed.

## Recommended topics

| Topic | Priority | Evidence from Project | Why It Fits |
| ----- | -------- | --------------------- | ----------- |
| Evolutionary Computing | Primary | `pub_multi/src/genetic_optimizer.py` implements a deterministic elitist genetic optimizer; `experiments/code/run_feature_aware_ga_pipeline.py` defines GA genomes, validation optimization, decision thresholds, evidence groups, availability masks, and cost-based promotion gates. | The central methodological contribution is optimizing a post-model decision policy with evolutionary search. A reviewer in this area would find an explicit representation, constraints, fitness function, search procedure, and comparative evaluation target. |
| Artificial Intelligence | Secondary | The system performs automated cross-platform identity decisions, separates MATCH/REVIEW/NO_MATCH outcomes, combines heterogeneous evidence, and supports a human-review safety layer. | AI-based decision making is central to the proposed system, not incidental API usage. The topic is appropriate as a broad umbrella, while the more specific ML and evolutionary topics identify the main methods. |
| Machine Learning and Deep Learning | Secondary | The project trains and evaluates Gradient Boosting and logistic models over lexical, semantic, URL, location, social, stylometric, platform, and image features. It also uses SBERT-derived similarities and image-caption cross-signals; the project explicitly separates model weights from GA policy weights. | ML methodology, feature construction, model training, calibration, validation/test separation, and empirical metrics are meaningful parts of the research. The claim should remain precise: the work uses pretrained semantic representations but does not claim to develop or fine-tune a new deep model. |
| Natural Language Processing | Secondary | Name and bio processing includes Jaro/edit/token-sort similarities, TF-IDF and SBERT cosine similarity, mention/hashtag overlap, style features, and caption-to-text cross-signals. | Text understanding and semantic similarity materially affect entity matching and the evidence policy. NLP is therefore more than a superficial keyword; however, it remains secondary because the paper’s main novelty is decision optimization rather than a new language model. |
| Data and Knowledge Management | Secondary | `docs/plans/GA_FEATURE_AWARE_DECISIONING_PLAN_TH.md` specifies a decisioning feature cache, feature manifest, coverage/reliability audit, availability masks, structured evidence groups, and reproducible validation/test artifacts. | The system’s contribution includes managing heterogeneous, partially missing identity evidence and preserving provenance-like coverage/reliability information for decisions. This is a significant structured-evidence and data-handling component, though not the primary algorithmic contribution. |

## Topics not recommended

| Topic Not Recommended | Why |
| --------------------- | --- |
| Computer in Education | No learning, teaching, assessment, educational outcome, or learning-support problem is studied. |
| Simulation and Modeling | The experiments evaluate models and decision policies on labeled pairs; simulation is not the proposed methodology. |
| Human Machine Interface | A review queue exists, but human interaction design or user-interface effectiveness is not scientifically evaluated. |
| Software Engineering | The repository contains engineering and tests, but architecture, maintainability, testing methodology, or software quality is not the research contribution. |
| Computer and Internet Application | The system uses cross-platform/social data, but this broad application label is less informative than the algorithmic topics and would not improve reviewer alignment. |
| Intelligent Systems | The system is intelligent in a general sense, but it does not require multiple adaptive, autonomous, or recommendation mechanisms beyond the explicitly covered AI/ML/GA methods. |
| Machine Intelligence and Applications | The project has a practical CRM/entity-resolution application, but selecting this broad category would overlap with the more technically diagnostic topics and dilute reviewer targeting. |
| Computer Vision and Image Processing | Image-derived features are present, but repository evidence says image coverage is limited and image context contributes only a small amount; no vision methodology is the main contribution. |
| Image Processing | Image statistics, perceptual hashes, and caption signals are supporting features, not the central research problem or evaluation. |
| Pattern Recognition | Entity matching is pattern-oriented, but this category is too generic when the manuscript has stronger, method-specific coverage under evolutionary computing and machine learning. |
| Knowledge Discovery | The project applies known evidence features to supervised matching and policy optimization; it does not primarily discover new knowledge or latent patterns as the research objective. |
| Computer Networks / Wireless Networks and Communications | Network protocols, routing, wireless communication, and network performance are outside the research problem. |
| Computer Architecture / High Performance Computing / Distributed Computing and Grid Computing | Compute efficiency is relevant operationally, but no architecture, distributed algorithm, or HPC method is evaluated as a research contribution. |
| Cryptography and Security / Digital Forensics | Privacy and false-merge risk are discussed, but there is no cryptographic protocol, security analysis, forensic acquisition, or forensic inference methodology. |
| Acoustics Speech and Signal Processing / Digital Signal Processing | The inputs are profile text, metadata, and optional images; speech or signal-processing methodology is absent. |
| Bioinformatics / Medical Image Processing | The project is not biomedical and does not process medical data or medical images. |
| Computer Graphics / Robotics and Automation / Mobile Computing / Quantum Computing | None is part of the implemented research problem or evaluation. |
| Semantic Web Ontology / Knowledge Management | The project manages structured evidence, but it does not build ontologies or study organizational knowledge-management processes. |
| Programming Language | No programming-language design, compiler, type system, or language semantics contribution is made. |

## Reviewer-alignment check

For each selected topic, the manuscript can provide a method and evaluation that a specialist reviewer can assess: GA representation and fitness for Evolutionary Computing; trained models and metrics for ML; semantic/text features for NLP; automated evidence-based decisions for AI; and feature-cache, missingness, coverage, and reliability controls for Data and Knowledge Management.

The manuscript should avoid presenting image processing, human-in-the-loop interaction, or software architecture as independent contributions because the current evidence is insufficient for those specialist reviewer expectations.

## Evidence limitations

The strongest current results cover labeled candidate pairs and a feature-aware GA validation/test workflow. The repository itself warns that some historical feature-aware runs are sensitivity analyses rather than a current production winner, and that image evidence has limited coverage. The final paper must preserve those boundaries and use `[EXPERIMENT REQUIRED]` where a topic-specific claim is not supported by a sealed experiment.

### Repository sources

- [Feature-aware GA plan](../plans/GA_FEATURE_AWARE_DECISIONING_PLAN_TH.md)
- [Feature-aware GA pipeline](../../experiments/code/run_feature_aware_ga_pipeline.py)
- [Genetic optimizer](../../pub_multi/src/genetic_optimizer.py)
- [Project findings and improvement report](PROJECT_FINDINGS_AND_IMPROVEMENT.md)
- [Project presentation speaker script](../../presentation/PROJECT_REPORT_SPEAKER_SCRIPT_TH.md)
