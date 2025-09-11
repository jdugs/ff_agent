'use client';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AlertCircle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="p-6">
      <Card className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-danger-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">
          Something went wrong!
        </h2>
        <p className="text-dark-400 mb-6">
          {error.message || 'An unexpected error occurred'}
        </p>
        <Button onClick={reset} variant="primary">
          Try again
        </Button>
      </Card>
    </div>
  );
}