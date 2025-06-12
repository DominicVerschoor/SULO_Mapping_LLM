# SULO Mapping with LLM

This repository presents a hybrid pipeline for semantic ontology mapping between the [Swiss Personalized Health Network (SPHN)](https://sphn.ch) schema and the [SULO](https://w3id.org/sulo) (Simplified Upper-Level Ontology). It supports both forward (SPHN → SULO) and reverse (SULO → SPHN) transformations using Large Language Models (LLMs), SPARQL, and SHACL validation. The pipeline was tested across two SPHN schema versions: `2023.02` and `2025.01`.

Features
-  Bidirectional mapping (SPHN → SULO and SULO → SPHN)
- LLM-guided reasoning via structured prompting and in-context learning
- Schema-agnostic mapping compatible with multiple SPHN versions
- SHACL validation of resulting RDF graphs
- Tkinter GUI for domain expert involvement
- Gradio interface for querying LLMs interactively

🧪 Usage
🔹 LLM Mapping Interface (Gradio)

The LLM processes multi-step instructions and outputs RDF triples mapped to SULO

🔹 Manual Mapping Tool (Tkinter GUI)

Provides class/property suggestions and LLM-generated justifications

🔹 SPARQL Transformations
Edit and run SPARQL queries from:

mappings/queries/sphn2023_to_sulo.rq

sulo_bidirectionality/sulo_to_sphn_construct.rq

Or test interactively in the Jupyter notebooks provided.

🔹 SHACL Validation
Use pySHACL to validate reverse-transformed SPHN RDF graphs:

Datasets & Examples

turtles/sphn_instance_administrativecase_v2025.ttl — original SPHN instance

mappings/output/administrative_case_transformed_sulo.ttl — SULO-mapped version

sulo_bidirectionality/sulo2sphnv2025.ttl — reconstructed SPHN RDF

Experiments & Evaluation
The system was tested on 5 representative SPHN classes:

AdministrativeCase, Allergy, DrugPrescription, ProblemCondition, Diagnosis

Each class was mapped from both SPHN 2023.02 and 2025.01 to SULO using SPARQL queries guided by LLM-inferred relations. Reverse mappings and SHACL validation were used to ensure semantic integrity.
