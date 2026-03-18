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
      x: 989,
      y: 90,
      width: 71,
      height: 54
    },
    logoContainer: {
      x: 946,
      y: 291,
      width: 102,
      height: 101
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
      x: 946,
      y: 291,
      width: 71,
      height: 54
    },
    logoContainer: {
      x: 989,
      y: 90,
      width: 102,
      height: 101
    }
  }
} as const;

export type PieceType = keyof typeof layoutRules;
