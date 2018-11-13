PYTHON ?= python
SRC_DIR = ./src
SRC = main.py
MAIN = main.py

run:
	${PYTHON} ${SRC_DIR}/${MAIN}

build:
	${PYTHON} -m compileall ${SRC_DIR}

clean:
	@net use x: /delete
	@rm -f ${FILENAME}
	$(foreach src,$(SRC), @rm -f $(SRC_DIR)/$(src)c)

.PHONY: clean test
