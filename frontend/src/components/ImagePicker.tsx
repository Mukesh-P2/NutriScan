import { useEffect, useRef, useState } from "react";

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
  max?: number;
}

/** Multi-image picker: add via file upload or camera capture, preview thumbnails, remove individually. */
export default function ImagePicker({ files, onChange, max = 6 }: Props) {
  const [previews, setPreviews] = useState<string[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const cameraInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f));
    setPreviews(urls);
    return () => urls.forEach((u) => URL.revokeObjectURL(u));
  }, [files]);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const incoming = Array.from(list);
    const combined = [...files, ...incoming].slice(0, max);
    onChange(combined);
  }

  function removeAt(idx: number) {
    onChange(files.filter((_, i) => i !== idx));
  }

  return (
    <div>
      <div className="flex flex-wrap gap-3">
        {previews.map((src, i) => (
          <div key={i} className="relative h-24 w-24 overflow-hidden rounded-lg ring-1 ring-slate-200">
            <img src={src} alt={`upload ${i + 1}`} className="h-full w-full object-cover" />
            <button
              type="button"
              onClick={() => removeAt(i)}
              className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-black/60 text-xs text-white"
              aria-label="Remove image"
            >
              ✕
            </button>
          </div>
        ))}

        {files.length < max && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => cameraInput.current?.click()}
              className="flex h-24 w-24 flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 text-slate-500 hover:border-emerald-400 hover:text-emerald-600"
            >
              <span className="text-2xl">📷</span>
              <span className="text-xs">Camera</span>
            </button>
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              className="flex h-24 w-24 flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 text-slate-500 hover:border-emerald-400 hover:text-emerald-600"
            >
              <span className="text-2xl">🖼️</span>
              <span className="text-xs">Upload</span>
            </button>
          </div>
        )}
      </div>

      <p className="mt-2 text-xs text-slate-400">
        {files.length}/{max} images. Add more photos (front, ingredients, nutrition table) for a fuller analysis.
      </p>

      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => addFiles(e.target.files)}
      />
      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(e) => addFiles(e.target.files)}
      />
    </div>
  );
}
