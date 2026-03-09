import Image from "next/image";

import type { UploadFileType } from "@/types/upload";

interface ImagePreviewProps {
  fileUrl: string;
  fileType: UploadFileType;
}

export function ImagePreview({ fileUrl, fileType }: ImagePreviewProps) {
  if (fileType === "pdf") {
    return (
      <div className="rounded-xl bg-gray-100 p-6 shadow-inner">
        <div className="rounded-xl bg-white p-2 shadow-md">
          <iframe
            src={fileUrl}
            title="Vista previa del PDF seleccionado"
            className="h-[500px] w-full rounded-lg border border-slate-200"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-gray-100 p-6 shadow-inner">
      <div className="flex justify-center rounded-xl bg-white p-4 shadow-md">
        <Image
          src={fileUrl}
          alt="Vista previa de la imagen seleccionada"
          width={1600}
          height={900}
          unoptimized
          className="h-auto max-h-[500px] w-auto max-w-full object-contain"
        />
      </div>
    </div>
  );
}
