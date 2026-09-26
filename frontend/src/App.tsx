import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, HashRouter as Router, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BrandPortalPage } from "./pages/BrandPortalPage";
import { CapturePage } from "./pages/CapturePage";
import { CreatorsPage } from "./pages/CreatorsPage";
import { LearningPage } from "./pages/LearningPage";
import { PortfolioPage } from "./pages/PortfolioPage";
import { ScoutPage } from "./pages/ScoutPage";
import { SelectionProvider } from "./state";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: 1 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SelectionProvider>
        <Router>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<BrandPortalPage />} />
              <Route path="/scout" element={<ScoutPage />} />
              <Route path="/capture" element={<CapturePage />} />
              <Route path="/creators" element={<CreatorsPage />} />
              <Route path="/portfolio" element={<PortfolioPage />} />
              <Route path="/learning" element={<LearningPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </Router>
      </SelectionProvider>
    </QueryClientProvider>
  );
}
