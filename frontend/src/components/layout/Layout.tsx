import { ReactNode } from "react";
import Header from "./Header";
import WalletBar from "./WalletBar";

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      {/* <WalletBar /> */}
      <main className="flex-1">{children}</main>
    </div>
  );
};

export default Layout;
