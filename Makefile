install:
	pip3 install --use-pep517 .

install-dev:
	pip3 install --use-pep517 --editable .

uninstall:
	pip3 uninstall --yes govee-h5072-logger

clean:
	rm -rf *.egg-info build

docker-image:
	docker build --pull --no-cache --tag govee-h5072-logger .
