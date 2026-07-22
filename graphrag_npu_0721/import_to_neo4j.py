"""Import GraphRAG 3.0.9 parquet outputs into Neo4j.

Required environment variables: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD.
This importer is non-destructive and can be run repeatedly.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd
from neo4j import GraphDatabase


DATASET = "graphrag_npu_0721"


def clean(value: Any) -> Any:
    """Convert pandas/numpy values to Neo4j property-compatible values."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        value = value.tolist()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, (list, tuple)):
        cleaned = [clean(item) for item in value]
        return [item for item in cleaned if item is not None]
    return value


def rows(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    result = []
    for record in frame.to_dict("records"):
        item = {column: clean(record.get(column)) for column in columns}
        item["key"] = f"{DATASET}:{record['id']}"
        item["dataset"] = DATASET
        result.append(item)
    return result


def batches(items: list[dict[str, Any]], size: int = 250):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def write_batches(driver, query: str, items: list[dict[str, Any]]) -> None:
    for batch in batches(items):
        driver.execute_query(query, rows=batch, database_="neo4j")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "output_batch10_stable",
    )
    args = parser.parse_args()

    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USERNAME"]
    password = os.environ["NEO4J_PASSWORD"]
    output = args.output.resolve()

    required = [
        "entities.parquet",
        "relationships.parquet",
        "communities.parquet",
        "community_reports.parquet",
        "documents.parquet",
        "text_units.parquet",
    ]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing GraphRAG outputs: {', '.join(missing)}")

    entities = pd.read_parquet(output / "entities.parquet")
    relationships = pd.read_parquet(output / "relationships.parquet")
    communities = pd.read_parquet(output / "communities.parquet")
    reports = pd.read_parquet(output / "community_reports.parquet")
    documents = pd.read_parquet(output / "documents.parquet")
    text_units = pd.read_parquet(output / "text_units.parquet")

    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        driver.verify_connectivity()

        constraints = [
            "CREATE CONSTRAINT graphrag_entity_key IF NOT EXISTS FOR (n:GraphRAGEntity) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_community_key IF NOT EXISTS FOR (n:GraphRAGCommunity) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_report_key IF NOT EXISTS FOR (n:GraphRAGCommunityReport) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_document_key IF NOT EXISTS FOR (n:GraphRAGDocument) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_text_unit_key IF NOT EXISTS FOR (n:GraphRAGTextUnit) REQUIRE n.key IS UNIQUE",
        ]
        for query in constraints:
            driver.execute_query(query, database_="neo4j")

        entity_rows = rows(
            entities,
            ["id", "human_readable_id", "title", "type", "description", "frequency", "degree"],
        )
        write_batches(
            driver,
            """UNWIND $rows AS row
            MERGE (n:GraphRAGEntity {key: row.key})
            SET n += row""",
            entity_rows,
        )

        relationship_rows = rows(
            relationships,
            ["id", "human_readable_id", "source", "target", "description", "weight", "combined_degree"],
        )
        write_batches(
            driver,
            """UNWIND $rows AS row
            MATCH (source:GraphRAGEntity {dataset: row.dataset, title: row.source})
            MATCH (target:GraphRAGEntity {dataset: row.dataset, title: row.target})
            MERGE (source)-[r:GRAPHRAG_RELATED_TO {key: row.key}]->(target)
            SET r += row""",
            relationship_rows,
        )

        community_rows = rows(
            communities,
            ["id", "human_readable_id", "community", "level", "parent", "title", "period", "size"],
        )
        write_batches(
            driver,
            """UNWIND $rows AS row
            MERGE (n:GraphRAGCommunity {key: row.key})
            SET n += row""",
            community_rows,
        )

        membership_rows = []
        for record in communities.to_dict("records"):
            community_key = f"{DATASET}:{record['id']}"
            for entity_id in clean(record.get("entity_ids")) or []:
                membership_rows.append(
                    {"community_key": community_key, "entity_key": f"{DATASET}:{entity_id}"}
                )
        write_batches(
            driver,
            """UNWIND $rows AS row
            MATCH (c:GraphRAGCommunity {key: row.community_key})
            MATCH (e:GraphRAGEntity {key: row.entity_key})
            MERGE (e)-[:IN_GRAPHRAG_COMMUNITY]->(c)""",
            membership_rows,
        )

        report_rows = rows(
            reports,
            ["id", "human_readable_id", "community", "level", "parent", "title", "summary", "full_content", "rank", "rating_explanation", "period", "size"],
        )
        write_batches(
            driver,
            """UNWIND $rows AS row
            MERGE (r:GraphRAGCommunityReport {key: row.key})
            SET r += row
            WITH r, row
            MATCH (c:GraphRAGCommunity {key: row.key})
            MERGE (c)-[:HAS_REPORT]->(r)""",
            report_rows,
        )

        document_rows = rows(documents, ["id", "human_readable_id", "title", "text", "creation_date"])
        write_batches(
            driver,
            """UNWIND $rows AS row
            MERGE (n:GraphRAGDocument {key: row.key})
            SET n += row""",
            document_rows,
        )

        text_unit_rows = rows(
            text_units,
            ["id", "human_readable_id", "text", "n_tokens", "document_id"],
        )
        write_batches(
            driver,
            """UNWIND $rows AS row
            MERGE (t:GraphRAGTextUnit {key: row.key})
            SET t += row
            WITH t, row
            MATCH (d:GraphRAGDocument {key: row.dataset + ':' + row.document_id})
            MERGE (d)-[:HAS_TEXT_UNIT]->(t)""",
            text_unit_rows,
        )

        counts, _, _ = driver.execute_query(
            """MATCH (n) WHERE n.dataset = $dataset
            RETURN labels(n)[0] AS label, count(*) AS count ORDER BY label""",
            dataset=DATASET,
            database_="neo4j",
        )
        relationship_count, _, _ = driver.execute_query(
            """MATCH ()-[r:GRAPHRAG_RELATED_TO]->()
            WHERE r.dataset = $dataset RETURN count(r) AS count""",
            dataset=DATASET,
            database_="neo4j",
        )

    print(f"Imported from: {output}")
    for record in counts:
        print(f"{record['label']}: {record['count']}")
    print(f"GRAPHRAG_RELATED_TO: {relationship_count[0]['count']}")


if __name__ == "__main__":
    main()
