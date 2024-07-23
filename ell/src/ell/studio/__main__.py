import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    args = parser.parse_args()

    app = create_app(args.storage_dir)
    
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()