import json


GRAPH_EXTRACTION_PROMPT = """-Goal-
Given a Medhop text document that may contain patient journey, referral, appointment,
clinical, insurance, facility, or care-team information, identify all entities of
the requested types and all clear relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract:
- entity_name: Name of the entity. Keep patient IDs, clinic names, medication names,
  and medical abbreviations exactly as written when case matters.
- entity_type: One of the following types: [{entity_types}]
- entity_description: A comprehensive description of the entity's role, attributes,
  clinical relevance, operational status, and activities in the Medhop context.
  Do not infer facts that are not supported by the text.
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of
(source_entity, target_entity) that are clearly related.
For each relationship, extract:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation of the Medhop workflow relationship, such
  as referral, appointment, diagnosis, medication use, test order, care handoff,
  coverage, location, risk, or follow-up need
- relationship_strength: a numeric score from 1-10 indicating importance for care
  coordination
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. Return output in Traditional Chinese as a single list of all entities and
relationships. Keep proper names, IDs, and standard medical abbreviations in their
original language. Use **{record_delimiter}** as the list delimiter.

4. When finished, output {completion_delimiter}

######################
-Examples-
######################
Example 1:
Entity_types: PATIENT,CONDITION,FACILITY,DEPARTMENT,PROVIDER,APPOINTMENT
Text:
Patient MH-2048 was referred from Green River Clinic to Medhop Cardiology because
of worsening chest tightness and shortness of breath. Dr. Lin requested an
appointment within 7 days at North Harbor Medical Center. The referral note
mentions possible unstable angina and asks the cardiology team to review the ECG
before the visit.
######################
Output:
("entity"{tuple_delimiter}MH-2048{tuple_delimiter}PATIENT{tuple_delimiter}MH-2048 是由 Green River Clinic 轉介至 Medhop Cardiology 的病患，主訴胸悶惡化與呼吸急促)
{record_delimiter}
("entity"{tuple_delimiter}GREEN RIVER CLINIC{tuple_delimiter}FACILITY{tuple_delimiter}Green River Clinic 是提出轉診的原照護院所)
{record_delimiter}
("entity"{tuple_delimiter}MEDHOP CARDIOLOGY{tuple_delimiter}DEPARTMENT{tuple_delimiter}Medhop Cardiology 是接收轉診並需審閱 ECG 的心臟科團隊)
{record_delimiter}
("entity"{tuple_delimiter}DR. LIN{tuple_delimiter}PROVIDER{tuple_delimiter}Dr. Lin 是要求 7 天內安排門診的轉診醫師)
{record_delimiter}
("entity"{tuple_delimiter}NORTH HARBOR MEDICAL CENTER{tuple_delimiter}FACILITY{tuple_delimiter}North Harbor Medical Center 是預計安排心臟科門診的醫療院所)
{record_delimiter}
("entity"{tuple_delimiter}UNSTABLE ANGINA{tuple_delimiter}CONDITION{tuple_delimiter}Unstable angina 是轉診單提及的可能診斷，需要心臟科進一步評估)
{record_delimiter}
("entity"{tuple_delimiter}CARDIOLOGY APPOINTMENT WITHIN 7 DAYS{tuple_delimiter}APPOINTMENT{tuple_delimiter}此門診需求要求在 7 天內安排，以回應胸悶與疑似不穩定心絞痛風險)
{record_delimiter}
("relationship"{tuple_delimiter}MH-2048{tuple_delimiter}GREEN RIVER CLINIC{tuple_delimiter}MH-2048 是由 Green River Clinic 轉出照護的病患{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}MH-2048{tuple_delimiter}MEDHOP CARDIOLOGY{tuple_delimiter}MH-2048 被轉介至 Medhop Cardiology 接受心臟科評估{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}DR. LIN{tuple_delimiter}CARDIOLOGY APPOINTMENT WITHIN 7 DAYS{tuple_delimiter}Dr. Lin 要求在 7 天內安排心臟科門診{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}UNSTABLE ANGINA{tuple_delimiter}MEDHOP CARDIOLOGY{tuple_delimiter}疑似 unstable angina 是心臟科需要評估的核心原因{tuple_delimiter}9)
{completion_delimiter}

######################
Example 2:
Entity_types: PATIENT,MEDICATION,CONDITION,CARE_PLAN,PROVIDER
Text:
The discharge summary for patient A-118 says she has type 2 diabetes and chronic
kidney disease stage 3. Her primary care provider asked Medhop to reconcile
metformin and lisinopril, confirm renal dosing, and schedule a nurse follow-up
call in two weeks.
######################
Output:
("entity"{tuple_delimiter}A-118{tuple_delimiter}PATIENT{tuple_delimiter}A-118 是出院摘要中的病患，需要 Medhop 協助用藥核對與後續追蹤)
{record_delimiter}
("entity"{tuple_delimiter}TYPE 2 DIABETES{tuple_delimiter}CONDITION{tuple_delimiter}Type 2 diabetes 是 A-118 的慢性疾病之一，與 metformin 用藥管理相關)
{record_delimiter}
("entity"{tuple_delimiter}CHRONIC KIDNEY DISEASE STAGE 3{tuple_delimiter}CONDITION{tuple_delimiter}Chronic kidney disease stage 3 是 A-118 的腎功能相關診斷，影響藥物劑量確認)
{record_delimiter}
("entity"{tuple_delimiter}METFORMIN{tuple_delimiter}MEDICATION{tuple_delimiter}Metformin 是需要 Medhop 核對並確認腎功能劑量適切性的藥物)
{record_delimiter}
("entity"{tuple_delimiter}NURSE FOLLOW-UP CALL IN TWO WEEKS{tuple_delimiter}CARE_PLAN{tuple_delimiter}兩週後護理追蹤電話是主要照護醫師要求安排的後續照護計畫)
{record_delimiter}
("relationship"{tuple_delimiter}A-118{tuple_delimiter}CHRONIC KIDNEY DISEASE STAGE 3{tuple_delimiter}A-118 有第三期慢性腎臟病，會影響用藥安全評估{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}METFORMIN{tuple_delimiter}CHRONIC KIDNEY DISEASE STAGE 3{tuple_delimiter}Metformin 需要依腎功能確認劑量適切性{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}A-118{tuple_delimiter}NURSE FOLLOW-UP CALL IN TWO WEEKS{tuple_delimiter}A-118 需要在兩週後接受護理追蹤電話{tuple_delimiter}7)
{completion_delimiter}

######################
Example 3:
Entity_types: PATIENT,INSURANCE,FACILITY,PROCEDURE,APPOINTMENT,ADMIN_TASK
Text:
Medhop intake notes show that patient TPE-77 needs an MRI of the lumbar spine at
Westlake Imaging. BrightCare HMO requires prior authorization before scheduling.
The care coordinator submitted the authorization request and marked the
appointment as pending insurance approval.
######################
Output:
("entity"{tuple_delimiter}TPE-77{tuple_delimiter}PATIENT{tuple_delimiter}TPE-77 是 Medhop intake notes 中需要安排腰椎 MRI 的病患)
{record_delimiter}
("entity"{tuple_delimiter}MRI OF THE LUMBAR SPINE{tuple_delimiter}PROCEDURE{tuple_delimiter}腰椎 MRI 是 TPE-77 需要安排的影像檢查)
{record_delimiter}
("entity"{tuple_delimiter}WESTLAKE IMAGING{tuple_delimiter}FACILITY{tuple_delimiter}Westlake Imaging 是預計執行腰椎 MRI 的影像檢查院所)
{record_delimiter}
("entity"{tuple_delimiter}BRIGHTCARE HMO{tuple_delimiter}INSURANCE{tuple_delimiter}BrightCare HMO 是要求排程前需事前授權的保險方)
{record_delimiter}
("entity"{tuple_delimiter}PRIOR AUTHORIZATION REQUEST{tuple_delimiter}ADMIN_TASK{tuple_delimiter}事前授權申請已由照護協調員送出，是排程前的行政必要事項)
{record_delimiter}
("relationship"{tuple_delimiter}TPE-77{tuple_delimiter}MRI OF THE LUMBAR SPINE{tuple_delimiter}TPE-77 需要接受腰椎 MRI 檢查{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}MRI OF THE LUMBAR SPINE{tuple_delimiter}WESTLAKE IMAGING{tuple_delimiter}腰椎 MRI 預計在 Westlake Imaging 執行{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}BRIGHTCARE HMO{tuple_delimiter}PRIOR AUTHORIZATION REQUEST{tuple_delimiter}BrightCare HMO 要求排程前必須取得事前授權{tuple_delimiter}9)
{completion_delimiter}

######################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:"""


def create_extraction_prompt(entity_types, input_text, tuple_delimiter=";"):
    return GRAPH_EXTRACTION_PROMPT.format(
        entity_types=entity_types,
        input_text=input_text,
        tuple_delimiter=tuple_delimiter,
        record_delimiter="|",
        completion_delimiter="\n\n",
    )


def parse_extraction_output(output_str, record_delimiter=None, tuple_delimiter=None):
    """
    Parse a structured output string containing "entity" and "relationship"
    records into separate node and relationship lists.
    """
    completion_marker = "{completion_delimiter}"
    if completion_marker in output_str:
        output_str = output_str.replace(completion_marker, "")
    output_str = output_str.strip()

    if record_delimiter is None:
        if "{record_delimiter}" in output_str:
            record_delimiter = "{record_delimiter}"
        elif "|" in output_str:
            record_delimiter = "|"
        else:
            record_delimiter = "\n"

    if tuple_delimiter is None:
        if "{tuple_delimiter}" in output_str:
            tuple_delimiter = "{tuple_delimiter}"
        elif ";" in output_str:
            tuple_delimiter = ";"
        else:
            tuple_delimiter = "\t"

    raw_records = [r.strip() for r in output_str.split(record_delimiter)]
    parsed_records = []

    for rec in raw_records:
        if not rec:
            continue
        if rec.startswith("(") and rec.endswith(")"):
            rec = rec[1:-1]

        tokens = [token.strip() for token in rec.split(tuple_delimiter)]
        if not tokens:
            continue

        rec_type = tokens[0].strip(" \"'").lower()
        if rec_type == "entity":
            if len(tokens) != 4:
                continue
            parsed_records.append(
                {
                    "record_type": "entity",
                    "entity_name": tokens[1],
                    "entity_type": tokens[2],
                    "entity_description": tokens[3],
                }
            )
        elif rec_type == "relationship":
            if len(tokens) != 5:
                continue
            try:
                strength = float(tokens[4])
                if strength.is_integer():
                    strength = int(strength)
            except ValueError:
                strength = tokens[4]

            parsed_records.append(
                {
                    "record_type": "relationship",
                    "source_entity": tokens[1],
                    "target_entity": tokens[2],
                    "relationship_description": tokens[3],
                    "relationship_strength": strength,
                }
            )

    nodes = [el for el in parsed_records if el.get("record_type") == "entity"]
    relationships = [
        el for el in parsed_records if el.get("record_type") == "relationship"
    ]
    return nodes, relationships


import_nodes_query = """
MERGE (d:MedhopDocument {id: $book_id})
MERGE (d)-[:HAS_CHUNK]->(c:__Chunk__ {id: $chunk_id})
SET c.text = $text
WITH c
UNWIND $data AS row
MERGE (n:__Entity__ {name: row.entity_name})
SET n:$(row.entity_type),
    n.description = coalesce(n.description, []) + [row.entity_description]
MERGE (n)<-[:MENTIONS]-(c)
"""

import_relationships_query = """
UNWIND $data AS row
MERGE (s:__Entity__ {name: row.source_entity})
MERGE (t:__Entity__ {name: row.target_entity})
CREATE (s)-[r:RELATIONSHIP {
    description: row.relationship_description,
    strength: row.relationship_strength
}]->(t)
"""

SUMMARIZE_PROMPT = """
You are a Medhop care-operations assistant responsible for generating a concise
but comprehensive clinical and operational summary from the data below.
Given one or two entities and a list of descriptions related to the same patient,
provider, facility, condition, medication, appointment, referral, insurance plan,
or administrative task, merge the descriptions into one coherent summary.

Include all supported information that matters for care coordination, referral
routing, scheduling, medication reconciliation, risk review, or follow-up. If the
descriptions are contradictory, resolve the conflict when evidence allows it;
otherwise note the uncertainty without inventing missing facts.

Write in Traditional Chinese, use third person, and include the entity names so
the context remains clear. Keep proper names, IDs, and standard medical
abbreviations in their original language.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""


def get_summarize_prompt(entity_name, description_list):
    return SUMMARIZE_PROMPT.format(
        entity_name=entity_name,
        description_list=description_list,
    )


def calculate_communities(neo4j_driver):
    try:
        neo4j_driver.execute_query("""
        CALL gds.graph.drop('entity')
        """)
    except Exception:
        pass

    neo4j_driver.execute_query("""
    MATCH (source:__Entity__)-[r:RELATIONSHIP]->(target:__Entity__)
    WITH gds.graph.project(
        'entity',
        source,
        target,
        {},
        {undirectedRelationshipTypes: ['*']}
    ) AS g
    RETURN g.graphName AS graph, g.nodeCount AS nodes, g.relationshipCount AS rels
    """)

    records, _, _ = neo4j_driver.execute_query("""
    CALL gds.louvain.write("entity", {writeProperty:"louvain"})
    """)
    return [el.data() for el in records][0]


COMMUNITY_REPORT_PROMPT = """
You are a Medhop AI assistant helping a care team understand a cluster of related
entities in a healthcare coordination graph. The graph may include patients,
symptoms, diagnoses, medications, procedures, tests, referrals, appointments,
providers, departments, facilities, insurance plans, care plans, and
administrative tasks.

# Goal
Write a comprehensive report of a community, given a list of entities that belong
to the community and their relationships. The report will be used by Medhop
operators and clinical reviewers to understand care context, coordination
dependencies, operational bottlenecks, and patient-safety considerations. Do not
provide medical advice beyond what is supported by the data.

# Report Structure

- TITLE: a short, specific name for the community. Include representative patient
  IDs, care teams, facilities, or clinical themes when possible.
- SUMMARY: an executive summary of the community's structure and what matters for
  care coordination.
- IMPACT SEVERITY RATING: a float score between 0-10. Higher scores indicate
  more urgent coordination needs, patient-safety risk, time-sensitive referrals,
  blocked scheduling, or unresolved administrative dependencies.
- RATING EXPLANATION: one sentence explaining the rating.
- DETAILED FINDINGS: 5-10 key insights, each with a short summary and grounded
  explanation.

Return output as a well-formed JSON string:
{{
    "title": <report_title>,
    "summary": <executive_summary>,
    "rating": <impact_severity_rating>,
    "rating_explanation": <rating_explanation>,
    "findings": [
        {{"summary": <insight_1_summary>, "explanation": <insight_1_explanation>}},
        {{"summary": <insight_2_summary>, "explanation": <insight_2_explanation>}}
    ]
}}

# Grounding Rules

Points supported by data should list references like:
"This sentence is supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Add "+more" when needed.
Do not include information where supporting evidence is not provided.
Use Traditional Chinese for narrative fields. Keep proper names, IDs, and
standard medical abbreviations in their original language.

# Real Data

Use the following text for your answer. Do not make anything up.

Text:
{input_text}

Output:"""


def get_summarize_community_prompt(nodes, relationships):
    input_text = f"""Entities

    {nodes}

    Relationships

    {relationships}
    """
    return COMMUNITY_REPORT_PROMPT.format(input_text=input_text)


def extract_json(input: str):
    return input.removeprefix("```json").removesuffix("```").strip()


import_community_query = """
UNWIND $data AS row
MERGE (c:__Community__ {communityId: row.communityId})
SET c.title = row.community.title,
    c.summary = row.community.summary,
    c.rating = row.community.rating,
    c.rating_explanation = row.community.rating_explanation
WITH c, row
UNWIND row.nodes AS node
MERGE (n:__Entity__ {name: node})
MERGE (n)-[:IN_COMMUNITY]->(c)
"""


def import_entity_summary(neo4j_driver, entity_information):
    neo4j_driver.execute_query("""
    UNWIND $data AS row
    MATCH (e:__Entity__ {name: row.entity})
    SET e.summary = row.summary
    """, data=entity_information)

    neo4j_driver.execute_query("""
    MATCH (e:__Entity__)
    WHERE size(e.description) = 1
    SET e.summary = e.description[0]
    """)


def import_rels_summary(neo4j_driver, rel_summaries):
    neo4j_driver.execute_query("""
    UNWIND $data AS row
    MATCH (s:__Entity__ {name: row.source}), (t:__Entity__ {name: row.target})
    MERGE (s)-[r:SUMMARIZED_RELATIONSHIP]-(t)
    SET r.summary = row.summary
    """, data=rel_summaries)

    neo4j_driver.execute_query("""
    MATCH (s:__Entity__)-[e:RELATIONSHIP]-(t:__Entity__)
    WHERE NOT (s)-[:SUMMARIZED_RELATIONSHIP]-(t)
    MERGE (s)-[r:SUMMARIZED_RELATIONSHIP]-(t)
    SET r.summary = e.description
    """)


community_info_query = """
MATCH (e:__Entity__)
WHERE e.louvain IS NOT NULL
WITH e.louvain AS louvain, collect(e) AS nodes
WHERE size(nodes) > 1
CALL apoc.path.subgraphAll(nodes[0], {
    whitelistNodes:nodes
})
YIELD relationships
RETURN louvain AS communityId,
       [n in nodes | {
           id: n.name,
           description: n.summary,
           type: [el in labels(n) WHERE el <> '__Entity__'][0]
       }] AS nodes,
       [r in relationships | {
           start: startNode(r).name,
           type: type(r),
           end: endNode(r).name,
           description: r.description
       }] AS rels
"""

MAP_SYSTEM_PROMPT = """
---Role---

You are a Medhop care-operations assistant responding to questions about
healthcare coordination data in the tables provided.

---Goal---

Generate a response consisting of key points that answer the user's question by
summarizing all relevant information in the input data tables.

Use the provided data tables as the primary context. If the tables do not contain
enough information, say so. Do not make anything up, do not diagnose, and do not
provide treatment advice beyond what is explicitly supported by the data.

Each key point should have:
- Description: focused on patient journey, referral status, appointment readiness,
  care-team responsibility, medication/test/procedure context, insurance or
  administrative blockers, and follow-up needs when relevant.
- Importance Score: an integer score between 0-100. An "I don't know" response
  should have a score of 0.

Return JSON:
{{
    "points": [
        {{"description": "Description of point 1 [Data: Reports (report ids)]", "score": score_value}},
        {{"description": "Description of point 2 [Data: Reports (report ids)]", "score": score_value}}
    ]
}}

Use Traditional Chinese unless the user's question asks for another language.
Keep proper names, patient IDs, facility names, medication names, and standard
medical abbreviations in their original language.

Do not list more than 5 record ids in a single reference. Add "+more" when needed.
Do not include information where supporting evidence is not provided.

---Data tables---

{context_data}

---Goal---

Generate the JSON response now.
"""

REDUCE_SYSTEM_PROMPT = """
---Role---

You are a Medhop care-operations assistant synthesizing multiple evidence-grounded
reports about healthcare coordination data.

---Goal---

Generate a response of the target length and format that answers the user's
question by synthesizing the provided reports. The reports are ranked in
descending order of importance.

Keep only information that is relevant to the question and supported by the
reports. If the reports do not contain enough information, say so clearly. Do not
make anything up, do not diagnose, and do not provide treatment advice beyond the
evidence.

The final response should be useful for Medhop care coordination, including
referral routing, appointment readiness, patient status, provider/facility
responsibility, medication/test/procedure context, insurance blockers,
administrative tasks, and follow-up actions.

Preserve data references included in the reports, but do not mention analyst
roles. Use Traditional Chinese unless the user's question asks for another
language. Keep proper names, IDs, medication names, and standard medical
abbreviations in their original language. Style the response in markdown when
appropriate.

Do not list more than 5 record ids in a single reference. Add "+more" when needed.
Do not include information where supporting evidence is not provided.

---Target response length and format---

{response_type}

---Reports---

{report_data}

---Goal---

Generate the final response now.
"""


def get_map_system_prompt(context):
    return MAP_SYSTEM_PROMPT.format(context_data=context)


def get_reduce_system_prompt(report_data, response_type: str = "multiple paragraphs"):
    return REDUCE_SYSTEM_PROMPT.format(
        report_data=report_data,
        response_type=response_type,
    )


LOCAL_SEARCH_SYSTEM_PROMPT = """
---Role---

You are a Medhop care-operations assistant responding to questions about
healthcare coordination data in the provided tables.

---Goal---

Generate a response of the target length and format that answers the user's
question by summarizing all relevant information in the input data tables.

Use the tables as the primary source of truth. You may include general healthcare
coordination context only when it helps explain the data, but you must not invent
missing facts, diagnose, or provide treatment advice beyond the evidence.

If you do not know the answer or the tables do not contain enough information,
say so clearly.

Points supported by data should list references like:
"This sentence is supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Add "+more" when needed.
Do not include information where supporting evidence is not provided.
Use Traditional Chinese unless the user's question asks for another language.
Keep proper names, patient IDs, medication names, facility names, and standard
medical abbreviations in their original language.

---Target response length and format---

{response_type}

---Data tables---

{context_data}

---Goal---

Generate the response now. Focus on what matters for Medhop care coordination:
patient journey, referral status, scheduling readiness, clinical context,
provider/facility roles, insurance or administrative blockers, and follow-up needs.
"""


def get_local_system_prompt(report_data, response_type: str = "multiple paragraphs"):
    return LOCAL_SEARCH_SYSTEM_PROMPT.format(
        context_data=report_data,
        response_type=response_type,
    )


def loads_json_response(response_text: str):
    """Extract and parse a JSON response produced by the Medhop prompts."""
    return json.loads(extract_json(response_text))
