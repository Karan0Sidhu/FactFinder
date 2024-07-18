# Import Libraries
import os
from crewai import Agent, Task, Crew
from tqdm import tqdm
import re
import json

# Set up OPEN AI key
os.environ["OPENAI_API_KEY"] = ""


def abstract_to_triple(abstract):
    # Define predicates
    predicates = """
        1) Environmental processes (A series of events that occur naturally in the environment and not within an organism)
        2) Biological processes (Biological or chemical events or a series thereof, leading to a known function or end-product within an organism)
        3) Industrial processes (A series of molecular events that involve at least one synthetic reaction)
        4) Adverse biological roles (The biological function of a chemical that results in harmful effect for an organism. This can include biochemical effects of non-endogenous chemicals, which are also assigned an industrial application such as pharmaceuticals)
        5) Normal biological roles (The biological function of a chemical. The biological role answers the question how a chemical is involved in molecular processes in an organism. This can include biochemical effects of non-endogenous chemicals, which are also assigned an industrial application such as pharmaceuticals. The biological role is limited to cellular levls, and will not include role at system process level, such as a chemical which has a role in a disease.)
        6) Environmental roles (A direct or indirect function of chemical product or process which affect the components of the environment)
        7) Industrial applications (The assumed function of a chemical is utilized in any kind of industry, including agriculture, pharmaceutical, medical, and construction)
        8) Low concentration Health effect (Low concentration of chemical effect to humans)
        9) High concentration Health effect (High concentration of chemical effect to humans)
        10) No Exposure Health effect (Naving none of this chemicals effect to humans)
        11) Exposure Health effect (If exposed to chemical effect to humans)
        12) Organoleptic effects (Human sensual perception of chemical stimuli)
        13) Sources (Natural or synthetic origin of a chemical)
        14) Biological locations (The physiological origin within an organism, including anatomical compnents, biofluids and excreta)
        15) Routes of exposure (A mean by which a chemical agent comes in contact with an organism, either under intended or unintended circumstances)
    """

    # Chemical parsing agent
    chemical_parser = Agent(
        role='Chemical and Metabolite Extractor',
        goal='Search for key chemical and metabolic biomarkers mentioned in a block of given text.',
        backstory='You are a professional working in a chain of scientists to help extend a chemical database. Your role in this chain of work is to find all the chemical compounds mentioned in a block of text from a research article.',
        verbose=True,
        allow_deligation=False
    )

    parser_task = Task(
        description=f"""Extract key chemical and metabolic biomarkers from the segment of text.
                    Only extract chemical compounds found within the segment of the text.
                    Your final answer should be a list of chemicals found in the following format: ['chemical 1', 'chemical 2', 'biomarker 3']
                    Text: {abstract}""",
        expected_output="A list of key chemical compounds mentioned in the text.",
        agent=chemical_parser
    )

    # Triplet extraction agent
    triplet_extractor = Agent(
        role='Relation and Predicate Mapper',
        goal='Extract semantic triples using the identified predicates and the key chemcial compounds.',
        backstory='As an integral part of a data extraction team focusing on scientific texts, your task is to analyze the context around identified chemicals and correctly map their interactions and functions within the environment or biological systems.',
        verbose=True,
        allow_deligation=False
    )

    triplet_task = Task(
        description=f"""Extract semantic triplets from the text using predefined predicates: {predicates}.
                    Use the identified chemical compounds as subjects, and map them to suitable objects and predicates.
                    Format of the output should be [['subject', 'predicate', 'object'], ['another subject', 'predicate', 'object']]. Ensure the predicates are from the predefined list.
                    Text: {abstract}""",
        expected_output="A list of lists where each list contains a key chemical compound that was previous found, and the prediates are all from the predefined predicate list.",
        agent=triplet_extractor
    )

    # Verification agent
    verification_agent = Agent(
        role='Data Integrity and Format Validator',
        goal='Ensure the triplets are correctly formatted and use only the predefined predicates.',
        backstory='You act as a quality control expert, checking the outputs of data extraction processes to guarantee accuracy and adherence to specifications in a high-stakes research environment.',
        verbose=True,
        allow_deligation=False
    )

    verification_task = Task(
        description=f"""Verify that for each extracted triple, the subject is present in the text, and the predicate used is ONLY from the following predefined list: {predicates}.
                    Ensure that the output is a list of lists in the following format: [['subject', 'predicate', 'object'], ['another subject', 'predicate', 'object']]
                    Text: {abstract}""",
        expected_output="A list of lists in the correct format.",
        agent=verification_agent
    )


    # Create the Crew
    crew = Crew(
        agents=[chemical_parser, triplet_extractor, verification_agent],
        tasks=[parser_task, triplet_task, verification_task],
        verbose=2)

    # Begin processing
    result = crew.kickoff()
    return result   

def load_jsonl_dataset(file_path):
    dataset = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line.strip())
            dataset.append(data)
    return dataset

if __name__ == "__main__":  
    testing_set = "/home/wishartlab/TMIC/Data/Training_Data/213_Data_Total/44_Testing.jsonl"
    output_path = "/home/wishartlab/TMIC/test.jsonl"
    test_dataset = load_jsonl_dataset(testing_set)

    with open(output_path, 'w') as outfile:
        for data in tqdm(testing_set):
            abstract = data['input']
            generated_output = abstract_to_triple(abstract)


    # Initally set valid as False
            valid = False

            output = []
            try:
                pattern = r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\]'
                extracted_list = re.findall(pattern, generated_output, re.MULTILINE)
                my_list = [triple for triple in extracted_list if 'NA' not in triple]
                output = my_list
                valid = True

            except (SyntaxError, ValueError) as e:
                #failed_output += 1
                print(generated_output)

            # Save the {'input': abstract, 'output': output} pair to JSONL
            json.dump({'input': abstract, 'output':output, 'output_complete': generated_output, 'valid':valid}, outfile)
            outfile.write('\n')