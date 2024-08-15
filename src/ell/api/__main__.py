import asyncio
import uvicorn
from argparse import ArgumentParser
from ell.api.config import Config
from ell.api.server import create_app
from ell.studio.logger import setup_logging


def main():
    setup_logging()
    parser = ArgumentParser(description="ELL API Server")
    parser.add_argument("--storage-dir", default=None,
                        help="Storage directory (default: None)")
    parser.add_argument("--pg-connection-string", default=None,
                        help="PostgreSQL connection string (default: None)")
    parser.add_argument("--mqtt-connection-string", default=None,
                        help="MQTT connection string (default: None)")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port to run the server on")
    parser.add_argument("--dev", action="store_true",
                        help="Run in development mode")
    args = parser.parse_args()

    config = Config(
        storage_dir=args.storage_dir,
        pg_connection_string=args.pg_connection_string,
        mqtt_connection_string=args.mqtt_connection_string,
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
