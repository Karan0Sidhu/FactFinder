# Import libraries
import re
import json
from tqdm import tqdm
from openai import OpenAI

# API key
OPENAI_KEY = ""

# InitaliE API
class API:
    def __init__(self, model, test_dataset, output_path, prompt):
        self.model = model
        self.client = OpenAI(api_key=OPENAI_KEY)
        self.test_dataset = test_dataset
        self.output = output_path
        self.prompt = prompt

    def run(self):
        with open(self.output, 'w') as outfile:
            # Load the data
            for data in tqdm(self.test_dataset):
                abstract = data['input']
                ground_truth = data['output']

                # Generate a singular prompt
                text = self.prompt + abstract

                # Run through the model
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": text
                        },
                    ]
                )
        
                generated_output = response.choices[0].message.content.strip()

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
                    failed_output += 1
                    print(generated_output)

                # Save the {'input': abstract, 'output': output} pair to JSONL
                json.dump({'input': abstract, 'output':output, 'output_complete': generated_output, 'valid':valid}, outfile)
                outfile.write('\n')

# Load JSONL dataset
def load_jsonl_dataset(file_path):
    dataset = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line.strip())
            dataset.append(data)
    return dataset

if __name__ == "__main__":
    # Initialize variables
    testing_set = "/home/wishartlab/TMIC/Data/Training_Data/213_Data_Total/44_Testing.jsonl"
    output_path = "/home/wishartlab/TMIC/test.jsonl"
    model = "gpt-4o"
    prompt = """You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph. 
                extract semantic triples using the following predicates (the definition for each predicate has been defined in the corresponding parentheses):

                1) Environmental processes  (A series of events that occur naturally in the environment and not within an organism)
                2) Biological processes (Naturally-occurring molecular events or a series thereof, leading to a known function or end-product)
                3) Industrial processes (A series of molecular events that involve at least one synthetic reaction.)
                4) Adverse biological roles (The biological function of a chemical that results in harmful effect for an organism. This can include biochemical effects of non-endogenous chemicals, which are also assigned an industrial application such as pharmaceuticals)
                5) Normal biological roles (The biological function of a chemical. The biological role answers the question how a chemical is involved in molecular processes in an organism. This can include biochemical effects of non-endogenous chemicals, which are also assigned an industrial application such as pharmaceuticals. The biological role is limited to cellular levels, and will not include role at system process level, such as a chemical which has a role in a disease)
                6) Environmental roles  (A direct or indirect function of chemical product or process which affect the components of the environment)
                7) Industrial applications (The assumed function of a chemical is utilized in any kind of industry, including agriculture, pharmaceutical, medical, and construction)
                8) Low concentration Health effect ( low concentration of chemical effect to humans)
                9) High concentration Health effect ( high concentration of chemical effect to humans)
                10) No Exposure Health effect ( having none of this chemicals effect to humans)
                11) Exposure Health effect ( if exposed to chemical effect to humans)
                12) Organoleptic effects (Human sensual perception of chemical stimuli)
                13) Sources (Natural or synthetic origin of a chemical)
                14) Biological locations (The physiological origin within an organism, including anatomical components, biofluids and excreta)
                15) Routes of exposure (A mean by which a chemical agent comes in contact with an organism, either under intended or unintended circumstances)

                follow the following rules:
                1. Only include triples where the subject is a chemical/metabolite. 

                2. Try to Keep a short Object for the triple, the triplet is a fact.

                3. It is ok to output nothing. 

                4. Output the triples in the format [[“subject”, “predicate”, “object”],[“subject”, “predicate”, “object”]]

                5. in the triple Only use full names for the subject, predicate and object.

                6.Coreference Resolution
                    - **Maintain Entity Consistency**: When extracting entities, it's vital to ensure consistency.
                    If an entity, such as "Tyrosine", is mentioned multiple times in the text but is referred to by different names or pronouns (e.g., "Tyr", "he"), 
                    always use the most complete identifier for that entity throughout the knowledge graph. In this example, use "Tyrosine" as the entity ID.  
                    Remember, the knowledge graph should be coherent and easily understandable, so maintaining consistency in entity references is crucial. 

                7. do not include triples with the word "and" in it, rather split the triplet into 2 triplets.

                General Guidelines:
                Subject: Chemical the sentence is about.
                Predicate: Identify what action or state the subject is associated with from the list of predicates above.
                Object: Identify what is receiving the action or associated with the state.

                only extract triples from the text provided

                output triples in a format of a list of 3 string to make it a string please put the items in the list in a quote

                Tip: Make sure to answer in the correct format
                 
                
                Here is the article:
    """

    # Load Test set
    test_dataset = load_jsonl_dataset(testing_set)

    # Set up API
    client = API(model, test_dataset, output_path, prompt)

    # Run the test
    client.run()


