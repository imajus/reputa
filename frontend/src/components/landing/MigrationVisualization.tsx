import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface FloatingCard {
  id: string;
  label: string;
  value: string;
  x: number;
  y: number;
  delay: number;
  side: 'left' | 'right';
}

const leftCards: FloatingCard[] = [
  { id: 'eth1', label: 'Aave Position', value: '$12,450', x: 15, y: 20, delay: 0, side: 'left' },
  { id: 'eth2', label: 'Uniswap LP', value: '2.3 ETH', x: 8, y: 45, delay: 0.3, side: 'left' },
  { id: 'eth3', label: 'DeFi Age', value: '847 days', x: 20, y: 70, delay: 0.6, side: 'left' },
];

const rightCards: FloatingCard[] = [
  { id: 'sui1', label: 'Reputa Score', value: '847', x: 65, y: 25, delay: 1.2, side: 'right' },
  { id: 'sui2', label: 'Tier', value: 'Premium', x: 70, y: 50, delay: 1.5, side: 'right' },
  { id: 'sui3', label: 'APY Boost', value: '+2.5%', x: 62, y: 75, delay: 1.8, side: 'right' },
];

const MigrationVisualization = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [particlesActive, setParticlesActive] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    const timer = setTimeout(() => setParticlesActive(true), 800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      {/* Background Grid */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, hsl(var(--muted)) 1px, transparent 0)`,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Chain Icons */}
      <div className="absolute left-[15%] top-1/2 -translate-y-1/2">
        <div className={cn(
          "flex h-20 w-20 items-center justify-center rounded-2xl border border-border/50 bg-card shadow-lg transition-all duration-700",
          isVisible ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-10"
        )}>
          <div className="text-2xl font-bold text-foreground">Ξ</div>
        </div>
        <p className="mt-3 text-center text-sm font-medium text-muted-foreground">Ethereum</p>
      </div>

      <div className="absolute right-[15%] top-1/2 -translate-y-1/2">
        <div className={cn(
          "flex h-20 w-20 items-center justify-center rounded-2xl border border-primary/50 bg-primary/10 shadow-lg shadow-primary/20 transition-all duration-700 delay-500",
          isVisible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-10"
        )}>
          <div className="text-2xl font-bold text-primary">S</div>
        </div>
        <p className="mt-3 text-center text-sm font-medium text-primary">Sui</p>
      </div>

      {/* Migration Flow Arrow */}
      <svg className="absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2" viewBox="0 0 100 100">
        {/* Dashed path */}
        <path
          d="M 20 50 Q 50 30 80 50"
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth="2"
          strokeDasharray="4 4"
          className={cn(
            "transition-opacity duration-500 delay-300",
            isVisible ? "opacity-100" : "opacity-0"
          )}
        />
        {/* Animated particle along path */}
        {particlesActive && (
          <>
            <circle r="4" fill="hsl(var(--primary))">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                path="M 20 50 Q 50 30 80 50"
              />
            </circle>
            <circle r="3" fill="hsl(var(--chart-2))" opacity="0.7">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                path="M 20 50 Q 50 30 80 50"
                begin="0.5s"
              />
            </circle>
            <circle r="2" fill="hsl(var(--primary))" opacity="0.5">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                path="M 20 50 Q 50 30 80 50"
                begin="1s"
              />
            </circle>
          </>
        )}
      </svg>

      {/* Floating Cards - Left (Ethereum) */}
      {leftCards.map((card) => (
        <div
          key={card.id}
          className={cn(
            "absolute rounded-lg border border-border/50 bg-card/90 px-4 py-3 shadow-md backdrop-blur-sm transition-all duration-700",
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          )}
          style={{
            left: `${card.x}%`,
            top: `${card.y}%`,
            transitionDelay: `${card.delay}s`,
            animation: isVisible ? `float 4s ease-in-out infinite ${card.delay}s` : 'none',
          }}
        >
          <p className="text-xs text-muted-foreground">{card.label}</p>
          <p className="text-sm font-semibold text-foreground">{card.value}</p>
        </div>
      ))}

      {/* Floating Cards - Right (Sui) */}
      {rightCards.map((card) => (
        <div
          key={card.id}
          className={cn(
            "absolute rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 shadow-md shadow-primary/10 backdrop-blur-sm transition-all duration-700",
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          )}
          style={{
            left: `${card.x}%`,
            top: `${card.y}%`,
            transitionDelay: `${card.delay}s`,
            animation: isVisible ? `float 4s ease-in-out infinite ${card.delay + 0.5}s` : 'none',
          }}
        >
          <p className="text-xs text-primary/70">{card.label}</p>
          <p className="text-sm font-semibold text-primary">{card.value}</p>
        </div>
      ))}

      {/* Glow effects */}
      <div className="absolute left-[15%] top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-muted/20 blur-3xl" />
      <div className="absolute right-[15%] top-1/2 h-40 w-40 -translate-y-1/2 translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
};

export default MigrationVisualization;
