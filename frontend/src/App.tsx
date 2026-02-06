import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { WagmiProvider } from 'wagmi';
import { RainbowKitProvider, lightTheme } from '@rainbow-me/rainbowkit';
import { ReputaProvider } from "@/contexts/ReputaContext";
import { config } from '@/lib/wagmi';
import Landing from "./pages/Landing";
import AddressInput from "./pages/AddressInput";
import Questionnaire from "./pages/Questionnaire";
import Analyzing from "./pages/Analyzing";
import ScoreReview from "./pages/ScoreReview";
import WalletConnect from "./pages/WalletConnect";
import Success from "./pages/Success";
import DemoProtocol from "./pages/DemoProtocol";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const customTheme = lightTheme({
  accentColor: 'hsl(var(--primary))',
  accentColorForeground: 'hsl(var(--primary-foreground))',
  borderRadius: 'medium',
  fontStack: 'system',
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={customTheme}>
          <TooltipProvider>
            <ReputaProvider>
              <Toaster />
              <Sonner />
              <BrowserRouter>
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route path="/analyze" element={<AddressInput />} />
                  <Route path="/questionnaire" element={<Questionnaire />} />
                  <Route path="/analyzing" element={<Analyzing />} />
                  <Route path="/score" element={<ScoreReview />} />
                  <Route path="/record" element={<WalletConnect />} />
                  <Route path="/success" element={<Success />} />
                  <Route path="/demo" element={<DemoProtocol />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </BrowserRouter>
            </ReputaProvider>
          </TooltipProvider>
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  </QueryClientProvider>
);

export default App;
