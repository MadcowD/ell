import asyncio
import logging
import os
import socket
import time
import webbrowser
import uvicorn
from argparse import ArgumentParser
from contextlib import closing
from ell.studio.config import Config
from ell.studio.server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from watchfiles import awatch


logger = logging.getLogger(__file__)


def _socket_is_open(host, port) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0


def _setup_logging(level):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s] %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    parser = ArgumentParser(description="ell studio")
    parser.add_argument("--storage-dir" , 
                        default=os.getenv("ELL_STORAGE_DIR"),
                        help="Directory for filesystem serialize storage (default: None, env: ELL_STORAGE_DIR)")
    parser.add_argument("--pg-connection-string", 
                        default=os.getenv("ELL_PG_CONNECTION_STRING"),
                        help="PostgreSQL connection string (default: None, env: ELL_PG_CONNECTION_STRING)")
    parser.add_argument("--mqtt-connection-string", 
                        default=os.getenv("ELL_MQTT_CONNECTION_STRING"),
                        help="MQTT connection string (default: None, env: ELL_MQTT_CONNECTION_STRING)")
    parser.add_argument("--minio-endpoint", 
                        default=os.getenv("ELL_MINIO_ENDPOINT"),
                        help="MinIO endpoint (default: None, env: ELL_MINIO_ENDPOINT)")
    parser.add_argument("--minio-access-key", 
                        default=os.getenv("ELL_MINIO_ACCESS_KEY"),
                        help="MinIO access key (default: None, env: ELL_MINIO_ACCESS_KEY)")
    parser.add_argument("--minio-secret-key", 
                        default=os.getenv("ELL_MINIO_SECRET_KEY"),
                        help="MinIO secret key (default: None, env: ELL_MINIO_SECRET_KEY)")
    parser.add_argument("--minio-bucket", default=os.getenv("ELL_MINIO_BUCKET"),
                        help="MinIO bucket (default: None, env: ELL_MINIO_BUCKET)")
    parser.add_argument("--host", 
                        default=os.getenv("ELL_STUDIO_HOST") or "0.0.0.0",
                        help="Host to run the server on (default: 0.0.0.0, env: ELL_STUDIO_HOST)")
    parser.add_argument("--port", 
                        type=int, 
                        default=int(os.getenv("ELL_STUDIO_PORT") or 5555),
                        help="Port to run the server on (default: 5555, env: ELL_STUDIO_PORT)")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--dev-static-dir", default=None, help="Directory to serve static files from in development mode")
    parser.add_argument("--open", action="store_true", help="Opens the studio web UI in a browser")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enables debug logging for more verbose output")
    args = parser.parse_args()

    _setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    if args.dev:
        assert args.port == 5555, "Port must be 5555 in development mode"

    config = Config.create(
        storage_dir=args.storage_dir,
        pg_connection_string=args.pg_connection_string,
        mqtt_connection_string=args.mqtt_connection_string,
        minio_endpoint=args.minio_endpoint,
        minio_access_key=args.minio_access_key,
        minio_secret_key=args.minio_secret_key,
        minio_bucket=args.minio_bucket
    )
    app = create_app(config)

    if not args.dev:
        # In production mode, serve the built React app
        static_dir = Path(__file__).parent / "static"
        # app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            file_path = static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            else:
                return FileResponse(static_dir / "index.html")
    elif args.dev_static_dir:
        app.mount("/", StaticFiles(directory=args.dev_static_dir, html=True), name="static")

    # Respect Config.create behavior, which has fallback to env vars.
    db_path = Path(config.storage_dir) if config.storage_dir else None

    async def db_watcher(db_path, app):
        last_stat = None

        while True:
            await asyncio.sleep(0.1)  # Fixed interval of 0.1 seconds
            try:
                current_stat = db_path.stat()
                
                if last_stat is None:
                    logger.info(f"Database file found: {db_path}")
                    await app.notify_clients("database_updated")
                else:
                    # Use a threshold for time comparison to account for filesystem differences
                    time_threshold = 0.1  # 1 second threshold
                    time_changed = abs(current_stat.st_mtime - last_stat.st_mtime) > time_threshold
                    size_changed = current_stat.st_size != last_stat.st_size
                    inode_changed = current_stat.st_ino != last_stat.st_ino

                    if time_changed or size_changed or inode_changed:
                        logger.info(
                            f"Database changed: mtime {time.ctime(last_stat.st_mtime)} -> {time.ctime(current_stat.st_mtime)}, "
                            f"size {last_stat.st_size} -> {current_stat.st_size}, "
                            f"inode {last_stat.st_ino} -> {current_stat.st_ino}"
                        )
                        await app.notify_clients("database_updated")
                
                last_stat = current_stat
            except FileNotFoundError:
                if last_stat is not None:
                    logger.info(f"Database file deleted: {db_path}")
                    await app.notify_clients("database_updated")
                last_stat = None
                await asyncio.sleep(1)  # Wait a bit longer if the file is missing
            except Exception as e:
                logger.info(f"Error checking database file: {e}")
                await asyncio.sleep(1)  # Wait a bit longer on errors

    async def open_browser(host, port):
        while True:
            logger.debug(f"Checking TCP port {port} on {host} for readiness.")
            if _socket_is_open(host, port):
                url = f"http://{host}:{port}"
                logger.debug(f"Port is open, launching {url}.")
                webbrowser.open_new(url)
                return

            logger.debug(f"Port {port} was not open, retrying.")
            await asyncio.sleep(.1)

    # Start the database watcher
    loop = asyncio.new_event_loop()

    config = uvicorn.Config(app=app, host=args.host, port=args.port, loop=loop)
    server = uvicorn.Server(config)
    loop.create_task(server.serve())
    if db_path:
        loop.create_task(db_watcher(db_path, app))
    if args.open:
        loop.create_task(open_browser(args.host, args.port))
    loop.run_forever()

if __name__ == "__main__":
    main()
