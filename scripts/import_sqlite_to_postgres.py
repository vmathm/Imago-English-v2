import argparse
import sys
from collections import defaultdict, deque

from sqlalchemy import create_engine, MetaData, Table, select, text
from sqlalchemy.engine import Engine


EXCLUDE_TABLES = {"alembic_version"}


def reflect(engine: Engine) -> MetaData:
    md = MetaData()
    md.reflect(bind=engine)
    return md


def topo_sort_tables(target_md: MetaData, table_names: list[str]) -> list[str]:
    """
    Topologically sort tables based on FK dependencies in the TARGET schema.
    If B has FK -> A, then A must come before B.
    """
    deps: dict[str, set[str]] = {t: set() for t in table_names}
    reverse: dict[str, set[str]] = {t: set() for t in table_names}

    for name in table_names:
        t = target_md.tables.get(name)
        if t is None:
            continue
        for fk in t.foreign_keys:
            parent = fk.column.table.name
            if parent in deps and parent != name:
                deps[name].add(parent)
                reverse[parent].add(name)

    # Kahn's algorithm
    q = deque([t for t in table_names if not deps[t]])
    out: list[str] = []

    while q:
        n = q.popleft()
        out.append(n)
        for child in reverse[n]:
            deps[child].discard(n)
            if not deps[child]:
                q.append(child)

    # If cycle/unresolved, append remaining in original order (rare, but avoids hard fail)
    remaining = [t for t in table_names if t not in out]
    return out + remaining


def table_rowcount(engine: Engine, table_name: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()



def source_has_table(source_md: MetaData, name: str) -> bool:
    return name in source_md.tables


def target_has_table(target_md: MetaData, name: str) -> bool:
    return name in target_md.tables


def copy_table(source_engine: Engine, target_engine: Engine, table_name: str, batch_size: int = 2000) -> int:
    source_md = MetaData()
    target_md = MetaData()

    src = Table(table_name, source_md, autoload_with=source_engine)
    tgt = Table(table_name, target_md, autoload_with=target_engine)

    # Only insert columns that exist in BOTH (handles minor drift safely)
    common_cols = [c.name for c in tgt.columns if c.name in src.columns]
    if not common_cols:
        print(f"⚠️  Skipping {table_name}: no common columns found.")
        return 0

    src_sel = select(*[src.c[c] for c in common_cols])

    inserted = 0
    with source_engine.connect() as src_conn, target_engine.begin() as tgt_conn:
        result = src_conn.execute(src_sel)
        while True:
            rows = result.fetchmany(batch_size)
            if not rows:
                break
            payload = [dict(zip(common_cols, row)) for row in rows]
            tgt_conn.execute(tgt.insert(), payload)
            inserted += len(payload)

    return inserted


def fix_serial_sequences(target_engine: Engine, target_md: MetaData, table_names: list[str]) -> None:
    """
    If any table has an integer PK backed by a sequence (SERIAL/IDENTITY),
    bump it to max(pk). Safe no-op if not applicable.
    """
    with target_engine.begin() as conn:
        for name in table_names:
            t = target_md.tables.get(name)
            if t is None:
                continue
            pk_cols = list(t.primary_key.columns)
            if len(pk_cols) != 1:
                continue
            col = pk_cols[0]

            # Only try on integer-ish PKs
            coltype = str(col.type).lower()
            if "int" not in coltype:
                continue

            # pg_get_serial_sequence returns NULL if no owned sequence
            seq = conn.execute(
                text("SELECT pg_get_serial_sequence(:tbl, :col)"),
                {"tbl": name, "col": col.name},
            ).scalar_one_or_none()

            if not seq:
                continue

            conn.execute(
                text(f"SELECT setval(:seq, COALESCE((SELECT MAX(\"{col.name}\") FROM \"{name}\"), 0))"),
                {"seq": seq},
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite-url", required=True, help="e.g. sqlite:////tmp/backup.db")
    ap.add_argument("--postgres-url", default=None, help="defaults to env DATABASE_URL inside container")
    ap.add_argument("--force", action="store_true", help="allow import even if target tables are non-empty")
    ap.add_argument("--batch-size", type=int, default=2000)
    args = ap.parse_args()

    pg_url = args.postgres_url
    if pg_url is None:
        import os
        pg_url = os.getenv("DATABASE_URL")
    if not pg_url:
        print("❌ Missing Postgres URL. Set DATABASE_URL or pass --postgres-url.")
        sys.exit(2)

    source_engine = create_engine(args.sqlite_url)
    target_engine = create_engine(pg_url)

    source_md = reflect(source_engine)
    target_md = reflect(target_engine)

    # Import only tables that exist in BOTH schemas
    candidates = [
        name for name in target_md.tables.keys()
        if name not in EXCLUDE_TABLES and source_has_table(source_md, name)
    ]

    if not candidates:
        print("❌ No matching tables found to import. Check schemas and sqlite file path.")
        sys.exit(1)

    ordered = topo_sort_tables(target_md, candidates)

    # Safety: ensure target tables are empty unless --force
    non_empty = []
    for t in ordered:
        try:
            c = table_rowcount(target_engine, t)
        except Exception as e:
            print(f"❌ Could not count rows in target table {t}: {e}")
            sys.exit(1)
        if c > 0:
            non_empty.append((t, c))

    if non_empty and not args.force:
        print("❌ Target DB is not empty. Refusing to import.")
        for t, c in non_empty:
            print(f"   - {t}: {c} rows")
        print("If you're sure, rerun with --force.")
        sys.exit(1)

    print("✅ Starting import")
    print(f"   SQLite : {args.sqlite_url}")
    print(f"   Postgres: {pg_url.split('@')[-1] if '@' in pg_url else pg_url}")
    print("   Tables:", ", ".join(ordered))

    total = 0
    for t in ordered:
        inserted = copy_table(source_engine, target_engine, t, batch_size=args.batch_size)
        print(f"✅ {t}: inserted {inserted}")
        total += inserted

    # Fix sequences after bulk inserts
    target_md2 = reflect(target_engine)
    fix_serial_sequences(target_engine, target_md2, ordered)

    print(f"🎉 Done. Total rows inserted: {total}")


if __name__ == "__main__":
    main()