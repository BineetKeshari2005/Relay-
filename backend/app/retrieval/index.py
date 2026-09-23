"""CLI and module for explicit Moss index lifecycle management."""

import argparse
import asyncio
import sys
from typing import List, Optional

from app.config.settings import settings
from app.retrieval.ingestion import load_moss_document_infos, load_normalized_documents

try:
    from moss import DocumentInfo, IndexInfo, MossClient
except ImportError:
    MossClient = None  # type: ignore


class MossIndexManager:
    """Manages index creation, population, and inspection on Moss."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        project_key: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        self.project_id = project_id or settings.moss_project_id
        self.project_key = project_key or settings.moss_project_key
        self.index_name = index_name or settings.moss_index_name

        if not self.project_id or not self.project_key or self.project_id.startswith("your_"):
            raise ValueError(
                "Cannot perform Moss index operations: MOSS_PROJECT_ID or MOSS_PROJECT_KEY is not configured."
            )

        if MossClient is None:
            raise RuntimeError("The 'moss' package is not installed. Install with 'pip install moss'.")

        self.client = MossClient(self.project_id, self.project_key)

    async def list_indexes(self) -> List[Any]:
        """List all indexes in the configured Moss project."""
        return await self.client.list_indexes()

    async def get_index_info(self, name: Optional[str] = None) -> Optional[Any]:
        """Retrieve info for a specific index, or None if it doesn't exist."""
        target_name = name or self.index_name
        indexes = await self.list_indexes()
        for idx in indexes:
            if idx.name == target_name:
                return idx
        return None

    async def delete_index(self, name: Optional[str] = None) -> bool:
        """Delete an index from Moss."""
        target_name = name or self.index_name
        return await self.client.delete_index(target_name)

    async def create_index(self, force: bool = False) -> Any:
        """
        Create and populate the Moss index with normalized knowledge documents.

        Args:
            force: If True, delete any existing index with the same name before creating.

        Returns:
            MutationResult from Moss.
        """
        existing = await self.get_index_info(self.index_name)
        if existing:
            if force:
                print(f"Index '{self.index_name}' already exists. Deleting due to --force...")
                await self.delete_index(self.index_name)
                print(f"Index '{self.index_name}' deleted.")
            else:
                print(
                    f"Index '{self.index_name}' already exists (doc_count={existing.doc_count}, status={existing.status})."
                )
                print("Use --force to recreate it.")
                return existing

        docs: List[DocumentInfo] = load_moss_document_infos()
        if not docs:
            raise RuntimeError("No knowledge documents found to index!")

        print(f"Creating Moss index '{self.index_name}' with {len(docs)} documents...")
        mutation_result = await self.client.create_index(
            self.index_name,
            docs,
            wait=True,
        )
        print(f"Index '{self.index_name}' created successfully! (doc_count={len(docs)})")
        return mutation_result


async def main():
    parser = argparse.ArgumentParser(description="Relay Moss Index Management CLI")
    parser.add_argument("--create", action="store_true", help="Create and populate the configured index")
    parser.add_argument("--force", action="store_true", help="Force recreation if index already exists")
    parser.add_argument("--status", action="store_true", help="Check status of the configured index")
    parser.add_argument("--list", action="store_true", help="List all indexes in the Moss project")

    args = parser.parse_args()

    # Default action if no flag is passed: check status
    if not (args.create or args.force or args.status or args.list):
        args.status = True

    try:
        manager = MossIndexManager()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.list:
            indexes = await manager.list_indexes()
            print(f"Found {len(indexes)} index(es) in Moss project:")
            for idx in indexes:
                print(f"  - Name: {idx.name} | Docs: {idx.doc_count} | Status: {idx.status}")

        if args.status:
            info = await manager.get_index_info()
            if info:
                print(f"Index '{manager.index_name}': EXISTS")
                print(f"  Doc Count: {info.doc_count}")
                print(f"  Status: {info.status}")
                print(f"  Model: {info.model.id if hasattr(info, 'model') else 'default'}")
            else:
                print(f"Index '{manager.index_name}': NOT FOUND. Run with --create to build it.")

        if args.create or args.force:
            await manager.create_index(force=args.force)

    except Exception as e:
        print(f"Index operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
