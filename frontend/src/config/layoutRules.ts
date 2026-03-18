export const layoutRules = {
  "1:1": {
    logo: {
      expected: {
        x: 989,
        y: 90,
        width: 71,
        height: 54
      },
      tolerance: {
        position: 40,
        sizePercent: 0.1
      }
    },
    container: {
      expected: {
        x: 946,
        y: 291,
        width: 102,
        height: 101
      }
    }
  },

  "9:16": {
    logo: {
      expected: {
        x: 946,
        y: 291,
        width: 71,
        height: 54
      },
      tolerance: {
        position: 40,
        sizePercent: 0.1
      }
    }
  }
} as const;

export type StaticLayoutPieceType = keyof typeof layoutRules;
