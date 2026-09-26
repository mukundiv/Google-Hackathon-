import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

/** Which trend the operator is working on, carried across the five stages. */
interface Selection {
  trendId: string | null;
  setTrendId: (id: string | null) => void;
}

const Ctx = createContext<Selection>({ trendId: null, setTrendId: () => {} });

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [trendId, setTrendId] = useState<string | null>(null);
  const value = useMemo(() => ({ trendId, setTrendId }), [trendId]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useSelection = () => useContext(Ctx);
