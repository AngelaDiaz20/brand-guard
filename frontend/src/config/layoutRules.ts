export const layoutRules = {
  "1:1": {
    canvas: {
      width: 1080,
      height: 1080
    },
    safeArea: {
      width: 1000,
      height: 1000,
      centerX: 540,
      centerY: 540
    },
    logo: {
      width: 71.1652,
      height: 53.7317
    },
    logoContainer: {
      width: 102.2869,
      height: 100.6546
    }
  },
  ST: {
    canvas: {
      width: 1080,
      height: 1920
    },
    safeArea: {
      width: 960,
      height: 1360,
      centerX: 540,
      centerY: 831
    },
    logo: {
      width: 71.1652,
      height: 53.7317
    },
    logoContainer: {
      width: 102.2869,
      height: 100.6546
    }
  }
} as const;

export type PieceType = keyof typeof layoutRules;

export type BoundingBox = { x: number; y: number; width: number; height: number };

export function detectPieceType(width: number, height: number): PieceType | null {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return null;
  }

  const ratio = width / height;
  if (Math.abs(ratio - 1) <= 0.03) {
    return "1:1";
  }
  if (Math.abs(ratio - 1080 / 1920) <= 0.03) {
    return "ST";
  }
  return null;
}

export function computeSafeAreaBoundingBox(
  pieceType: PieceType,
  imageWidth: number,
  imageHeight: number
): BoundingBox {
  const rule = layoutRules[pieceType];
  const scaleX = imageWidth / rule.canvas.width;
  const scaleY = imageHeight / rule.canvas.height;
  const safe = rule.safeArea;

  const safeWidth = safe.width * scaleX;
  const safeHeight = safe.height * scaleY;
  const centerX = safe.centerX * scaleX;
  const centerY = safe.centerY * scaleY;

  return {
    x: centerX - safeWidth / 2,
    y: centerY - safeHeight / 2,
    width: safeWidth,
    height: safeHeight
  };
}

