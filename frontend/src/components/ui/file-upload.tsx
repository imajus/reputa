import { Upload, File, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface FileUploadButtonProps {
  onChange?: (file: File) => void;
  accept?: string;
  className?: string;
  file?: File;
  onReset?: () => void;
}

export const FileUploadButton = ({ onChange, accept, className, file, onReset }: FileUploadButtonProps) => {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && onChange) {
      onChange(selectedFile);
    }
  };
  if (file) {
    return (
      <div className={cn('rounded-lg border border-border/50 p-4', className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <File className="h-8 w-8 text-primary" />
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={onReset}>
            <X className="mr-1 h-4 w-4" />
            Reset
          </Button>
        </div>
      </div>
    );
  }
  return (
    <div className={cn('relative', className)}>
      <input
        type="file"
        accept={accept}
        onChange={handleFileChange}
        className="absolute inset-0 z-10 cursor-pointer opacity-0"
      />
      <div className="rounded-lg border-2 border-dashed border-border/50 p-8 text-center transition-colors hover:border-primary/50">
        <Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
        <Button variant="outline" className="pointer-events-none">
          Upload Document
        </Button>
        <p className="mt-2 text-sm text-muted-foreground">
          Click to upload supporting documents
        </p>
      </div>
    </div>
  );
};
