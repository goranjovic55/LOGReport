package api

import (
    "net/http"

    "github.com/go-chi/chi/v5"
    "github.com/rs/cors"

    "github.com/goranjovic55/LOGReport/internal/api/handlers"
    "github.com/goranjovic55/LOGReport/internal/nodes"
)

func NewRouter(nodeManager *nodes.Manager) http.Handler {
    r := chi.NewRouter()

    // CORS middleware
    corsHandler := cors.New(cors.Options{
        AllowedOrigins:   []string{"http://localhost:*", "http://127.0.0.1:*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"*"},
        AllowCredentials: true,
    })
    r.Use(corsHandler.Handler)

    // Health check
    r.Get("/api/health", handlers.HealthHandler)

    // Nodes API
    nodesHandler := handlers.NewNodesHandler(nodeManager)
    r.Route("/api/nodes", func(r chi.Router) {
        r.Get("/", nodesHandler.GetAll)
        r.Post("/", nodesHandler.Create)
        r.Get("/{name}", nodesHandler.GetOne)
        r.Put("/{name}", nodesHandler.Update)
        r.Delete("/{name}", nodesHandler.Delete)
    })

    return r
}