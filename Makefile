install:
	@mkdir -p ~/.config/OneDriveCLI
	pip uninstall -y ./dist/onedrivecli-0.0.1-py3-none-any.whl	
	python -m build
	pip install ./dist/onedrivecli-0.0.1-py3-none-any.whl
