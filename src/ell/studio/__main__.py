import asyncio
import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import watchfiles
import importlib
import sys
import time

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    args = parser.parse_args()


    app = create_app()

    if not args.dev:
        # In production mode, serve the built React app
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))


    async def db_watcher(db_path, app):
        print("Starting db watcher")
        last_stat = None
        while True:
            try:
                current_stat = os.stat(db_path)
                if last_stat is None:
                    print(f"Database file found: {db_path}")
                    await app.notify_clients("database_updated")
                else:
                    # Use a threshold for time comparison to account for filesystem differences
                    time_threshold = 1  # 1 second threshold
                    time_changed = abs(current_stat.st_mtime - last_stat.st_mtime) > time_threshold
                    size_changed = current_stat.st_size != last_stat.st_size
                    inode_changed = current_stat.st_ino != last_stat.st_ino

                    if time_changed or size_changed or inode_changed:
                        print(f"Database changed: mtime {time.ctime(last_stat.st_mtime)} -> {time.ctime(current_stat.st_mtime)}, "
                              f"size {last_stat.st_size} -> {current_stat.st_size}, "
                              f"inode {last_stat.st_ino} -> {current_stat.st_ino}")
                        await app.notify_clients("database_updated")
                
                last_stat = current_stat
            except FileNotFoundError:
                if last_stat is not None:
                    print(f"Database file deleted: {db_path}")
                    await app.notify_clients("database_updated")
                last_stat = None
                await asyncio.sleep(1)  # Wait a bit longer if the file is missing
            except Exception as e:
                print(f"Error checking database file: {e}")
                await asyncio.sleep(1)  # Wait a bit longer on errors
            finally:
                await asyncio.sleep(1)  # Use a consistent sleep interval

    def get_dependencies(module_name):
        module = importlib.import_module(module_name)
        return list(set(sys.modules[name].__file__ for name in sys.modules if name.startswith(module_name.split('.')[0])))

    def reload_app():
        importlib.reload(sys.modules["ell.studio.data_server"])
        return create_app()

    async def run_server(server):
        await server.serve()

    async def watch_files(dependencies, server, config, loop):
        async for changes in watchfiles.awatch(*dependencies):
            print(f"Detected changes in {changes}. Reloading...")
            new_app = reload_app()
            await server.shutdown()
            config.app = new_app
            server.force_exit = False
            loop.create_task(run_server(server))

    async def main_async(args):
        db_path = os.path.join(args.storage_dir, "ell.db")
        dependencies = get_dependencies("ell.studio.data_server")

        config = uvicorn.Config(
            app=app,
            host=args.host,
            port=args.port,
            loop=asyncio.get_event_loop(),
        )
        server = uvicorn.Server(config)

        tasks = [
            asyncio.create_task(run_server(server)),
        ]
        # todo. figure out equivalent for other backends
        # maybe the server should broadcast a message to all clients on write instead of the db watcher approach
        if args.storage_dir:
            tasks.append(asyncio.create_task(db_watcher(db_path, app)))
        if args.dev:
            tasks.append(asyncio.create_task(watch_files(dependencies, server, config, asyncio.get_event_loop())))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()