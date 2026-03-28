package config

type Config struct {
    Port       string
    NodesPath  string
    LogRoot    string
}

func New() *Config {
    return &Config{
        Port:      "8080",
        NodesPath: "./nodes.json",
        LogRoot:   "./",
    }
}