import os
from argparse import ArgumentParser
from ell.studio.data_server import create_app

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    args = parser.parse_args()


    app = create_app(args.storage_dir)
    app.run(debug=True, port=8080)
    print('jho')

if __name__ == "__main__":
    main()