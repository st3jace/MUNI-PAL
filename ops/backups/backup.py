"""Encrypted public-schema backups; never prints credentials or client records.

Supabase owns its internal schemas. BFMS accounts and all Register bytes live in
public. The managed Supabase backup remains the full-platform recovery layer.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import tarfile
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import boto3
import psycopg2
from botocore.config import Config
from psycopg2 import sql

REQUIRED = {
    "alembic_version",
    "users",
    "register_deals",
    "register_documents",
    "register_folders",
    "register_reports",
    "register_payment_reversals",
}
PREFIX = "munipal/public-v1/"
OBJECT_PATTERN = re.compile(r"^munipal/public-v1/\d{8}T\d{6}Z-[0-9a-f]{12}\.tar\.age$")


def run(args, *, env=None, input=None):
    """Keep subprocess errors out of hosted logs: they can contain source data."""
    result = subprocess.run(
        args,
        env=env,
        input=input,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=1800,
    )
    if result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} failed (exit {result.returncode})")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_env():
    env = dict(os.environ)
    for target, source in {
        "PGHOST": "POSTGRES_HOST",
        "PGPORT": "POSTGRES_PORT",
        "PGUSER": "POSTGRES_USER",
        "PGPASSWORD": "POSTGRES_PASSWORD",
        "PGDATABASE": "POSTGRES_DB",
    }.items():
        env[target] = os.environ[source]
    env["PGSSLMODE"] = "require"
    env["PGCONNECT_TIMEOUT"] = "20"
    return env


def connect(env):
    return psycopg2.connect(
        host=env["PGHOST"],
        port=env["PGPORT"],
        user=env["PGUSER"],
        password=env["PGPASSWORD"],
        dbname=env["PGDATABASE"],
        sslmode=env.get("PGSSLMODE", "require"),
        connect_timeout=20,
        options="-c timezone=UTC -c datestyle=ISO,YMD -c statement_timeout=1200000",
    )


def inventory(conn):
    """Hash every restored value, including password hashes and binary contents."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
                   COALESCE(c.relacl::text, '')
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='public' AND c.relkind IN ('r','p') ORDER BY c.relname
        """)
        tables = cur.fetchall()
        if not REQUIRED.issubset({row[0] for row in tables}):
            raise RuntimeError("Required BFMS tables are missing")
        cur.execute("SELECT version_num FROM public.alembic_version ORDER BY version_num")
        versions = [row[0] for row in cur.fetchall()]
        cur.execute(
            "SELECT row_to_json(p)::text FROM pg_policies p WHERE schemaname='public' ORDER BY tablename, policyname"
        )
        policies = [json.loads(row[0]) for row in cur.fetchall()]
    result = {"versions": versions, "policies": policies, "tables": {}}
    for name, rls, force_rls, acl in tables:
        checksum = hashlib.sha256()
        count = 0
        with conn.cursor(name="backup_rows") as rows:
            rows.itersize = 32
            rows.execute(
                sql.SQL(
                    'SELECT row_to_json(t)::text FROM public.{} t ORDER BY row_to_json(t)::text COLLATE "C"'
                ).format(sql.Identifier(name))
            )
            for (row,) in rows:
                raw = row.encode("utf-8")
                checksum.update(len(raw).to_bytes(8, "big"))
                checksum.update(raw)
                count += 1
        result["tables"][name] = {
            "rows": count,
            "sha256": checksum.hexdigest(),
            "rls": rls,
            "force_rls": force_rls,
            "acl": acl,
        }
    for name in ("register_documents", "register_reports"):
        with conn.cursor(name="backup_blobs") as rows:
            rows.itersize = 1
            rows.execute(
                sql.SQL("SELECT content, sha256 FROM public.{}").format(sql.Identifier(name))
            )
            for content, expected in rows:
                if hashlib.sha256(bytes(content)).hexdigest() != expected:
                    raise RuntimeError("Stored document/report checksum mismatch")
    return result


def capture(directory, env):
    dump = directory / "database.dump"
    with connect(env) as conn:
        conn.set_session(isolation_level="REPEATABLE READ", readonly=True)
        with conn.cursor() as cur:
            cur.execute("SELECT pg_export_snapshot()")
            snapshot = cur.fetchone()[0]
            cur.execute(
                "SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' ORDER BY rolname"
            )
            roles = [row[0] for row in cur.fetchall()]
        started = datetime.now(UTC).isoformat()
        run(
            [
                "pg_dump",
                "--format=custom",
                "--schema=public",
                "--no-owner",
                "--lock-wait-timeout=60000",
                "--snapshot=" + snapshot,
                "--file=" + str(dump),
            ],
            env=env,
        )
        manifest = {
            "format": 1,
            "started_at": started,
            "dump_sha256": digest(dump),
            "roles": roles,
            "inventory": inventory(conn),
        }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


@contextmanager
def temporary_postgres(directory):
    """Always restore into a new isolated local cluster, never a supplied database."""
    cluster = directory / "restore-cluster"
    password_file = directory / "restore-password"
    password = secrets.token_urlsafe(32)
    password_file.write_text(password, encoding="utf-8")
    password_file.chmod(0o600)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    run(
        [
            "initdb",
            "-D",
            str(cluster),
            "-U",
            "postgres",
            "-A",
            "scram-sha-256",
            "--pwfile=" + str(password_file),
            "--no-locale",
            "-E",
            "UTF8",
        ]
    )
    env = {
        **os.environ,
        "PGHOST": "127.0.0.1",
        "PGPORT": str(port),
        "PGUSER": "postgres",
        "PGPASSWORD": password,
        "PGDATABASE": "postgres",
        "PGSSLMODE": "disable",
    }
    # Avoid the image's /var/run socket directory; it may not be writable.
    options = f"-h 127.0.0.1 -p {port}"
    if os.name != "nt":
        options += f" -k {directory}"
    started = False
    try:
        run(
            [
                "pg_ctl",
                "-D",
                str(cluster),
                "-l",
                str(directory / "restore.log"),
                "-o",
                options,
                "-w",
                "start",
            ]
        )
        started = True
        yield env
    finally:
        if started:
            run(["pg_ctl", "-D", str(cluster), "-m", "immediate", "-w", "stop"])


def verify_restore(directory, manifest):
    dump = directory / "database.dump"
    if digest(dump) != manifest["dump_sha256"]:
        raise RuntimeError("Dump checksum mismatch")
    with temporary_postgres(directory) as env:
        with connect(env) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                for role in manifest["roles"]:
                    if role != "postgres":
                        # ACL dependencies only: no passwords or login privileges.
                        cur.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
                # initdb creates an empty public schema; the dump recreates it.
                cur.execute("DROP SCHEMA public")
        run(
            ["pg_restore", "--exit-on-error", "--no-owner", "--dbname=postgres", str(dump)], env=env
        )
        with connect(env) as conn:
            if inventory(conn) != manifest["inventory"]:
                raise RuntimeError("Restored database differs from the backup snapshot")


def storage():
    endpoint = os.environ["AWS_ENDPOINT_URL"]
    if not endpoint.startswith("https://"):
        raise RuntimeError("Backup storage requires HTTPS")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "auto"),
        config=Config(s3={"addressing_style": "virtual"}, retries={"max_attempts": 5}),
    ), os.environ["BUCKET_NAME"]


def expired_keys(objects, now, keep_days=30):
    """Only this job's dated objects; never delete arbitrary bucket contents."""
    if keep_days < 30:
        raise RuntimeError("Retention may not be shorter than 30 days")
    cutoff = now - timedelta(days=keep_days)
    return [
        o["Key"]
        for o in objects
        if OBJECT_PATTERN.fullmatch(o["Key"]) and o["LastModified"] < cutoff
    ]


def backup():
    os.umask(0o077)
    recipient = os.environ["BACKUP_AGE_RECIPIENT"]
    if not recipient.startswith("age1"):
        raise RuntimeError("Missing age public recipient")
    client, bucket = storage()
    with tempfile.TemporaryDirectory(prefix="munipal-backup-") as tmp:
        directory = Path(tmp)
        manifest = capture(directory, source_env())
        verify_restore(directory, manifest)
        archive = directory / "backup.tar"
        with tarfile.open(archive, "w") as tar:
            for name in ("database.dump", "manifest.json"):
                tar.add(directory / name, arcname=name)
        encrypted = directory / "backup.tar.age"
        run(
            ["age", "--encrypt", "--recipient", recipient, "--output", str(encrypted), str(archive)]
        )
        key = (
            PREFIX
            + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + secrets.token_hex(6)
            + ".tar.age"
        )
        checksum = digest(encrypted)
        client.upload_file(
            str(encrypted),
            bucket,
            key,
            ExtraArgs={"ContentType": "application/octet-stream", "Metadata": {"sha256": checksum}},
        )
        downloaded = directory / "readback.age"
        client.download_file(bucket, key, str(downloaded))
        if digest(downloaded) != checksum:
            raise RuntimeError("Uploaded backup readback failed")
        receipt = {
            "format": 1,
            "snapshot_at": manifest["started_at"],
            "completed_at": datetime.now(UTC).isoformat(),
            "key": key,
            "sha256": checksum,
            "bytes": encrypted.stat().st_size,
            "tables": len(manifest["inventory"]["tables"]),
            "restore_verified": True,
            "encryption": "age-X25519",
        }
        client.put_object(
            Bucket=bucket,
            Key=PREFIX + "latest-success.json",
            Body=json.dumps(receipt).encode(),
            ContentType="application/json",
        )
        # Retention is applied only after a new fully verified copy exists.
        now = datetime.now(UTC)
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=PREFIX):
            for old_key in expired_keys(page.get("Contents", []), now):
                client.delete_object(Bucket=bucket, Key=old_key)
        print(json.dumps({"status": "backup_verified", **receipt}), flush=True)


def monitor():
    client, bucket = storage()
    receipt = json.loads(
        client.get_object(Bucket=bucket, Key=PREFIX + "latest-success.json")["Body"].read()
    )
    validate_receipt(receipt, datetime.now(UTC))
    head = client.head_object(Bucket=bucket, Key=receipt["key"])
    if (
        head["ContentLength"] != receipt["bytes"]
        or head.get("Metadata", {}).get("sha256") != receipt["sha256"]
    ):
        raise RuntimeError("Latest backup object is missing or changed")
    print(json.dumps({"status": "backup_fresh", "snapshot_at": receipt["snapshot_at"]}), flush=True)


def validate_receipt(receipt, now):
    age = now - datetime.fromisoformat(receipt["snapshot_at"])
    if age > timedelta(hours=26) or age < timedelta(minutes=-5):
        raise RuntimeError("No recent verified backup (26 hour maximum)")
    if not receipt.get("restore_verified") or not OBJECT_PATTERN.fullmatch(receipt["key"]):
        raise RuntimeError("Invalid backup receipt")


def rehearse(identity, object_key=None):
    """Download, decrypt and restore; private identity stays on the operator device."""
    os.umask(0o077)
    client, bucket = storage()
    receipt = json.loads(
        client.get_object(Bucket=bucket, Key=PREFIX + "latest-success.json")["Body"].read()
    )
    key = object_key or receipt["key"]
    if not OBJECT_PATTERN.fullmatch(key):
        raise RuntimeError("Invalid backup key")
    with tempfile.TemporaryDirectory(prefix="munipal-rehearsal-") as tmp:
        directory = Path(tmp)
        encrypted = directory / "backup.age"
        client.download_file(bucket, key, str(encrypted))
        if key == receipt["key"] and digest(encrypted) != receipt["sha256"]:
            raise RuntimeError("Downloaded backup checksum mismatch")
        archive = directory / "backup.tar"
        run(
            [
                "age",
                "--decrypt",
                "--identity",
                str(identity),
                "--output",
                str(archive),
                str(encrypted),
            ]
        )
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            if (
                {m.name for m in members} != {"database.dump", "manifest.json"}
                or len(members) != 2
                or any(not m.isfile() for m in members)
            ):
                raise RuntimeError("Unexpected backup archive contents")
            for member in members:
                with (
                    tar.extractfile(member) as source,
                    (directory / member.name).open("wb") as target,
                ):
                    import shutil

                    shutil.copyfileobj(source, target)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        verify_restore(directory, manifest)
        result = {
            "status": "recovery_rehearsal_passed",
            "key": key,
            "snapshot_at": manifest["started_at"],
            "tables": len(manifest["inventory"]["tables"]),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        print(json.dumps(result), flush=True)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["backup", "monitor", "rehearse"])
    parser.add_argument("--identity", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "backup":
            backup()
        elif args.mode == "monitor":
            monitor()
        else:
            if not args.identity:
                raise RuntimeError("Recovery identity file required")
            rehearse(args.identity)
    except Exception as error:
        # Do not emit raw DB/client/SDK exceptions, which may include sensitive data.
        print(
            json.dumps(
                {"status": "failed", "phase": args.mode, "error_type": type(error).__name__}
            ),
            flush=True,
        )
        raise SystemExit(1) from None
