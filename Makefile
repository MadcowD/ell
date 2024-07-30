.PHONY: install npm-install npm-build

install: npm-install npm-build python-install

sync-version:
	git tag -f $(shell poetry version -s)

python-install: sync-version
	poetry self add poetry-dynamic-versioning
	poetry dynamic-versioning enable
	pip uninstall -y ell
	poetry install
	poetry build
	cd dist && pip install *.whl
	rm -rf dist

npm-install:
	@echo "Running npm install"
	cd ell-studio && npm install

npm-build:
	@echo "Running npm build"
	cd ell-studio && npm run build
	@echo "Copying static files"
	python -c "import os, shutil; \
	  source_dir = os.path.join('ell-studio', 'build'); \
	  target_dir = os.path.join('src', 'ell', 'studio', 'static'); \
	  shutil.rmtree(target_dir, ignore_errors=True); \
	  shutil.copytree(source_dir, target_dir); \
	  print(f'Copied static files from {source_dir} to {target_dir}')"

test:
	poetry run pytest -vvv
