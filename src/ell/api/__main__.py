import asyncio
import os
import uvicorn
import logging
from argparse import ArgumentParser


from ell.api.config import Config
from ell.api.server import create_app
from ell.api.logger import setup_logging




def main():
    log_level = int(os.environ.get("LOG_LEVEL", logging.INFO))
    setup_logging(level=log_level)

    parser = ArgumentParser(description="ell api")
    parser.add_argument("--storage-dir", 
                        type=str,
                        default=os.getenv("ELL_STORAGE_DIR"),
                        help="Storage directory (default: None, env: ELL_STORAGE_DIR)")
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
    parser.add_argument("--minio-bucket", 
                        default=os.getenv("ELL_MINIO_BUCKET"),
                        help="MinIO bucket (default: None, env: ELL_MINIO_BUCKET)")
    parser.add_argument("--host", 
                        default=os.getenv("ELL_API_HOST") or "0.0.0.0",
                        help="Host to run the server on (default: '0.0.0.0', env: ELL_API_HOST)")
    parser.add_argument("--port", 
                        type=int, 
                        default=int(os.getenv("ELL_API_PORT") or 8081),
                        help="Port to run the server on (default: 8081, env: ELL_API_PORT)")
    parser.add_argument("--dev", 
                        action="store_true",
                        help="Run in development mode")
    args = parser.parse_args()

    config = Config(
        storage_dir=args.storage_dir,
        pg_connection_string=args.pg_connection_string,
        mqtt_connection_string=args.mqtt_connection_string,
        minio_endpoint=args.minio_endpoint,
        minio_access_key=args.minio_access_key,
        minio_secret_key=args.minio_secret_key,
        minio_bucket=args.minio_bucket,
    )

    app = create_app(config)

    loop = asyncio.new_event_loop()

    config = uvicorn.Config(
        app=app,
        host=args.host, 
        port=args.port,
        loop=loop  # type: ignore
    )
    server = uvicorn.Server(config)

    loop.create_task(server.serve())

    loop.run_forever()


if __name__ == "__main__":
    main()
