SYSTEM_INSTRUCTION = [
    # Agent Role and Information Source
    "You are a document processing agent specializing in RFP analysis, equipment identification, and synergy opportunities. You rely exclusively on the documents provided in each session (e.g., MISCO, Shape, and Southwest) as your authoritative source for answering questions, extracting information, and generating outputs.",
    "Use only information found directly in the provided documents. Avoid inferring details that aren't explicitly present in the documents.",

    # Key Features of the Agent
    "Your Key Features include:",
    "* Persistent Question Answering",
    "* Document Summarization",
    "* Key Phrase Extraction",
    "* Named Entity Recognition",
    "* JSON File Generation for Excel and DOCX Creation",
    "* Synergy Identification for specific brands and product categories",

    # Instructions for Handling Excel and DOCX Generations
    "For requests to 'extract to bluesheet', 'extract to excel', 'extract to spreadsheet', 'extract to .xlsx', or 'extract to .csv', generate a JSON format string. This JSON will be used to create a well-formatted Excel file.",
    "For document analysis outputs (e.g., '{Project Name} – Basic RFP Bid Analysis'), create a JSON file to generate a .docx file with structured sections as specified, directly pulling content from the uploaded RFP.",
    "Clear instructions on generating JSON files for document creation will be provided in the prompts.",

    # Handling Missing Data
    "If required data is missing from the document, mark it as 'Not specified' in the output file.",

    # HTML Formatting for Non-JSON Text Outputs
    "For text outputs that are not in JSON format, provide them in HTML format (except explicitly specified in prompt not to):",
    "Use the following tags for easy rendering in a chat window:",
    "* <b> for bold text",
    "* <h2> for headings",
    "* <ul> and <li> for bullet lists",
    "* <ol> for numbered lists",

    # Unsupported File Types
    "If asked to generate a document type other than Excel or Word, respond with: 'Sorry, I can't help with that.'"
]




prompt_template_one = """
<INSTRUCTIONS>
You are tasked with generating JSON data that represents the structure of a `.docx` document titled "<Project Name> – Basic RFP Bid Analysis". Replace <Project Name> with the name of the project (ensure it follows file naming conventions). This document will summarize essential project information as provided in the uploaded RFP. Each section should be formatted with clear headings and proper spacing for readability.
If user specifies the project name in <PROJECT_NAME>, extract and use that name in the title. Otherwise, use the project name extracted from the RFP.

<FORMATTING GUIDELINES>
1. Title: Set the document title as "[Project Name] - RFP Analysis" using the project name extracted from the RFP.
2. Use the Blue_Sheet_Bid_Document_Template.pdf as a reference for formatting.
3. Use a header for each main section, with bold font for section names and sub-section names (e.g., "Bid Information:", "Funding Sources:").
4. Format content with appropriate spacing and alignment to ensure clarity.
5. Populate each field directly with extracted data from the RFP. If data is not available, label it as "Not specified". Make sure document is thoroughly scanned before using the "Not specified" phrase.
6. If data is not found, find a description that can suit data to be extracted that was not found.

<ACTION>
Parse and extract the following sections from the RFP document and format them as JSON according to this schema:

[{{"fileName": "<Project Name> - RFP Analysis.docx"}},
{{"type": "heading", "text": "<section title>", "fontSize": <font size>, "level": <heading level>}},
{{"type": "paragraph", "text": "<section content>", "fontSize": <font size>}},
...]

The sections are as follows:

1. Project Information:
   - Project Name
   - Location
   - Owner/Agency
   - Engineer or Consulting Firm (including contact information if available)

2. Bid Information:
   - Bid Number
   - Bid Date and Time
   - Pre-Bid Date, Time, and Type (mandatory or optional)

3. Funding Sources:
   - List the funding source(s) provided in the RFP (Federal, State, Local, Private, Turnkey, P3, or Other)

4. Project Scope:
   - Summarize the project's scope of work as described in the RFP, including major components or requirements.

5. Contractual Information:
   - Job Completion Date
   - Bid Acceptance Period
   - Guarantee Percentage
   - Construction Schedule (working days)
   - Estimated Award Date
   - Liquidated Damages (daily penalty cost)

6. Bid Conditions:
   - Listing Form requirement
   - Base Bid requirement
   - Substitutes Allowed (yes/no) with related comments
   - Or-Equals Accepted (yes/no) with related comments

<OUTPUT>
Make sure only valid JSON is generated with no errors.
Title: "<Project Name> - RFP Analysis"
Use the project name from the RFP as the title.
Extraction Guidelines:

Territory: [Determine the applicable territory based on the project location, such as Northern California, Southern California, etc. Match this territory with the sales or service regions defined by the organization].
Project Information:

Project Name: [Insert Project Name from RFP]
Location: [Insert project location, including city, county, and state]
Owner/Agency: [Insert name of the owner or agency managing the project]
Consulting / Engineer: [Insert name of the consulting or engineering firm overseeing the project]
Consulting Firm Contact: [Insert contact information if available, or any relevant details provided in the RFP]
Bid Information:

Bid Number: [Insert bid number if provided]
Bid Date and Time: [Insert the date and time for bid submission]
Pre-Bid Date: [Insert the date and details of any pre-bid meetings or conferences]
Funding Sources:
[List the funding sources as specified in the RFP, such as Federal, State, Local, Private, etc.]

Project Scope:
Scope of Work: [Summarize the project scope. Explain the individual key components including major components like infrastructure, construction, or system installation, etc described in the RFP]

Contractual Information:

Job Completion Date: [Insert the number of working days or the expected completion timeline]
Bid Acceptance Period: [Insert the duration for which the bid is valid. Look carefully for any specific bid acceptance period mentioned]
Guarantee Percentage: [Insert any guarantee or performance bond percentage required. Look for any specific percentage mentioned in the RFP]
Construction Schedule (working days): [Insert the number of working days as specified. Look for any specific construction schedule mentioned]
Estimated Award Date: [Insert the estimated date for bid award as specified in the RFP]
Liquidated Damages (daily penanlty cost): [Insert the daily penalty or liquidated damages clause if stated]

Bid Conditions:

Listing Form Requirement: [Describe subcontractor listing requirements, including thresholds and categories]
Base Bid Requirement: [Detail any base bid requirements, including forms and submission guidelines]
Substitutes Allowed: [Indicate whether material or product substitutions are allowed and under what conditions]
Or-Equals Accepted: [Do a detiled analysis and indicate and describe whether "or-equal" products or brands are accepted and describe the approval process]

<NOTE> For each extracted data, include a description.
<PROJECT_NAME>{project_name}</PROJECT_NAME>
"""

prompt_template_two = """
<INSTRUCTIONS>
You are tasked with performing an initial equipment identification and MISCO analysis. Using the RFP document provided by the user and MISCO Water Products, identify relevant equipment sections that match MISCO’s brands, product categories, and technologies. Your response should be clear, concise, and formatted for easy readability.

<FORMATTING GUIDELINES>
1. Begin with a statement confirming analysis completion, e.g., "Based on the provided RFP and MISCO’s product categories and brands, the following sections and equipment are relevant to MISCO:"
2. List and explain in details each identified section and corresponding equipment description from the RFP, ensuring it aligns with MISCO’s represented brands and technologies.
3. Use bullet points or numbered lists for each item, with clear labels like "Spec Section:" and "Equipment Description:".
4. Output should be in html format:
[
   "The html output should be in format for easy rendering in chat window. Use html elements instead of '*' and '#'",
   "use b tag for bold text",
   "use h2 for headings",
   "use ul for bullet lists",
   "use li for each list item",
   "use ol for numbers list"
]

<ACTION>
To analyze the RFP and match it with MISCO-represented brands and product categories, here’s a step-by-step approach:

1. **Gather Information**:
   - Obtain the RFP document and the MISCO water products text.
   - Make sure you have access to the predefined list of MISCO-represented brands, product categories, and specific technologies.

2. **Review and Extract Key Terms**:
   - Scan through the RFP to identify relevant specification sections and keywords related to MISCO’s product categories.
   - Extract terms related to water products, technologies, equipment, and brands mentioned in the RFP.

3. **Cross-Reference with MISCO's Product Information**:
   - Go through the MISCO water products text to locate brands, product categories, and technologies.
   - List out each product category, brand, and technology in a structured format for easy reference.

4. **Identify Relevant RFP Sections**:
   - Match each section of the RFP with corresponding MISCO product categories and brands.
   - Use keywords or phrases from both the RFP and MISCO information to make relevant connections.

5. **List Relevant Equipment and Descriptions**:
   - For each RFP section, display the specific MISCO-represented brands and equipment that align with the requirements.
   - Provide descriptions of each equipment piece as listed in the MISCO water products text, including features or specifications that are particularly relevant.

6. **Create a Summary Table or List**:
   - Organize the information following the description in <FORMATTING_GUIDELINES> and <OUTPUT>
   - Include detailed information to ensure clear alignment between the RFP requirements and MISCO products.

7. **Review for Completeness**:
   - Verify that all sections of the RFP have been matched with applicable MISCO products.
   - Ensure that all relevant equipment descriptions are comprehensive and accurate.

8. **Present the Final Analysis**:
   - Present the analysis in a format that is easy to read, with clear headings for each RFP section.
   - Provide any additional recommendations or notes regarding potential alignments between the RFP requirements and MISCO offerings.

<OUTPUT>
Example output format:
"Based on your provided RFP and MISCO's product categories and brands below, the following sections and equipment seem relevant to MISCO:"
• Spec Section: [specification number, e.g., "43 41 43"]
  Equipment Description: [brief description of equipment, e.g., "Fine Bubble Diffusers"]
• Spec Section: [another specification number]
  Equipment Description: [another equipment description]

<USER_RESPONSE>{response}</USER_RESPONSE>
If the user replies with "yes" or an affirmation, proceed with the extraction and analysis and display the output in the format above. If the user responds with "no" or a similar negative, respond with "Okay, I will not proceed with the analysis for MISCO."
"""

prompt_template_three = """
<INSTRUCTIONS>
You are tasked with identifying synergy opportunities. Analyze the RFP for potential opportunities for the following companies: 'Shape’s Represented Manufacturers and Categories' and 'Southwest Valve Manufacturers and Product Categories'  to identify relevant sections and equipment. Respond with a formatted summary of potential synergy opportunities, aligning each identified item with the specific companies and product categories.

<FORMATTING GUIDELINES>
1. Begin with a statement, e.g., "Based on the provided RFP and product categories from Shape and Southwest Valve, the following synergy opportunities are identified:"
2. Use bullet points for each synergy item, with labels like "Spec Section:" and "Relevant Equipment:".
3. Organize findings by company (Shape and Southwest Valve), listing relevant product categories and equipment in each section.
4. If no relevant synergies are found for either company, state "No relevant synergies identified for Shape or Southwest Valve."
5. Output should be in html format: 
[
   "The html outmat should be in format for easy rendering in chat window. Use html elements instead of '*' and '#'",
   "use b tag for bold text",
   "use h2 for headings",
   "use ul for bullet lists",
   "use li for each list item",
   "use ol for numbers list"
]

<ACTION>
1. Analyze the RFP for references to equipment and technologies that match Shape’s and Southwest Valve's represented product categories.
2. For each identified match, list the relevant sections and equipment descriptions.
3. Structure output to clearly show synergy opportunities for Shape and Southwest Valve, based on the client's specifications.

<OUTPUT>
Example output format:
"Here are potential synergy opportunities for UFT's sister companies, Shape, and Southwest Valve based on the RFP: [List of identified sections and relevant equipment from UFT’s sister companies, Shape, and Southwest Valve]."

Shape
• Spec Section: [specification number, e.g., "45 12 30"]
  Relevant Equipment: [equipment name and description, e.g., "Variable Frequency Drives by ABB"]

• Spec Section: [another specification number]
  Relevant Equipment: [another equipment description]

Southwest Valve
• Spec Section: [specification number, e.g., "41 22 14"]
  Relevant Equipment: [equipment name and description, e.g., "Butterfly Valves (Metal-Seated)"]

<USER_RESPONSE>{response}</USER_RESPONSE>
If the user replies with "yes" or an affirmation, proceed with the analysis for synergy opportunities, using the RFP, Shape, and Southwest Valve product categories. Display the results as shown in the format above. If the user replies with "no" or a similar response, confirm by saying "Okay, I will not proceed with the synergy analysis for Shape and Southwest Valve."
"""

prompt_template_four = """
<INSTRUCTIONS>
Generate JSON output to create an Excel document draft based on the structure of "Blue Sheet Template 2024.txt" (which is a .csv file converted to .txt) This JSON should represent the data for three separate worksheets—one each for MISCO, Shape, and Southwest Valve. Each worksheet should be structured as a list of dictionaries, where each dictionary represents a row with key-value pairs for column headers and cell values.

<JSON SCHEMA>
Your JSON output should have the following structure:
{
    "document_name": "<Project Name> – Bluesheet Draft.xlsx",
    "MISCO": [
        { "Spec Section": "...", "Equipment/Item Description": "...", "Named Manufacturers": "...", "Represented Company": "...", "Contact Information": "...", "Product Specifications": "..." },
        ...
    ],
    "Shape": [
        { "Spec Section": "...", "Equipment/Item Description": "...", "Named Manufacturers": "...", "Represented Company": "...", "Contact Information": "...", "Product Specifications": "..." },
        ...
    ],
    "Southwest Valve": [
        { "Spec Section": "...", "Equipment/Item Description": "...", "Named Manufacturers": "...", "Represented Company": "...", "Contact Information": "...", "Product Specifications": "..." },
        ...
    ]
}

<FORMATTING GUIDELINES>
1. Provide three worksheets with headers (e.g., Spec Section, Equipment/Item Description, Named Manufacturers, Represented Company, Contact Information, Product Specifications).
2. Each row should be formatted as a dictionary entry with the appropriate data extracted from the RFP.
3. For each worksheet (MISCO, Shape, Southwest Valve):
   - Include fields for spec sections, equipment descriptions, manufacturers, represented companies, and contacts.
   - Extract data based on relevance for each company, and if data is missing, label as "Not specified".
   - Example row for JSON entry:
      { "Spec Section": "33 40 00", "Equipment/Item Description": "Valve", "Named Manufacturers": "Brand A, Brand B", "Represented Company": "MISCO", "Contact Information": "Sandy Clarke, sclarke@miscowater.com", "Product Specifications": "Max pressure: 100 PSI" }
<ACTION>
Generate a draft bluesheet in Excel format (should come in JSON format as specified in FORMATTING_GUIDELINES and JSON_SCHEMA) using the format in the attached "Blue Sheet Template 2024.txt" with the following details. (You would need three sheets, one each for MISCO, Shape and Southwest Valve):
1.	Spec Section: Identified from the RFP, relevant to MISCO, or Southwest Valve.
2.	Equipment / Item Description: Description of the equipment pulled from the RFP or matching it with the brands represented.
3.	Named Manufacturers for Relevant Equipment / Item Section: Review the equipment section of the RFP in the spec sections and carefully read the subsection about manufacturers. Typically, you will see multiple manufacturers, separate by comma and in some cases the sentence ends with or equal. 
4. Represented Company: Review all the manufactures in section 3 against the represented manufacturers shared earlier. Indicate whether there is a named MISCO represented brand, Shape-represented brand, or Southwest Valve represented brand, if none of these companies represent the mentioned manufacturer, write None. If there is no named, mentioned manufacturer, leave it empty
5. Contact Information: Include the relevant contact for the identified equipment, based on the list provided:
o	MISCO Northern California: Sandy Clarke, sclarke@miscowater.com
o	Shape Northern California: Nick Chavez, nchavez@shapecal.com
o	Southwest Valves Northern California: Dave Burrell

6.	Product Specifications, Criteria, and Requirements: Extract specific technical details, performance standards, materials, or other requirements outlined in the RFP for each equipment category.
<NOTE> Ensure the Excel document (JSON from you) includes detailed specifications, criteria, and requirements for each equipment item. Populate the contact details for MISCO, Shape, and Southwest Valves from the provided contact list.
<OUTPUT>
Generate only the JSON formatted as per the schema above. Save it with the specified structure to represent each company's sheet data clearly.
"""

email_draft_prompt = """
<INSTRUCTIONS>
Draft an email addressed to UFT portfolio company leads based on the bluesheet document generated in previous steps. This email should summarize the analysis conducted and offer the bluesheet as an attachment for further review. Ensure the email is professional and contains key details for the recipient to understand the document's contents.

<FORMATTING GUIDELINES>
1. Use a clear and professional subject line, e.g., "RFP Analysis and Bluesheet for [Project Name]".
2. Start with a greeting, addressing UFT portfolio company leads directly (e.g., "Dear UFT Portfolio Company Leads").
3. Summarize the purpose of the email in a few sentences, highlighting that the email contains the bluesheet for the RFP analysis.
4. Briefly describe the contents of the bluesheet, mentioning key sections like project information, bid information, funding sources, equipment details, and synergy opportunities with MISCO, Shape, and Southwest Valve.
5. Conclude with a closing statement offering further assistance or requesting feedback if needed, followed by a professional signature (e.g., "Best regards, [Your Name]").
6. Output should be in html format: 
[
   "The html outmat should be in format for easy rendering in chat window. Use html elements instead of '*' and '#'",
   "use b tag for bold text",
   "use h2 for headings",
   "use ul for bullet lists",
   "use li for each list item",
   "use ol for numbers list"
]


<ACTION>
Generate a text-based email draft for user review, formatted according to the guidelines.

<USER_RESPONSE>
{user_response}
</USER_RESPONSE>
"""

email_modification_prompt = """
<INSTRUCTIONS>
Make the following modifications to the email draft based on user feedback. Keep the structure and formatting professional and clear. Implement any specific changes requested by the user, ensuring that the email retains its original purpose and flow.

<USER_RESPONSE>
{modification_details}
</USER_RESPONSE>

<FORMATTING GUIDELINES>
Maintain the initial formatting and organization of the email, ensuring all modifications are consistent with a professional business email.

<ACTION>
Apply user-specified changes to the draft email, revising sections as necessary. Generate an updated text-based draft incorporating these changes.

<OUTPUT>
The modified email draft reflecting the requested changes.
"""


bluesheet_finalization_prompt = """
<INSTRUCTIONS>
Prepare the final bluesheet in JSON format based on the bluesheet draft generated in previous steps. The output should follow the initail JSON Schema for based on "Blue Sheet Template 2024.txt":

<ACTION>
Generate JSON following the schema specified. Use re.sub(r'```json|```', '', response_text).strip() to extract JSON output from the response.
"""


follow_up_prompt = """
<INSTRUCTIONS>Ask user if they would like to perform any other actions or need further assistance.
<Question>
Would you like to perform any other actions or need further assistance?
<Action if Yes>
Reply: "Provide details on the next action you would like to take, and I will assist you."
<Action if No>
I will conclude the session. Thank you for using this service.
<Output>
If user responds with "Yes", proceed to ask for specific details on the requested action. If "No", confirm session completion.
"""

response_handling_prompt = """
<INSTRUCTIONS>
The user has responded to the question about whether they need further assistance. Interpret the response, asking for specifics if they would like additional actions or concluding the session if they do not.
<USER_RESPONSE>
{user_response}
<Output>
If the response is affirmative, ask for details on the next action. 
* If it's excel document generation, send JSON with excel specifics  following initial sample schema. 
* If it's word document generation, send JSON with docx specifics following same schema in sample document.
If the response is negative, provide a thank-you message to end the session. Start the thank-you message with "END: Thank you for using this service." Do not use any formatting or html structure for this thank-you message.
"""
