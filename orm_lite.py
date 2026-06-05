"""
A lightweight ORM for SQLite with enhanced features:
- Auto-migration: Automatically adds new columns when the model changes.
- Bulk operations: Efficiently insert and update multiple records.
- Lazy evaluation: QuerySets are evaluated only when needed.
- Improved error handling: Better feedback for common issues.
Example usage:
from orm_lite import Model, StringField, IntegerField, BooleanField, DateTimeField, ForeignKey, db

class User(Model):
    name = StringField(nullable=False, unique=True)
    age = IntegerField(default=18)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

class Post(Model):
    title = StringField(nullable=False)
    content = StringField()
    user_id = ForeignKey(User, on_delete="CASCADE")

db = Database()
User.migrate()
Post.migrate()
# Bulk create – now works without NOT NULL error
users = User.bulk_create([
    {"name": "Charlie", "age": 22},
    {"name": "Diana", "age": 28}
])

print(User.all())
db.close()
"""

import sqlite3
from typing import Any, List, Optional, Type, Dict, Union, Iterator
from datetime import datetime
from contextlib import contextmanager

# =========================
# DATABASE CORE
# =========================
class Database:
    '''
    Simple wrapper around sqlite3 with enhanced error handling and transaction support.
    - Automatically enables foreign key constraints.
    - Provides a context manager for transactions.
    - Improved error handling with rollback on failure.
    '''
    def __init__(self, db_name: str = "database.db"):
        self.db_name = db_name
        self.conn = None
        self._connect()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def connect(self, db_name: str):
        """Switch the database file used by this Database instance."""
        self.close()
        self.db_name = db_name
        self._connect()

    def __call__(self, db_name: str):
        self.connect(db_name)

    def execute(self, query: str, params: tuple = ()):
        try:
            cursor = self.conn.execute(query, params)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    def executemany(self, query: str, params_seq: List[tuple]):
        try:
            cursor = self.conn.executemany(query, params_seq)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            self.conn.rollback()
            raise e

    @contextmanager
    def transaction(self):
        """Context manager for manual transaction control."""
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self):
        if self.conn:
            self.conn.close()

# Global DB instance
db = Database()


# =========================
# ENHANCED FIELD DEFINITIONS
# =========================
class Field:
    """
    Base class for all field types with enhanced options:
    - unique: Enforces uniqueness at the database level.
    - auto_now: Automatically updates to current timestamp on save.
    - auto_now_add: Automatically sets to current timestamp on first save.
    - Improved SQL definition generation to handle new options.
    Example usage:
    class User(Model):
        name = StringField(nullable=False, unique=True)
        age = IntegerField(default=18)
        is_active = BooleanField(default=True)
        created_at = DateTimeField(auto_now_add=True)
    """
    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"
    def __init__(
        self,
        column_type: str,
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        unique: bool = False,
    ):
        self.column_type = column_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique

    def get_sql_definition(self, name: str) -> str:
        parts = [name, self.column_type]
        if self.primary_key:
            parts.append("PRIMARY KEY AUTOINCREMENT")
        else:
            if not self.nullable:
                parts.append("NOT NULL")
            if self.unique:
                parts.append("UNIQUE")
        return " ".join(parts)


class IntegerField(Field):
    def __init__(self, primary_key=False, nullable=False, default=None, unique=False):
        super().__init__("INTEGER", primary_key, nullable, default, unique)


class StringField(Field):
    def __init__(self, nullable=False, default="", unique=False):
        super().__init__("TEXT", False, nullable, default, unique)


class FloatField(Field):
    def __init__(self, nullable=False, default=0.0, unique=False):
        super().__init__("REAL", False, nullable, default, unique)


class BooleanField(Field):
    def __init__(self, nullable=False, default=False):
        super().__init__("INTEGER", False, nullable, default, unique=False)


class DateTimeField(Field):
    def __init__(self, nullable=False, default=None, auto_now=False, auto_now_add=False):
        super().__init__("TIMESTAMP", False, nullable, default, unique=False)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def get_sql_definition(self, name: str) -> str:
        # SQLite doesn't have native TIMESTAMP, but it will store as TEXT.
        return super().get_sql_definition(name).replace("TIMESTAMP", "TEXT")


class ForeignKey(Field):
    def __init__(self, to_model: Type["Model"], nullable=True, on_delete="CASCADE"):
        super().__init__("INTEGER", False, nullable, default=None, unique=False)
        self.to_model = to_model
        self.on_delete = on_delete

    def get_sql_definition(self, name: str) -> str:
        ref_table = self.to_model._table
        base = super().get_sql_definition(name)
        return f"{base} REFERENCES {ref_table}(id) ON DELETE {self.on_delete}"


# =========================
# QUERYSET (lazy evaluation)
# =========================
class QuerySet:
    def __init__(self, model_class: Type["Model"]):
        self.model_class = model_class
        self._filters = []
        self._order_by = []
        self._limit = None
        self._offset = None

    def filter(self, **kwargs) -> "QuerySet":
        qs = self._clone()
        for key, value in kwargs.items():
            qs._filters.append((key, value))
        return qs

    def order_by(self, *fields: str) -> "QuerySet":
        qs = self._clone()
        qs._order_by.extend(fields)
        return qs

    def limit(self, limit: int) -> "QuerySet":
        qs = self._clone()
        qs._limit = limit
        return qs

    def offset(self, offset: int) -> "QuerySet":
        qs = self._clone()
        qs._offset = offset
        return qs

    def _clone(self) -> "QuerySet":
        qs = QuerySet(self.model_class)
        qs._filters = self._filters[:]
        qs._order_by = self._order_by[:]
        qs._limit = self._limit
        qs._offset = self._offset
        return qs

    def _build_query(self) -> tuple:
        where_clause = ""
        params = []
        if self._filters:
            conditions = []
            for k, v in self._filters:
                conditions.append(f"{k}=?")
                params.append(v)
            where_clause = "WHERE " + " AND ".join(conditions)

        order_clause = ""
        if self._order_by:
            order_clause = "ORDER BY " + ", ".join(self._order_by)

        limit_clause = ""
        if self._limit is not None:
            limit_clause = f"LIMIT {self._limit}"
        offset_clause = ""
        if self._offset is not None:
            offset_clause = f"OFFSET {self._offset}"

        query = f"SELECT * FROM {self.model_class._table} {where_clause} {order_clause} {limit_clause} {offset_clause}".strip()
        return query, tuple(params)

    def _execute(self):
        query, params = self._build_query()
        rows = db.execute(query, params).fetchall()
        return [self.model_class(**dict(row)) for row in rows]

    def all(self) -> List["Model"]:
        return self._execute()

    def first(self) -> Optional["Model"]:
        qs = self.limit(1)
        rows = qs._execute()
        return rows[0] if rows else None

    def last(self) -> Optional["Model"]:
        if not self._order_by:
            qs = self.order_by(f"{self.model_class._pk} DESC").limit(1)
        else:
            qs = self.order_by(*[f"{f} DESC" for f in self._order_by]).limit(1)
        rows = qs._execute()
        return rows[0] if rows else None

    def count(self) -> int:
        query, params = self._build_query()
        count_query = f"SELECT COUNT(*) FROM ({query})"
        result = db.execute(count_query, params).fetchone()[0]
        return result

    def exists(self) -> bool:
        return self.count() > 0

    def delete(self) -> int:
        if not self._filters:
            raise ValueError("Cannot delete without filters (would delete all rows)")
        query, params = self._build_query()
        delete_query = f"DELETE FROM {self.model_class._table} WHERE rowid IN (SELECT rowid FROM ({query}))"
        cursor = db.execute(delete_query, params)
        return cursor.rowcount

    def update(self, **kwargs) -> int:
        if not self._filters:
            raise ValueError("Cannot update without filters (would update all rows)")
        set_clause = ", ".join([f"{k}=?" for k in kwargs])
        params = tuple(kwargs.values())
        query, filter_params = self._build_query()
        update_query = f"""
            UPDATE {self.model_class._table}
            SET {set_clause}
            WHERE rowid IN (SELECT rowid FROM ({query}))
        """
        cursor = db.execute(update_query, params + filter_params)
        return cursor.rowcount

    def __iter__(self) -> Iterator["Model"]:
        return iter(self._execute())

    def __repr__(self):
        return f"<QuerySet {self.model_class.__name__} filters={self._filters}>"


# =========================
# METACLASS
# =========================
class ModelMeta(type):
    def __new__(cls, name, bases, attrs):
        if name == "Model":
            return super().__new__(cls, name, bases, attrs)

        fields = {}
        primary_key_name = None
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                fields[key] = value
                attrs.pop(key)
                if value.primary_key:
                    primary_key_name = key

        if not primary_key_name:
            if "id" not in fields:
                fields["id"] = IntegerField(primary_key=True)
                primary_key_name = "id"
            else:
                if not fields["id"].primary_key:
                    fields["id"].primary_key = True
                    fields["id"].nullable = False
                primary_key_name = "id"

        attrs["_fields"] = fields
        attrs["_table"] = name.lower()
        attrs["_pk"] = primary_key_name

        new_class = super().__new__(cls, name, bases, attrs)
        new_class._create_table()
        return new_class


# =========================
# BASE MODEL
# =========================
class Model(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        self._loaded_from_db = False
        for field in self._fields:
            value = kwargs.get(field)
            if value is None and field != self._pk:
                field_def = self._fields[field]
                if field_def.default is not None:
                    value = field_def.default if not callable(field_def.default) else field_def.default()
            setattr(self, field, value)

    @classmethod
    def _create_table(cls):
        columns = []
        for name, field in cls._fields.items():
            columns.append(field.get_sql_definition(name))
        query = f"CREATE TABLE IF NOT EXISTS {cls._table} ({', '.join(columns)})"
        db.execute(query)

    @classmethod
    def _migrate_add_column(cls, column_name: str, field: Field):
        try:
            db.execute(f"ALTER TABLE {cls._table} ADD COLUMN {field.get_sql_definition(column_name)}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise

    @classmethod
    def migrate(cls):
        cursor = db.execute(f"PRAGMA table_info({cls._table})")
        existing = {row[1] for row in cursor.fetchall()}
        for name, field in cls._fields.items():
            if name not in existing and not field.primary_key:
                cls._migrate_add_column(name, field)

    def save(self):
        # Auto-handle DateTimeField with auto_now/auto_now_add
        for name, field in self._fields.items():
            if isinstance(field, DateTimeField):
                if field.auto_now:
                    setattr(self, name, datetime.now().isoformat())
                elif field.auto_now_add and not getattr(self, name, None):
                    setattr(self, name, datetime.now().isoformat())

        fields = [f for f in self._fields if f != self._pk]
        values = [getattr(self, f) for f in fields]

        if getattr(self, self._pk, None):
            set_clause = ", ".join([f"{f}=?" for f in fields])
            query = f"UPDATE {self._table} SET {set_clause} WHERE {self._pk}=?"
            db.execute(query, (*values, getattr(self, self._pk)))
        else:
            placeholders = ", ".join(["?"] * len(fields))
            query = f"INSERT INTO {self._table} ({', '.join(fields)}) VALUES ({placeholders})"
            cursor = db.execute(query, tuple(values))
            setattr(self, self._pk, cursor.lastrowid)

    def delete(self):
        pk_val = getattr(self, self._pk, None)
        if pk_val is None:
            return
        db.execute(f"DELETE FROM {self._table} WHERE {self._pk}=?", (pk_val,))

    @classmethod
    def objects(cls) -> QuerySet:
        return QuerySet(cls)

    @classmethod
    def all(cls) -> List["Model"]:
        return cls.objects().all()

    @classmethod
    def get(cls, **kwargs) -> Optional["Model"]:
        return cls.objects().filter(**kwargs).first()

    @classmethod
    def filter(cls, **kwargs) -> QuerySet:
        return cls.objects().filter(**kwargs)

    @classmethod
    def bulk_create(cls, items: List[Dict[str, Any]]) -> List["Model"]:
        """Efficiently insert many objects, handling auto_now_add and defaults."""
        if not items:
            return []

        fields = [f for f in cls._fields if f != cls._pk]
        instances = []
        params_seq = []

        for item in items:
            instance = cls(**item)  # __init__ sets defaults

            # Apply auto_now_add / auto_now for DateTimeField
            for name, field in cls._fields.items():
                if isinstance(field, DateTimeField):
                    if field.auto_now_add and getattr(instance, name, None) is None:
                        setattr(instance, name, datetime.now().isoformat())
                    elif field.auto_now:
                        setattr(instance, name, datetime.now().isoformat())

            # Collect values in field order
            values = [getattr(instance, f) for f in fields]
            params_seq.append(tuple(values))
            instances.append(instance)

        placeholders = ", ".join(["?"] * len(fields))
        query = f"INSERT INTO {cls._table} ({', '.join(fields)}) VALUES ({placeholders})"
        db.executemany(query, params_seq)

        # Optional: fetch last inserted rowid range (only if no concurrent writes)
        # Uncomment the following block if you need ids populated:
        """
        last_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        first_id = last_id - len(instances) + 1
        for i, inst in enumerate(instances):
            setattr(inst, cls._pk, first_id + i)
        """
        return instances

    @classmethod
    def bulk_update(cls, instances: List["Model"], fields: List[str]) -> int:
        if not instances or not fields:
            return 0
        set_clause = ", ".join([f"{f}=?" for f in fields])
        query = f"UPDATE {cls._table} SET {set_clause} WHERE {cls._pk}=?"
        params_seq = []
        for inst in instances:
            values = [getattr(inst, f) for f in fields]
            values.append(getattr(inst, cls._pk))
            params_seq.append(tuple(values))
        cursor = db.executemany(query, params_seq)
        return cursor.rowcount

    def refresh_from_db(self):
        pk_val = getattr(self, self._pk, None)
        if pk_val is None:
            return
        row = db.execute(f"SELECT * FROM {self._table} WHERE {self._pk}=?", (pk_val,)).fetchone()
        if row:
            for key, value in dict(row).items():
                setattr(self, key, value)

    def __repr__(self):
        fields = ", ".join([f"{k}={getattr(self, k)}" for k in self._fields])
        return f"<{self.__class__.__name__} {fields}>"