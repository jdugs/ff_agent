import { LoadingSpinner } from "@/components/ui/LoadingSpinner";


export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-dark-400">Loading...</p>
      </div>
    </div>
  );
}