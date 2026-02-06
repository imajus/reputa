import { Link } from 'react-router-dom';
import { ArrowRight, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Layout from '@/components/layout/Layout';
import MigrationVisualization from '@/components/landing/MigrationVisualization';
import StatsBar from '@/components/landing/StatsBar';

const Landing = () => {
  return (
    <Layout showFooter={false}>
      <div className="relative flex min-h-[calc(100vh-4rem)] flex-col">
        {/* Main Split Section */}
        <div className="flex flex-1 flex-col lg:flex-row">
          {/* Left Side - Content */}
          <div className="flex flex-1 flex-col justify-center px-6 py-12 lg:px-12 xl:px-20">
            <div className="mx-auto max-w-xl">
              {/* Badge */}
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm">
                <Zap className="h-4 w-4 text-primary" />
                <span className="text-primary">Powered by TEE</span>
              </div>
              
              <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight text-foreground md:text-5xl xl:text-6xl">
                Your DeFi History,
                <span className="block bg-gradient-to-r from-primary to-chart-2 bg-clip-text text-transparent">
                  Now on Sui
                </span>
              </h1>
              
              <p className="mb-8 text-lg text-muted-foreground md:text-xl">
                Don't start from zero. Migrate your proven Ethereum reputation to Sui and unlock premium benefits instantly.
              </p>
              
              <div className="flex flex-col gap-4 sm:flex-row">
                <Button size="lg" asChild className="group text-base">
                  <Link to="/analyze">
                    Start Migration
                    <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="text-base">
                  <a href="https://docs.reputa.io" target="_blank" rel="noopener noreferrer">
                    How It Works
                  </a>
                </Button>
              </div>
              
              {/* Trust indicators */}
              <div className="mt-12 flex items-center gap-6 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <span>Cryptographically verified</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <span>Privacy-preserving</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Right Side - Visualization */}
          <div className="relative hidden flex-1 overflow-hidden lg:block">
            <MigrationVisualization />
          </div>
        </div>
        
        {/* Bottom Stats Bar */}
        <StatsBar />
      </div>
    </Layout>
  );
};

export default Landing;
