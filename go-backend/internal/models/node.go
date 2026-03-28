package models

type NodeToken struct {
    TokenID   string `json:"token_id"`
    TokenType string `json:"token_type"` // FBC/RPC/LOG/LIS
    Port      int    `json:"port"`
    Protocol  string `json:"protocol"`
}

type Node struct {
    Name      string      `json:"name"`
    IPAddress string      `json:"ip_address"`
    Status    string      `json:"status"` // offline/online/scanning/error
    Tokens    []NodeToken `json:"tokens"`
}