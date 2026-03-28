import { fetchApi } from './client';
import type { Node } from '../types/node';

export const nodesApi = {
  getAll: () => fetchApi<Node[]>('/nodes'),
  getOne: (name: string) => fetchApi<Node>(`/nodes/${name}`),
  create: (node: Node) => fetchApi<Node>('/nodes', {
    method: 'POST',
    body: JSON.stringify(node),
  }),
  update: (name: string, node: Node) => fetchApi<Node>(`/nodes/${name}`, {
    method: 'PUT',
    body: JSON.stringify(node),
  }),
  delete: (name: string) => fetchApi<void>(`/nodes/${name}`, {
    method: 'DELETE',
  }),
};