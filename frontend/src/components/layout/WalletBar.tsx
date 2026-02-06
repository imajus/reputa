import { ConnectButton } from '@rainbow-me/rainbowkit';

const WalletBar = () => {
  return (
    <div className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-end">
        <ConnectButton
          chainStatus="icon"
          showBalance={false}
        />
      </div>
    </div>
  );
};

export default WalletBar;
