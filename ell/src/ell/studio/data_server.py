from typing import Optional
from ell.stores.sql import SQLiteStore
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

def create_app(storage_dir: Optional[str] = None):
    storage_path = storage_dir or os.environ.get('ELL_STORAGE_DIR') or os.getcwd()
    assert storage_path, "ELL_STORAGE_DIR must be set"
    serializer = SQLiteStore(storage_path)

    app = Flask(__name__)
    CORS(app, resources={r"*": {"origins": "*"}})  # Enable CORS for all /api routes
    @app.route('/api/lmps', methods=['GET'])
    def get_lmps():
        filters = request.args.to_dict()
        lmps = serializer.get_lmps(**filters)
        return jsonify(lmps)

    @app.route('/api/lmps/search', methods=['GET'])
    def search_lmps():
        query = request.args.get('q', '')
        lmps = serializer.search_lmps(query)
        return jsonify(lmps)

    @app.route('/api/lmps/<lmp_id>', methods=['GET'])
    def get_lmp(lmp_id):
        lmps = serializer.get_lmps({'lmp_id': lmp_id})
        if lmps:
            return jsonify(lmps[0])
        else:
            return jsonify({"error": "LMP not found"}), 404

    @app.route('/api/invocations/<lmp_id>', methods=['GET'])
    def get_invocations(lmp_id):
        filters = request.args.to_dict()
        invocations = serializer.get_invocations(lmp_id, **filters)
        return jsonify(invocations)

    @app.route('/api/invocations/search', methods=['GET'])
    def search_invocations():
        query = request.args.get('q', '')
        invocations = serializer.search_invocations(query)
        return jsonify(invocations)

    @app.route('/api/lmps/<lmp_id>/versions', methods=['GET'])
    def get_lmp_versions(lmp_id):
        versions = serializer.get_lmp_versions(lmp_id)
        if versions:
            return jsonify(versions)
        else:
            return jsonify({"error": "LMP versions not found"}), 404

    @app.route('/api/lmps/latest', methods=['GET'])
    def get_latest_lmps():
        latest_lmps = serializer.get_latest_lmps()
        return jsonify(latest_lmps)

    return app