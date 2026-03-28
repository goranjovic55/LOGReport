import { create } from 'zustand';
import type { Node } from '../types/node';

interface NodesState {
  nodes: Node[];
  selectedNode: Node | null;
  isLoading: boolean;
  error: string | null;
  setNodes: (nodes: Node[]) => void;
  setSelectedNode: (node: Node | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useNodesStore = create<NodesState>((set) => ({
  nodes: [],
  selectedNode: null,
  isLoading: false,
  error: null,
  setNodes: (nodes) => set({ nodes }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));