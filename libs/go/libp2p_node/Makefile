test:
	go test -gcflags=-l -p 1 -timeout 0 -count 1 -covermode=atomic -coverprofile=coverage.txt -v ./...
	go tool cover -func=coverage.txt
lint:
	golines . -w
	golangci-lint run
	
build:
	go build
install:
	go get -v -t -d ./...
race_test:
	go test -gcflags=-l -p 1 -timeout 0 -count 1 -race -v ./...
