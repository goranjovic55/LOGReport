package main

import (
    "flag"
    "fmt"
    "log"
    "net/http"

    "github.com/goranjovic55/LOGReport/internal/api"
    "github.com/goranjovic55/LOGReport/internal/nodes"
)

func main() {
    var (
        port     = flag.String("port", "8080", "Server port")
        nodesPath = flag.String("nodes", "./nodes.json", "Path to nodes.json file")
        logRoot  = flag.String("log-root", "./", "Root directory for logs")
    )
    flag.Parse()

    _ = logRoot // Reserved for future use

    // Initialize node manager
    nodeManager := nodes.NewManager(*nodesPath)
    if err := nodeManager.Load(); err != nil {
        log.Fatalf("Failed to load nodes: %v", err)
    }

    // Create router
    router := api.NewRouter(nodeManager)

    // Serve static files (React build output)
    fs := http.FileServer(http.Dir("./web/dist"))
    http.Handle("/", fs)
    http.Handle("/api/", router)

    addr := fmt.Sprintf(":%s", *port)
    log.Printf("LOGReport server starting on %s", addr)
    log.Printf("Nodes file: %s", *nodesPath)
    log.Printf("Serving static files from ./web/dist")

    if err := http.ListenAndServe(addr, nil); err != nil {
        log.Fatalf("Server failed: %v", err)
    }
}