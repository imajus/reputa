import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Lightbulb, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Layout from '@/components/layout/Layout';
import ProgressIndicator from '@/components/layout/ProgressIndicator';
import { useReputa } from '@/contexts/ReputaContext';

const AddressInput = () => {
  const navigate = useNavigate();
  const { setEvmAddress, setResolvedAddress } = useReputa();
  const [address, setAddress] = useState('');
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [isResolving, setIsResolving] = useState(false);

  // Validate address format
  const validateAddress = (value: string) => {
    const evmRegex = /^0x[a-fA-F0-9]{40}$/;
    const ensRegex = /^[a-zA-Z0-9-]+\.eth$/;
    return evmRegex.test(value) || ensRegex.test(value);
  };

  useEffect(() => {
    if (address.length === 0) {
      setIsValid(null);
    } else {
      setIsValid(validateAddress(address));
    }
  }, [address]);

  const handleContinue = async () => {
    if (!isValid) return;
    
    setIsResolving(true);
    
    // Simulate ENS resolution
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const resolved = address.endsWith('.eth') 
      ? '0x1234567890123456789012345678901234567890' 
      : address;
    
    setEvmAddress(address);
    setResolvedAddress(resolved);
    setIsResolving(false);
    
    navigate('/questionnaire');
  };

  return (
    <Layout>
      <div className="container max-w-2xl py-8">
        <ProgressIndicator currentStep={1} />
        
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Enter Your EVM Address</CardTitle>
            <p className="text-muted-foreground">
              We'll analyze your on-chain history from Ethereum and L2s
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="relative">
              <Input
                placeholder="0x... or vitalik.eth"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="h-14 pr-12 text-lg font-mono"
              />
              {isValid !== null && (
                <div className="absolute right-4 top-1/2 -translate-y-1/2">
                  {isValid ? (
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                  ) : (
                    <XCircle className="h-5 w-5 text-destructive" />
                  )}
                </div>
              )}
            </div>
            
            <div className="flex items-start gap-3 rounded-lg bg-primary/5 p-4">
              <Lightbulb className="h-5 w-5 shrink-0 text-primary" />
              <p className="text-sm text-muted-foreground">
                We'll analyze your transaction history across Ethereum, Arbitrum, Optimism, and other major L2s to build your reputation score.
              </p>
            </div>
            
            <Button 
              className="w-full" 
              size="lg"
              disabled={!isValid || isResolving}
              onClick={handleContinue}
            >
              {isResolving ? 'Resolving...' : 'Continue'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default AddressInput;
