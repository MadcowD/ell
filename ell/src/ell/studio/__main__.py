import os
from argparse import ArgumentParser
from ell.studio.data_server import app, serializer

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    args = parser.parse_args()

    # Update the serializer's storage directory
    serializer.storage_dir = args.storage_dir

    # Run the Flask app
    app.run(debug=True)

if __name__ == "__main__":
    main()