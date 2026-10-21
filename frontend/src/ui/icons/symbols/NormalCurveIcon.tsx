import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const NormalCurveIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <path d="M2 20h20" />
        <path d="M4 20c3 0 5-2 6-8 1-6 2-8 2-8s1 2 2 8c1 6 3 8 6 8" />
      </g>
    )}
  />
);
