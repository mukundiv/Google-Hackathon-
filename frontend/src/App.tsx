import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, HashRouter as Router, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BrandPortalPage } from "./pages/BrandPortalPage";
import { CapturePage } from "./pages/CapturePage";
import { CreatorsPage } from "./pages/CreatorsPage";
import { LearningPage } from "./pages/LearningPage";
import { PortfolioPage } from "./pages/PortfolioPage";
import { ScoutPage } from "./pages/ScoutPage";
import { LayoutV2 } from "./v2/Layout";
import { BrandPage as BrandPageV2 } from "./v2/pages/BrandPage";
import { CapturePage as CapturePageV2 } from "./v2/pages/CapturePage";
import { CreatorsPage as CreatorsPageV2 } from "./v2/pages/CreatorsPage";
import { LearningPage as LearningPageV2 } from "./v2/pages/LearningPage";
import { PortfolioPage as PortfolioPageV2 } from "./v2/pages/PortfolioPage";
import { ScoutPage as ScoutPageV2 } from "./v2/pages/ScoutPage";
import { SelectionProvider } from "./state";

/** Which skin to render, fixed at build time.
 *
 *  "youtube" is the simplified, YouTube-flavoured version: same data, same
 *  engine, same charts — plain language on the surface with the technical
 *  detail one click away. Both are built from this one tree so the two never
 *  drift apart.
 */
const SKIN = import.meta.env.VITE_SKIN === "youtube" ? "youtube" : "classic";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: 1 } },
});

const SCREENS =
  SKIN === "youtube"
    ? {
        Layout: LayoutV2,
        Brand: BrandPageV2,
        Scout: ScoutPageV2,
        Capture: CapturePageV2,
        Creators: CreatorsPageV2,
        Portfolio: PortfolioPageV2,
        Learning: LearningPageV2,
      }
    : {
        Layout,
        Brand: BrandPortalPage,
        Scout: ScoutPage,
        Capture: CapturePage,
        Creators: CreatorsPage,
        Portfolio: PortfolioPage,
        Learning: LearningPage,
      };

export default function App() {
  const S = SCREENS;
  return (
    <QueryClientProvider client={queryClient}>
      <SelectionProvider>
        <Router>
          <Routes>
            <Route element={<S.Layout />}>
              <Route path="/" element={<S.Brand />} />
              <Route path="/scout" element={<S.Scout />} />
              <Route path="/capture" element={<S.Capture />} />
              <Route path="/creators" element={<S.Creators />} />
              <Route path="/portfolio" element={<S.Portfolio />} />
              <Route path="/learning" element={<S.Learning />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </Router>
      </SelectionProvider>
    </QueryClientProvider>
  );
}
