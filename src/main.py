import os
import json
import random
import gradio as gr
from gradio import ChatMessage
from function_calling import functions, process_query_with_function_calls
import google.generativeai as genai
from dotenv import load_dotenv
import pymupdf4llm


# Initialization
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

print("Loading context...")
sphn_context = json.load(open("data/sphn_classes.json"))
sulo_context = json.load(open("data/sulo_data.json"))
sulo_mapping_context = json.load(open("data/sphn_to_sulo_mappings.json"))

# Path to your uploaded PDF
pdf_path = "data/sulo-paper-pages1-7-no-examples.pdf"

sulo_pdf_text: str = pymupdf4llm.to_markdown(pdf_path)
sulo_pdf_text = sulo_pdf_text.replace("March 2025", "")

print("Loading model...")

complete_instructions = f"""
Your primary task is to map a triple from one ontology into a ULO named SULO (simplified upper level ontology). 
I will give you the exact steps you need to execute to complete this task. 
Do not do more or less than asked in the instructions. 
The instructions will be given one at a time. 
Each of these instructions builds upon the others. 
Use the information from the previous steps to complete the task to the best of your abilities.
"""

llm_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=complete_instructions,
    tools=functions.values(),
    generation_config=genai.GenerationConfig(temperature=0.0),
)

instructions = [
    f"""Task I. Building Conceptual Context 
Think in real-world terms
Important notes: Think beyond how things are in a database. Consider the input as a real-world scenario and build your definitions based on a real-world context bound to the focal concept, rather than a digital record. Determine what real-world information the source class is intended to capture and how each property contributes to that goal.
Declare the focal concept
The class will be the central concept you will keep refining.
Create an initial working definition—brief and tentative.
Collect related terms
The provided focal class will have properties found in the provided JSON file.
If the exact class cannot be found, stop and notify the user
For each term and facet, do three micro-tasks
Linkage - a sentence on how this term interacts with or constrains the focal concept (why it matters).
Concise definition - a short description in plain language. This definition shouldn't be a direct general definition, but instead should be in the context of the focal class. The intention is to capture the purpose of the term and its purpose in the focal class.
Reasoning - a short phrase explaining how you arrived at that definition (e.g., industry practice, logical contrast, regulatory cue). 
Uncover deeper semantic layers
For any property that at first glance looks like a simple artifact (a code, URI, identifier), ask “What contextual role or feature within the focal concept does this proxy stand in for?” Produce two facets for each such term:
Surface artifact - what it literally is (e.g., a pseudonymized code).
Conceptual referent - what real-world function or contextual role does this artifact serve within the focal concept? (e.g., the role of a patient whose identity it preserves).
For each facet, go back to your micro-tasks and produce multiple definitions, reasoning, and linkages for each facet and flag them.
Iteratively refine the focal concept
After the terms have been defined, revisit the focal concept.
Weave the new attributes and relationships into a tighter, richer definition, ensuring every term is represented.
Keep the definition concise; remove redundancy.
Return and remember the final definition of the focal concept alongside the definitions of each term.
Here is the content of the JSON file: {sphn_context}
""",
    f"""Task II. Understanding SULO
Read the whole SULO paper to learn its motives and what it is expecting from mappings
Focus on section 4 of the SULO paper (classes, relations, and design patterns) and remember the information
Familiarize yourself with the sulo properties alongside their respective domain and range found in the provided JSON file.
Investigate the provided examples in the paper and understand the logic behind the mappings.
Note the important rule stating never to introduce new relations; reuse SULO’s object properties.
Remember the content from the provided files and notify the user when the task is complete; this information will be used in future tasks.
Here is the content of the SULO paper: {sulo_pdf_text}
Here is the content of SULO classes and properties: {sulo_context},
Here is the content of SULO example classifications: {sulo_mapping_context}""",
    """Task III.	Classify the input class and its properties
For these steps, remember to stick strictly to the SULO classes found from step 2.
Decide whether the focal class is a Process or an Object
Use SULO’s official definitions to choose one of these two top-level categories (process or object). The focal concept must be either a process or an object.
Generally, processes have a start or end date as part of their properties
The output will be the domain
Select candidate ranges for each property
For each property, review the conceptual context from Step I.
Identify all conceptual facets that have been flagged for that property
Map each facet to one or more SULO classes, but keep them together as a single property’s range.
In other words, a property’s range is a set of SULO classes, not a single class, so you capture every relevant facet under that one property name.
When mapping, focus on the linkage of each term/facet towards the focal concept, not its direct meaning. Ask: “In the story of the focal concept, what function does the range fulfil?”
Output: A list of SULO class(es) for each property, reflecting all its facets as the property’s unified range.
""",
    """Task IV. 	Determine the SULO relations
For each source property, use only the SULO object properties you determined in Step III.
Match the focal class (domain) to each SULO predicate and list the SULO class(es) you assigned as its range.
Do not introduce any new relations or classes—only reuse SULO's existing vocabulary.
If multiple ranges can be applied, take all of them into account.
""",
    """Task V. Determine and apply the SULO Design Patterns
Important note to keep in mind: multiple design patterns can apply to a single ontology. Using both PRO and SOLID in the same triple is not uncommon. If multiple ranges can be applied, merge them into a single multi-layered triple (i.e. PRO + SOLID in a single triple).
Direct mapping, based on the domain and range determined in step III, maps it using the SULO: relations. If the relation cannot be determined directly, continue.
If the domain is a process and the range is a role, apply the PRO design pattern according to the structure defined in the paper investigated in step 3.
If the range is a literal (SULO:informationObject), apply the SOLID design pattern according to the structure defined in the paper investigated in step 3.
The final output will always be a single RDF triple for each property. Make sure to have the correct TTL syntax for each triple. Preface the output with the classification of the input class""",
]


def full_pipeline(class_to_map: str) -> str:
    chat = llm_model.start_chat()
    
    # STEP 0: user’s class name    
    chat.send_message(f"The class I want to map is: {class_to_map}")
    
    # STEP 1–N: your internal tasks
    for step in instructions:
        print(f"Processing step: {step[:8]}")
        output = chat.send_message(step)
    
    # STEP N+1: ask the model to give the final mapping
    return output.text

# GUI
print("Starting Gradio UI...")
gr.Interface(
    fn=full_pipeline,
    inputs=gr.Textbox(label="Enter the SULO class to map"),
    outputs=gr.Textbox(label="SULO mapping result"),
    title="The Big Bad SULO Translator Bot",
    description="Enter a class once, and I'll do the rest.",
    example_labels=["Administrative Case", "Allergy"]
).launch()
