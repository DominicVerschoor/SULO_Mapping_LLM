import json

def get_design_pattern(domain: str, range: str) -> str:
    """This function possesses complete knowledge of the SULO design patterns. Based on the provided domain and range, it returns the correct design pattern and guidance on how to apply it.

    Args:
    domain: The domain of the property (the predicate's context). Supply a single string starting with sulo: followed by the domain name. The domain must be one of the SULO classes in the context database provided; include no extra text.
    range:The range of the property (the entity being identified). Supply a single string starting with sulo: followed by the range name. The range must be one of the SULO classes in the context database provided; include no extra text.

    Returns:
      One of:
        - 'SOLID'   : if range is a literal datatype or coded value.
        - 'PRO'     : if domain is a Process and range is a Role or entity participating in a process.
        - 'DIRECT'  : otherwise (static entities, spatial links, simple references).
    """

    outputs = {
        "SOLID": """The SOLID pattern uses a single functional datatype property, hasValue, to as 
            to assign a literal value to an instance of an InformationObject. This pattern precludes
            the introduction of domain-specific datatype properties such as hasTemperature or
            hasAdmissionDateTime by reifying these data relations as classes (e.g., Temperature,
            DateTime) under InformationObject. Thus, SOLID pushes the semantics out of data
            properties and into the classes, where they can be better described through class expressions. 
            Moreover, it simplifies representations, as it is always predictable where any stored
            value will be in the range of hasValue of some information object.""",
            
        "PRO": """The Process-Role-Object (PRO) ontology design pattern provides a structured
            way to represent how entities participate in processes through specific roles. It is defined as follows:
            Process hasParticipant Role isFeatureOf Object.
            PRO specifies the roles that are necessary and specific to each object and which are direct participants in the process.
            We recover the participation of the object in the process by inference through the
            role chain hasParticipant o isFeatureOf -> hasParticipant.""",
        
        "DIRECT": """When neither SOLID nor PRO applies, link entities directly utilizing the 
            respective SULO classes and properties to create a RDF triple. In most common cases, this will occur in
            Time values, or Spatial values, where the domain is OWL:Thing""",
    }

    print("Getting design pattern...")
    print(f"Domain: {domain}, Range: {range}")
    # Domain is a Process
    if domain == "sulo:Process":
        print('PRO Pattern')
        print()
        return outputs["PRO"]

    # Range is a InformationObject?
    if range == "sulo:InformationObject":
        print('SOLID Pattern')
        print()
        return outputs["SOLID"]

    print('DIRECT Pattern')
    print()
    # Otherwise, link entities directly
    return outputs["DIRECT"]

def get_number_of_components(user_input: str) -> int:
    """Returns the number of compoenets in the user input. This is used to determine how many times the design pattern should be applied.
    Args:
        user_input: The user input string containing the components.
        """
        
    count = user_input.count('?a')
    print("Couting {count} components...")
    return count

functions = {
    "get_design_pattern": get_design_pattern,
    "get_number_of_components": get_number_of_components,
}


def process_query_with_function_calls(chat, user_question):
    response = chat.send_message(user_question)
    return response.text
