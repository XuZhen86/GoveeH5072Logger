install:
	pip3 install .

install-dev:
	pip3 install --editable .

uninstall:
	pip3 uninstall --yes govee-h5072-logger

clean:
	rm -rf *.egg-info build

docker-image:
	docker build -t govee-h5072-logger .
