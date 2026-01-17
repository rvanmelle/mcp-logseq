import requests
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mcp-logseq")

class LogSeq():
    def __init__(
            self, 
            api_key: str,
            protocol: str = 'http',
            host: str = "127.0.0.1",
            port: int = 12315,
            verify_ssl: bool = False,
        ):
        self.api_key = api_key
        self.protocol = protocol
        self.host = host
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = (3, 6)

    def get_base_url(self) -> str:
        return f'{self.protocol}://{self.host}:{self.port}/api'
    
    def _get_headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_key}'
        }

    def create_page(self, title: str, content: str = "") -> Any:
        """Create a new LogSeq page with specified title and content."""
        url = self.get_base_url()
        logger.info(f"Creating page '{title}'")
        
        try:
            # Step 1: Create the page
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.createPage",
                    "args": [title, {}, {"createFirstBlock": True}]
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            page_result = response.json()
            
            # Step 2: Add content if provided
            if content and content.strip():
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json={
                        "method": "logseq.Editor.appendBlockInPage",
                        "args": [title, content]
                    },
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                response.raise_for_status()
            
            return page_result

        except Exception as e:
            logger.error(f"Error creating page: {str(e)}")
            raise
            
    def list_pages(self) -> Any:
        """List all pages in the LogSeq graph."""
        url = self.get_base_url()
        logger.info("Listing pages")
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.getAllPages",
                    "args": []
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error listing pages: {str(e)}")
            raise
    
    def get_page_content(self, page_name: str) -> Any:
        """Get content of a LogSeq page including metadata and block content."""
        url = self.get_base_url()
        logger.info(f"Getting content for page '{page_name}'")
        
        try:
            # Step 1: Get page metadata (includes UUID)
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.getPage",
                    "args": [page_name]
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            page_info = response.json()
            
            if not page_info:
                logger.error(f"Page '{page_name}' not found")
                return None
                
            # Step 2: Get page blocks using the page name
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.getPageBlocksTree",
                    "args": [page_name]
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            blocks = response.json()
            
            # Step 3: Get page properties
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.getPageProperties",
                    "args": [page_name]
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            properties = response.json() or {}
            
            return {
                "page": {
                    **page_info,
                    "properties": properties
                },
                "blocks": blocks or []
            }
            
        except Exception as e:
            logger.error(f"Error getting page content: {str(e)}")
            raise

    def search_content(self, query: str, options: dict = None) -> Any:
        """Search for content across LogSeq pages and blocks."""
        url = self.get_base_url()
        logger.info(f"Searching for '{query}'")
        
        # Default search options
        search_options = options or {}
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.search",
                    "args": [query, search_options]
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            raise
    
    def delete_page(self, page_name: str) -> Any:
        """Delete a LogSeq page by name."""
        url = self.get_base_url()
        logger.info(f"Deleting page '{page_name}'")

        try:
            # Pre-delete validation: verify page exists
            existing_pages = self.list_pages()
            page_names = [p.get("originalName") or p.get("name") for p in existing_pages if p.get("originalName") or p.get("name")]
            
            if page_name not in page_names:
                raise ValueError(f"Page '{page_name}' does not exist")
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.deletePage",
                    "args": [page_name]
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully deleted page '{page_name}'")
            return result

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Error deleting page '{page_name}': {str(e)}")
            raise
    
    def update_page(self, page_name: str, content: str = None, properties: dict = None) -> Any:
        """Update a LogSeq page with new content and/or properties."""
        url = self.get_base_url()
        logger.info(f"Updating page '{page_name}'")
        
        try:
            # Pre-update validation: verify page exists
            existing_pages = self.list_pages()
            page_names = [p.get("originalName") or p.get("name") for p in existing_pages if p.get("originalName") or p.get("name")]
            
            if page_name not in page_names:
                raise ValueError(f"Page '{page_name}' does not exist")
            
            results = []
            
            # Update properties if provided
            if properties:
                logger.debug(f"Updating properties for page '{page_name}': {properties}")
                try:
                    response = requests.post(
                        url,
                        headers=self._get_headers(),
                        json={
                            "method": "logseq.Editor.updatePage",
                            "args": [page_name, properties]
                        },
                        verify=self.verify_ssl,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    prop_result = response.json()
                    results.append(("properties", prop_result))
                except Exception as e:
                    logger.warning(f"Failed to update properties with updatePage, trying setPageProperties: {str(e)}")
                    # Fallback to setPageProperties
                    response = requests.post(
                        url,
                        headers=self._get_headers(),
                        json={
                            "method": "logseq.Editor.setPageProperties",
                            "args": [page_name, properties]
                        },
                        verify=self.verify_ssl,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    prop_result = response.json()
                    results.append(("properties_fallback", prop_result))
            
            # Update content if provided
            if content is not None:
                logger.debug(f"Updating content for page '{page_name}'")
                # Strategy: Get existing blocks and update them, or add new content
                # For now, we'll use appendBlockInPage to add new content
                # TODO: In future, implement block-level updates for more sophisticated content management
                
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json={
                        "method": "logseq.Editor.appendBlockInPage",
                        "args": [page_name, content]
                    },
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                response.raise_for_status()
                content_result = response.json()
                results.append(("content", content_result))
            
            logger.info(f"Successfully updated page '{page_name}'")
            return {"updates": results, "page": page_name}

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Error updating page '{page_name}': {str(e)}")
            raise

    # ------------------------------------------------------------------
    # Block-level operations

    def insert_block(
        self,
        parent_block: str | None,
        content: str,
        *,
        is_page_block: bool = False,
        before: bool = False,
        custom_uuid: str | None = None,
    ) -> Any:
        """Insert a new block via logseq.Editor.insertBlock."""

        url = self.get_base_url()
        logger.info(
            "Inserting block under %s (is_page_block=%s, before=%s)",
            parent_block,
            is_page_block,
            before,
        )

        options = {
            "isPageBlock": is_page_block,
            "before": before,
            "customUUID": custom_uuid,
        }

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.insertBlock",
                    "args": [parent_block, content, options],
                },
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug("insert_block result: %s", result)
            return result
        except Exception as e:
            logger.error("Error inserting block: %s", str(e))
            raise

    def update_block(self, block_uuid: str, content: str, pos: int | None = None) -> Any:
        """Update an existing block via logseq.Editor.updateBlock."""

        url = self.get_base_url()
        logger.info("Updating block %s", block_uuid)

        payload = {"content": content}
        if pos is not None:
            payload["pos"] = pos

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.updateBlock",
                    "args": [block_uuid, payload],
                },
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug("update_block result: %s", result)
            return result
        except Exception as e:
            logger.error("Error updating block %s: %s", block_uuid, str(e))
            raise

    def delete_block(self, block_uuid: str) -> Any:
        """Delete a block via logseq.Editor.removeBlock."""

        url = self.get_base_url()
        logger.info("Removing block %s", block_uuid)

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.removeBlock",
                    "args": [block_uuid],
                },
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug("delete_block result: %s", result)
            return result
        except Exception as e:
            logger.error("Error deleting block %s: %s", block_uuid, str(e))
            raise

    def get_block(self, block_uuid: str, include_children: bool = False) -> Any:
        """Fetch block details via logseq.Editor.getBlock."""

        url = self.get_base_url()
        logger.info(
            "Fetching block %s (include_children=%s)", block_uuid, include_children
        )

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "method": "logseq.Editor.getBlock",
                    "args": [block_uuid, {"includeChildren": include_children}],
                },
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug("get_block result: %s", result)
            return result
        except Exception as e:
            logger.error("Error fetching block %s: %s", block_uuid, str(e))
            raise

    # ------------------------------------------------------------------
    # Higher-level helpers for batch operations

    def _extract_block_uuid(self, result: Any) -> Optional[str]:
        """Best-effort attempt to derive a block UUID from various API responses."""

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            for key in ("uuid", "id"):
                value = result.get(key)
                if isinstance(value, str):
                    return value

            block = result.get("block")
            if isinstance(block, dict):
                for key in ("uuid", "id"):
                    value = block.get(key)
                    if isinstance(value, str):
                        return value

        return None

    def _get_children_tree(self, parent: str, *, is_page: bool) -> List[Dict[str, Any]]:
        """Return the children tree for a page or block."""

        url = self.get_base_url()
        method = "logseq.Editor.getPageBlocksTree" if is_page else "logseq.Editor.getBlockChildrenTree"

        response = requests.post(
            url,
            headers=self._get_headers(),
            json={"method": method, "args": [parent]},
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        response.raise_for_status()
        tree = response.json()

        if not tree:
            return []

        if isinstance(tree, dict):
            return tree.get("children", []) or []

        if isinstance(tree, list):
            return tree

        logger.warning("Unexpected children payload for parent %s: %r", parent, tree)
        return []

    def _insert_block_tree(
        self,
        parent: str,
        block_data: Dict[str, Any],
        *,
        is_page_block: bool,
    ) -> Optional[str]:
        """Insert a block (and its subtree) under the given parent."""

        if "content" not in block_data:
            raise ValueError("Each block definition must include a 'content' field.")

        result = self.insert_block(
            parent,
            block_data["content"],
            is_page_block=is_page_block,
            custom_uuid=block_data.get("custom_uuid"),
        )

        new_uuid = self._extract_block_uuid(result)
        if new_uuid is None:
            logger.warning("Could not determine UUID for inserted block under %s", parent)
            return None

        for child in block_data.get("children", []) or []:
            self._insert_block_tree(new_uuid, child, is_page_block=False)

        return new_uuid

    def replace_children(
        self,
        parent: str,
        blocks: List[Dict[str, Any]],
        *,
        is_page: bool = False,
        delete_existing: bool = True,
    ) -> List[str]:
        """Replace the children of a page or block with a provided block tree."""

        logger.info(
            "Replacing children under %s (is_page=%s, delete_existing=%s)",
            parent,
            is_page,
            delete_existing,
        )

        inserted: List[str] = []

        if delete_existing:
            existing_children = self._get_children_tree(parent, is_page=is_page)
            for child in reversed(existing_children):
                uuid = child.get("uuid")
                if isinstance(uuid, str):
                    self.delete_block(uuid)

        for block in blocks:
            new_uuid = self._insert_block_tree(parent, block, is_page_block=is_page)
            if new_uuid:
                inserted.append(new_uuid)

        return inserted
