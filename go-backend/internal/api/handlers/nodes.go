package handlers

import (
    "encoding/json"
    "net/http"

    "github.com/go-chi/chi/v5"
    "github.com/goranjovic55/LOGReport/internal/models"
    "github.com/goranjovic55/LOGReport/internal/nodes"
)

type NodesHandler struct {
    manager *nodes.Manager
}

func NewNodesHandler(manager *nodes.Manager) *NodesHandler {
    return &NodesHandler{manager: manager}
}

func (h *NodesHandler) GetAll(w http.ResponseWriter, r *http.Request) {
    nodes := h.manager.GetAll()
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(nodes)
}

func (h *NodesHandler) GetOne(w http.ResponseWriter, r *http.Request) {
    name := chi.URLParam(r, "name")
    node, err := h.manager.GetByName(name)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(node)
}

func (h *NodesHandler) Create(w http.ResponseWriter, r *http.Request) {
    var node models.Node
    if err := json.NewDecoder(r.Body).Decode(&node); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    if err := h.manager.Add(node); err != nil {
        http.Error(w, err.Error(), http.StatusConflict)
        return
    }

    if err := h.manager.Save(); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(node)
}

func (h *NodesHandler) Update(w http.ResponseWriter, r *http.Request) {
    name := chi.URLParam(r, "name")

    var node models.Node
    if err := json.NewDecoder(r.Body).Decode(&node); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    if err := h.manager.Update(name, node); err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }

    if err := h.manager.Save(); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(node)
}

func (h *NodesHandler) Delete(w http.ResponseWriter, r *http.Request) {
    name := chi.URLParam(r, "name")

    if err := h.manager.Delete(name); err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }

    if err := h.manager.Save(); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.WriteHeader(http.StatusNoContent)
}