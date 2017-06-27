all:
	@echo "Please specify target. Current target(s) are: clean"

clean:
	find . -name "*.pyc" -exec rm -f {} +
	find . -name "*.py" -exec sed -i 's/[[:blank:]]\+$$//g' {} +

.PHONY: all clean
