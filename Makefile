install: clean
	@mkdir -p ~/.config/OneDriveCLI
	pip uninstall -y ./dist/onedrivecli-*-py3-none-any.whl	
	python -m build
	pip install ./dist/onedrivecli-*-py3-none-any.whl
clean:
	rm -rf ./dist/*