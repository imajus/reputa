import { ReactNode } from 'react';
import Header from './Header';
import Footer from './Footer';
import WalletBar from './WalletBar';

interface LayoutProps {
  children: ReactNode;
  showFooter?: boolean;
}

const Layout = ({ children, showFooter = true }: LayoutProps) => {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <WalletBar />
      <main className="flex-1">{children}</main>
      {showFooter && <Footer />}
    </div>
  );
};

export default Layout;
