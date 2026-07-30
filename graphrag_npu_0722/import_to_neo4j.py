"""Import the 2026-07-22 GraphRAG parquet artifacts into Neo4j.

The import is idempotent: all nodes and relationships use stable dataset-scoped
keys and MERGE, so rerunning the command updates rather than duplicates data.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase


DEFAULT_DATASET = "graphrag_npu_0722"
REQUIRED_FILES = (
    "entities.parquet",
    "relationships.parquet",
    "communities.parquet",
    "community_reports.parquet",
    "documents.parquet",
    "text_units.parquet",
)


def clean(value: Any) -> Any:
    """Convert pandas/numpy scalar and list values to Neo4j properties."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        value = value.tolist()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, (list, tuple)):
        return [item for item in (clean(item) for item in value) if item is not None]
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def keyed_rows(frame: pd.DataFrame, columns: list[str], dataset: str) -> list[dict[str, Any]]:
    result = []
    for record in frame.to_dict("records"):
        item = {column: clean(record.get(column)) for column in columns}
        item["key"] = f"{dataset}:{record['id']}"
        item["dataset"] = dataset
        result.append(item)
    return result


def batches(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def write_batches(driver, database: str, query: str, items: list[dict[str, Any]], size: int) -> None:
    for batch in batches(items, size):
        driver.execute_query(query, rows=batch, database_=database)


def load_outputs(output: Path) -> dict[str, pd.DataFrame]:
    missing = [name for name in REQUIRED_FILES if not (output / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing GraphRAG outputs: {', '.join(missing)}")
    return {name.removesuffix(".parquet"): pd.read_parquet(output / name) for name in REQUIRED_FILES}


def validate(data: dict[str, pd.DataFrame]) -> None:
    entities = data["entities"]
    relationships = data["relationships"]
    communities = data["communities"]
    reports = data["community_reports"]
    documents = data["documents"]
    text_units = data["text_units"]

    for name, frame in data.items():
        if "id" not in frame or not frame["id"].is_unique:
            raise ValueError(f"{name}: id column is missing or not unique")
    titles = set(entities["title"])
    if not set(relationships["source"]).issubset(titles) or not set(relationships["target"]).issubset(titles):
        raise ValueError("relationships contain endpoints absent from entities")
    if not set(reports["community"]).issubset(set(communities["community"])):
        raise ValueError("community reports reference absent communities")
    if not set(text_units["document_id"]).issubset(set(documents["id"])):
        raise ValueError("text units reference absent documents")


def main() -> None:
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "output_batch10_stable")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--dry-run", action="store_true", help="Validate and count parquet data without connecting")
    args = parser.parse_args()

    output = args.output.resolve()
    data = load_outputs(output)
    validate(data)
    print(f"Validated: {output}")
    for name, frame in data.items():
        print(f"{name}: {len(frame)}")
    if args.dry_run:
        return

    uri = os.environ["NEO4J_URI"]
    username = os.getenv("NEO4J_USERNAME") or os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    dataset = args.dataset

    entities = data["entities"]
    relationships = data["relationships"]
    communities = data["communities"]
    reports = data["community_reports"]
    documents = data["documents"]
    text_units = data["text_units"]

    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        driver.verify_connectivity()
        for query in (
            "CREATE CONSTRAINT graphrag_entity_key IF NOT EXISTS FOR (n:GraphRAGEntity) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_community_key IF NOT EXISTS FOR (n:GraphRAGCommunity) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_report_key IF NOT EXISTS FOR (n:GraphRAGCommunityReport) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_document_key IF NOT EXISTS FOR (n:GraphRAGDocument) REQUIRE n.key IS UNIQUE",
            "CREATE CONSTRAINT graphrag_text_unit_key IF NOT EXISTS FOR (n:GraphRAGTextUnit) REQUIRE n.key IS UNIQUE",
        ):
            driver.execute_query(query, database_=args.database)

        write_batches(driver, args.database, "UNWIND $rows AS row MERGE (n:GraphRAGEntity {key: row.key}) SET n += row", keyed_rows(entities, ["id", "human_readable_id", "title", "type", "description", "frequency", "degree"], dataset), args.batch_size)
        write_batches(driver, args.database, "UNWIND $rows AS row MERGE (n:GraphRAGCommunity {key: row.key}) SET n += row", keyed_rows(communities, ["id", "human_readable_id", "community", "level", "parent", "title", "period", "size"], dataset), args.batch_size)
        write_batches(driver, args.database, "UNWIND $rows AS row MERGE (n:GraphRAGCommunityReport {key: row.key}) SET n += row WITH n, row MATCH (c:GraphRAGCommunity {dataset: row.dataset, community: row.community}) MERGE (c)-[:HAS_REPORT]->(n)", keyed_rows(reports, ["id", "human_readable_id", "community", "level", "parent", "title", "summary", "full_content", "rank", "rating_explanation", "period", "size"], dataset), args.batch_size)
        write_batches(driver, args.database, "UNWIND $rows AS row MERGE (n:GraphRAGDocument {key: row.key}) SET n += row", keyed_rows(documents, ["id", "human_readable_id", "title", "text", "creation_date"], dataset), args.batch_size)
        write_batches(driver, args.database, "UNWIND $rows AS row MERGE (t:GraphRAGTextUnit {key: row.key}) SET t += row WITH t, row MATCH (d:GraphRAGDocument {key: row.dataset + ':' + row.document_id}) MERGE (d)-[:HAS_TEXT_UNIT]->(t)", keyed_rows(text_units, ["id", "human_readable_id", "text", "n_tokens", "document_id"], dataset), args.batch_size)

        relationship_rows = keyed_rows(relationships, ["id", "human_readable_id", "source", "target", "description", "weight", "combined_degree", "text_unit_ids"], dataset)
        write_batches(driver, args.database, "UNWIND $rows AS row MATCH (s:GraphRAGEntity {dataset: row.dataset, title: row.source}) MATCH (t:GraphRAGEntity {dataset: row.dataset, title: row.target}) MERGE (s)-[r:GRAPHRAG_RELATED_TO {key: row.key}]->(t) SET r += row", relationship_rows, args.batch_size)

        membership_rows = [{"community_key": f"{dataset}:{record['id']}", "entity_key": f"{dataset}:{entity_id}"} for record in communities.to_dict("records") for entity_id in (clean(record.get("entity_ids")) or [])]
        write_batches(driver, args.database, "UNWIND $rows AS row MATCH (c:GraphRAGCommunity {key: row.community_key}) MATCH (e:GraphRAGEntity {key: row.entity_key}) MERGE (e)-[:IN_GRAPHRAG_COMMUNITY]->(c)", membership_rows, args.batch_size)

        evidence_rows = [{"owner_key": f"{dataset}:{record['id']}", "text_key": f"{dataset}:{text_id}"} for record in entities.to_dict("records") for text_id in (clean(record.get("text_unit_ids")) or [])]
        write_batches(driver, args.database, "UNWIND $rows AS row MATCH (e:GraphRAGEntity {key: row.owner_key}) MATCH (t:GraphRAGTextUnit {key: row.text_key}) MERGE (e)-[:MENTIONED_IN]->(t)", evidence_rows, args.batch_size)

        node_counts, _, _ = driver.execute_query("MATCH (n) WHERE n.dataset = $dataset RETURN labels(n)[0] AS label, count(*) AS count ORDER BY label", dataset=dataset, database_=args.database)
        edge_counts, _, _ = driver.execute_query("MATCH (a)-[r]->(b) WHERE a.dataset = $dataset AND b.dataset = $dataset RETURN type(r) AS type, count(*) AS count ORDER BY type", dataset=dataset, database_=args.database)

    print("Import complete")
    for record in node_counts:
        print(f"{record['label']}: {record['count']}")
    for record in edge_counts:
        print(f"{record['type']}: {record['count']}")


if __name__ == "__main__":
    main()
