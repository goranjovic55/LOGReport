export interface NodeToken {
  token_id: string;
  token_type: string; // FBC/RPC/LOG/LIS
  port: number;
  protocol: string;
}

export interface Node {
  name: string;
  ip_address: string;
  status: 'offline' | 'online' | 'scanning' | 'error';
  tokens: NodeToken[];
}