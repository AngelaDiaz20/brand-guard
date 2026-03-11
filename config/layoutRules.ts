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

