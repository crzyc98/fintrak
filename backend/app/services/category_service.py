import re
import uuid
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTree,
    CategoryGroup,
)


class CategoryService:
    def create(self, data: CategoryCreate) -> CategoryResponse:
        category_id = str(uuid.uuid4())
        created_at = datetime.utcnow()

        if data.parent_id:
            if not self._parent_exists(data.parent_id):
                raise ValueError("Parent category not found")
            if self._would_create_cycle(category_id, data.parent_id):
                raise ValueError("Cannot set parent: would create circular reference")

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO categories (id, name, emoji, parent_id, group_name, budget_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    category_id,
                    data.name,
                    data.emoji,
                    data.parent_id,
                    data.group_name.value,
                    data.budget_amount,
                    created_at,
                ],
            )

        return CategoryResponse(
            id=category_id,
            name=data.name,
            emoji=data.emoji,
            parent_id=data.parent_id,
            group_name=data.group_name,
            budget_amount=data.budget_amount,
            created_at=created_at,
        )

    def get_all(self) -> list[CategoryResponse]:
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT id, name, emoji, parent_id, group_name, budget_amount, created_at
                FROM categories
                ORDER BY group_name, name
                """
            ).fetchall()

        return [
            CategoryResponse(
                id=row[0],
                name=row[1],
                emoji=row[2],
                parent_id=row[3],
                group_name=CategoryGroup(row[4]),
                budget_amount=row[5],
                created_at=row[6],
            )
            for row in result
        ]

    def get_tree(self) -> list[CategoryTree]:
        categories = self.get_all()
        category_map = {c.id: c for c in categories}

        def build_tree_node(cat: CategoryResponse) -> CategoryTree:
            children = [
                build_tree_node(c) for c in categories if c.parent_id == cat.id
            ]
            return CategoryTree(
                id=cat.id,
                name=cat.name,
                emoji=cat.emoji,
                parent_id=cat.parent_id,
                group_name=cat.group_name,
                budget_amount=cat.budget_amount,
                created_at=cat.created_at,
                children=children,
            )

        root_categories = [c for c in categories if c.parent_id is None]
        return [build_tree_node(c) for c in root_categories]

    def get_by_id(self, category_id: str) -> Optional[CategoryResponse]:
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT id, name, emoji, parent_id, group_name, budget_amount, created_at
                FROM categories
                WHERE id = ?
                """,
                [category_id],
            ).fetchone()

        if not result:
            return None

        return CategoryResponse(
            id=result[0],
            name=result[1],
            emoji=result[2],
            parent_id=result[3],
            group_name=CategoryGroup(result[4]),
            budget_amount=result[5],
            created_at=result[6],
        )

    def update(self, category_id: str, data: CategoryUpdate) -> Optional[CategoryResponse]:
        existing = self.get_by_id(category_id)
        if not existing:
            return None

        if data.parent_id is not None:
            if data.parent_id == category_id:
                raise ValueError("Category cannot be its own parent")
            if data.parent_id and not self._parent_exists(data.parent_id):
                raise ValueError("Parent category not found")
            if data.parent_id and self._would_create_cycle(category_id, data.parent_id):
                raise ValueError("Cannot set parent: would create circular reference")

        updates = []
        values = []

        if data.name is not None:
            updates.append("name = ?")
            values.append(data.name)

        if data.emoji is not None:
            updates.append("emoji = ?")
            values.append(data.emoji)

        if data.parent_id is not None:
            updates.append("parent_id = ?")
            values.append(data.parent_id if data.parent_id else None)

        if data.group_name is not None:
            updates.append("group_name = ?")
            values.append(data.group_name.value)

        if data.budget_amount is not None:
            updates.append("budget_amount = ?")
            values.append(data.budget_amount)

        if not updates:
            return existing

        values.append(category_id)

        with get_db() as conn:
            conn.execute(
                f"UPDATE categories SET {', '.join(updates)} WHERE id = ?",
                values,
            )

        return self.get_by_id(category_id)

    def delete(self, category_id: str) -> tuple[bool, Optional[str]]:
        existing = self.get_by_id(category_id)
        if not existing:
            return False, "Category not found"

        with get_db() as conn:
            child_count = conn.execute(
                "SELECT COUNT(*) FROM categories WHERE parent_id = ?",
                [category_id],
            ).fetchone()[0]

            if child_count > 0:
                return False, f"Cannot delete category: {child_count} child category(ies) exist"

            conn.execute("DELETE FROM categories WHERE id = ?", [category_id])

        return True, None

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        """Normalize a category name for fuzzy matching."""
        s = name.strip().lower()
        # Normalize whitespace
        s = re.sub(r"\s+", " ", s)
        # Normalize & / and
        s = s.replace(" & ", " and ")
        # Remove trailing 's' for simple singular/plural
        if s.endswith("s") and not s.endswith("ss"):
            s = s[:-1]
        return s

    def find_by_name(self, name: str) -> Optional[CategoryResponse]:
        """Case-insensitive lookup of a category by name with fuzzy matching."""
        normalized = self._normalize_category_name(name)
        categories = self.get_all()
        for cat in categories:
            if self._normalize_category_name(cat.name) == normalized:
                return cat
        return None

    def find_or_create(
        self,
        name: str,
        group_name: str = "Other",
        emoji: Optional[str] = None,
    ) -> CategoryResponse:
        """Look up a category by name; create it if missing."""
        existing = self.find_by_name(name)
        if existing:
            return existing

        # Map group_name string to CategoryGroup enum
        try:
            group = CategoryGroup(group_name)
        except ValueError:
            group = CategoryGroup.OTHER

        return self.create(CategoryCreate(
            name=name,
            emoji=emoji,
            group_name=group,
        ))

    def _parent_exists(self, parent_id: str) -> bool:
        with get_db() as conn:
            result = conn.execute(
                "SELECT 1 FROM categories WHERE id = ?",
                [parent_id],
            ).fetchone()
        return result is not None

    def _would_create_cycle(self, category_id: str, new_parent_id: str) -> bool:
        if category_id == new_parent_id:
            return True

        descendants = self._get_all_descendants(category_id)
        return new_parent_id in descendants

    def _get_all_descendants(self, category_id: str) -> set[str]:
        descendants = set()
        with get_db() as conn:
            children = conn.execute(
                "SELECT id FROM categories WHERE parent_id = ?",
                [category_id],
            ).fetchall()

            for (child_id,) in children:
                descendants.add(child_id)
                descendants.update(self._get_all_descendants(child_id))

        return descendants


category_service = CategoryService()
