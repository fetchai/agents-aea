test:
	go test -gcflags=-l -p 1 -timeout 0 -count 1 -coverprofile=coverage.out -v ./... 
	go tool cover -func=coverage.out

lint:
	golines . -w
	golangci-lint run
	
build:
	go build
install:
	go get -v -t -d ./...