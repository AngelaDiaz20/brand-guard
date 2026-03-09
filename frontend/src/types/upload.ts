export type UploadFileType = "image" | "pdf";

export const UPLOAD_ACCEPT = ".jpg,.jpeg,.png,.pdf,image/*,application/pdf";

export function getUploadFileType(file: File): UploadFileType | null {
  if (file.type === "application/pdf") {
    return "pdf";
  }

  if (file.type.startsWith("image/")) {
    return "image";
  }

  return null;
}
