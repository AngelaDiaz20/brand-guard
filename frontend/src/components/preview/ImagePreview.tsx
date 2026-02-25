import Image from "next/image";

interface ImagePreviewProps {
  imageUrl: string;
}

export function ImagePreview({ imageUrl }: ImagePreviewProps) {
  return (
    <div className="rounded-xl bg-gray-100 p-6 shadow-inner">
      <div className="flex justify-center rounded-xl bg-white p-4 shadow-md">
        <Image
          src={imageUrl}
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
