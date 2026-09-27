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
import { LayoutV3 } from "./v3/Layout";
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
 *  detail one click away. "kairos" is a third presentation of that same
 *  plain-language console under its own identity. All three are built from
 *  this one tree, over one data layer and one set of charts, so they cannot
 *  drift apart or disagree about a number.
 */
const SCREENS_BY_SKIN = {
  classic: {
    Layout,
    Brand: BrandPortalPage,
    Scout: ScoutPage,
    Capture: CapturePage,
    Creators: CreatorsPage,
    Portfolio: PortfolioPage,
    Learning: LearningPage,
  },
  youtube: {
    Layout: LayoutV2,
    Brand: BrandPageV2,
    Scout: ScoutPageV2,
    Capture: CapturePageV2,
    Creators: CreatorsPageV2,
    Portfolio: PortfolioPageV2,
    Learning: LearningPageV2,
  },
  // KAIROS is a different identity over the same six screens, not a fork of
  // them: it supplies its own shell and its own token set, and reuses the
  // plain-language pages unchanged. Copying them would let the two drift, and
  // the whole point of showing it beside version 2 is that only the
  // presentation differs.
  kairos: {
    Layout: LayoutV3,
    Brand: BrandPageV2,
    Scout: ScoutPageV2,
    Capture: CapturePageV2,
    Creators: CreatorsPageV2,
    Portfolio: PortfolioPageV2,
    Learning: LearningPageV2,
  },
} as const;

type Skin = keyof typeof SCREENS_BY_SKIN;

const requested = import.meta.env.VITE_SKIN as string | undefined;
const SKIN: Skin = requested && requested in SCREENS_BY_SKIN ? (requested as Skin) : "classic";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: 1 } },
});

const SCREENS = SCREENS_BY_SKIN[SKIN];

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
