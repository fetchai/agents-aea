module seller_agent

go 1.14

replace aealite => ../aealite

require (
	aealite v0.0.0-00010101000000-000000000000
	github.com/golang/protobuf v1.5.2
	github.com/sirupsen/logrus v1.8.1
	google.golang.org/protobuf v1.28.1
)
