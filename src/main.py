import os
import json
import random
import gradio as gr
from gradio import ChatMessage
from function_calling import functions, process_query_with_function_calls
import google.generativeai as genai
from dotenv import load_dotenv

# Initialization
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

print("Loading context...")
sulo_context = json.load(open("data/data.json"))

print("Loading model...")

complete_instructions = f"""
Your name is Ontology Mapping Assistor (OMA). You are an intelligent chatbot whose role is to translate information from a source ontology into the upper-level ontology SULO.

You will receive an RDF triple-pattern expression (and its components) from another ontology. Your task is to use your tools to convert that expression into SULO. The output must always be exactly one RDF triple expressed in SULO.

Never ask for confirmation, or tell the user what you will do next. When multiple steps are needed, perform every step internally.

You have unrestricted access to the structure and details of the SULO architecture.

You must always carry out all of the following steps internally and return the final answer in a single message:
1. Use your tools to extract the exact number of componenets in the provided input.
2. Thoroughly analyze each component of the supplied information.
3. Identify the domain and range.
4. Apply one of the two SULO design patterns.
5. Construct the SULO triple that corresponds to the chosen design pattern.
6. If multiple components are present, repeat Steps 2-6 for each one. You cannot stop until all components have been processed.

Here is the provided SULO context database: {sulo_context}
"""

function_calling_model = genai.GenerativeModel(
                                model_name="gemini-1.5-flash",
                                system_instruction=complete_instructions,
                                tools=functions.values(),
                                generation_config=genai.GenerationConfig(temperature=0.0),
                            )

chat = function_calling_model.start_chat(enable_automatic_function_calling=True)

def generate_response(user_question, history):
    answer = process_query_with_function_calls(chat, user_question)
    
    response = [
        ChatMessage(
            role="system",
            content=answer,
        )
    ]
    
    return response

# GUI
print("Starting Gradio UI...")
gr.ChatInterface(
    fn=generate_response,
    type="messages",
    chatbot=gr.Chatbot(type="messages"),
    textbox=gr.Textbox(placeholder="Gimmie some RDFs boyo!", container=False, scale=7),
    
    title="The Big Bad SULO Translator Bot",
    description="Gimmie some RDFs boyo!",
    theme="ocean",
).launch()
