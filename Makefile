.PHONY: clean coverage beta test lint typing
init:
	python -m pip install --upgrade pip flit
	flit install
	pre-commit install
coverage:
	py.test --verbose --cov-report term-missing --cov-report xml --cov=aioweenect tests
build:
	flit build
clean:
	rm -rf dist/
publish:
	flit --repository pypi publish
beta:
	flit --repository testpypi publish
test:
	py.test tests
lint:
	flake8 aioweenect
	pylint --rcfile=.pylintrc aioweenect
	black --check aioweenect
typing:
	mypy aioweenect
all: test lint typing
