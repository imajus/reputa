import { Link } from 'react-router-dom';
import { FileText, Github } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <img src="/blowfish.png" alt="Reputa" className="h-8 w-8" />
          <span className="text-xl font-bold text-foreground">Reputa</span>
        </Link>
        
        <nav className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <a href="https://docs.reputa.io" target="_blank" rel="noopener noreferrer">
              <FileText className="mr-2 h-4 w-4" />
              Docs
            </a>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <a href="https://github.com/reputa" target="_blank" rel="noopener noreferrer">
              <Github className="mr-2 h-4 w-4" />
              GitHub
            </a>
          </Button>
        </nav>
      </div>
    </header>
  );
};

export default Header;
